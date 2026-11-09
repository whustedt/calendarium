"""Read-only, versioned JSON API for Grafana's Infinity backend data source."""

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from hmac import compare_digest
import calendar
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import BadRequest, UnprocessableEntity

from . import db
from .helpers import calculate_milestone_info
from .models import Category, Entry


grafana_api = Blueprint('grafana_api', __name__, url_prefix='/api/grafana/v1')
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
MAX_RANGE = timedelta(days=3660)
MAX_ROWS = 10000
MAX_OCCURRENCES = 50000
RANGE_PARAMETERS = {'from', 'to', 'timezone', 'category', 'categories', 'include_cancelled'}


@grafana_api.before_request
def authenticate():
    """An optional token protects every route, including the health check."""
    token = current_app.config.get('GRAFANA_API_TOKEN')
    if not token:
        return None
    authorization = request.authorization
    if (authorization is None or authorization.type != 'bearer'
            or not authorization.token
            or not compare_digest(authorization.token.encode('utf-8'), token.encode('utf-8'))):
        return jsonify(error='A valid bearer token is required'), 401, {'WWW-Authenticate': 'Bearer'}


@grafana_api.after_request
def prevent_caching(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


@grafana_api.errorhandler(BadRequest)
@grafana_api.errorhandler(UnprocessableEntity)
def invalid_query(error):
    return jsonify(error=error.description), error.code


@grafana_api.errorhandler(SQLAlchemyError)
def database_unavailable(error):
    db.session.rollback()
    current_app.logger.exception('Grafana database query failed')
    return jsonify(error='Database unavailable'), 503


def _validate_parameters(allowed):
    unknown = set(request.args) - allowed
    if unknown:
        raise BadRequest(f"Unknown query parameter(s): {', '.join(sorted(unknown))}")
    for name in set(request.args) - {'category'}:
        if len(request.args.getlist(name)) != 1:
            raise BadRequest(f'{name} must be supplied only once')


def _timestamp(value, name):
    if not value:
        raise BadRequest(f'{name} is required (Unix milliseconds or ISO 8601 with timezone)')
    try:
        if re.fullmatch(r'-?\d+', value):
            return EPOCH + timedelta(milliseconds=int(value))
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError('Timezone is required')
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise BadRequest(f'Invalid {name}: use Unix milliseconds or ISO 8601 with timezone') from None


def _milliseconds(value):
    # Integer arithmetic avoids platform-local timezone and floating point rounding.
    return (value.astimezone(timezone.utc) - EPOCH) // timedelta(milliseconds=1)


def _category_names():
    if 'category' in request.args and 'categories' in request.args:
        raise BadRequest('Use category or categories, not both')
    if 'categories' in request.args:
        try:
            names = json.loads(request.args['categories'])
        except ValueError:
            raise BadRequest('categories must be a JSON array of category names') from None
        if not isinstance(names, list):
            raise BadRequest('categories must be a JSON array of category names')
    elif 'category' in request.args:
        names = request.args.getlist('category')
    else:
        return None
    if len(names) > 100 or any(not isinstance(name, str) or not name for name in names):
        raise BadRequest('Supply at most 100 non-empty category names')
    return names


@dataclass(frozen=True)
class QueryRange:
    start: datetime
    end: datetime
    zone: ZoneInfo
    first_date: date
    last_date: date
    categories: list | None
    include_cancelled: bool

    @classmethod
    def from_request(cls, extra_parameters=()):
        _validate_parameters(RANGE_PARAMETERS | set(extra_parameters))
        start = _timestamp(request.args.get('from'), 'from')
        end = _timestamp(request.args.get('to'), 'to')
        if start > end:
            raise BadRequest('from must not be after to')
        if end - start > MAX_RANGE:
            raise BadRequest('The time range must not exceed 3660 days')
        zone_name = request.args.get('timezone', current_app.config['GRAFANA_TIMEZONE'])
        try:
            zone = ZoneInfo(zone_name)
            first_date = start.astimezone(zone).date()
            last_date = end.astimezone(zone).date()
        except (ZoneInfoNotFoundError, ValueError, OverflowError):
            raise BadRequest('Use a valid IANA timezone and representable local dates') from None
        cancelled = request.args.get('include_cancelled', 'false')
        if cancelled not in {'true', 'false'}:
            raise BadRequest('include_cancelled must be true or false')
        return cls(start, end, zone, first_date, last_date, _category_names(), cancelled == 'true')

    def midnight(self, day):
        return datetime.combine(day, time.min, self.zone)


def _categories(names=None):
    query = db.select(Category).order_by(Category.name, Category.id)
    if names is not None:
        query = query.where(Category.name.in_(names))
    return db.session.execute(query).scalars().all()


def _occurrences(window):
    """Expand anniversaries in the requested years, not relative to today's date."""
    query = (db.select(Entry).join(Category).options(joinedload(Entry.category))
             .where(or_(Category.repeat_annually.is_(True),
                        Entry.date.between(window.first_date.isoformat(), window.last_date.isoformat())))
             .order_by(Entry.id))
    if window.categories is not None:
        query = query.where(Category.name.in_(window.categories))
    if not window.include_cancelled:
        query = query.where(Entry.cancelled.is_(False))
    count = 0
    for entry in db.session.execute(query).scalars().yield_per(500):
        try:
            original = date.fromisoformat(entry.date)
        except ValueError:
            current_app.logger.warning('Skipping invalid date for Grafana entry %s', entry.id)
            continue
        if entry.category.repeat_annually:
            days = (date(year, original.month,
                         min(original.day, calendar.monthrange(year, original.month)[1]))
                    for year in range(max(original.year, window.first_date.year), window.last_date.year + 1))
        else:
            days = (original,)
        for day in days:
            instant = window.midnight(day)
            if window.start <= instant <= window.end:
                count += 1
                if count > MAX_OCCURRENCES:
                    raise UnprocessableEntity('Too many event occurrences; narrow the time range or categories')
                yield entry, day, _milliseconds(instant)


def _limited_rows(rows):
    result = []
    for row in rows:
        if len(result) >= MAX_ROWS:
            raise UnprocessableEntity('More than 10000 rows; narrow the time range or categories')
        result.append(row)
    return result


@grafana_api.get('/health')
def health():
    _validate_parameters(set())
    db.session.execute(text('SELECT 1'))
    return jsonify(status='ok', api_version=1)


@grafana_api.get('/categories')
def categories():
    _validate_parameters(set())
    return jsonify([{
        'id': category.id,
        'name': category.name,
        'symbol': category.symbol,
        'color': category.color_hex,
        'repeat_annually': category.repeat_annually,
    } for category in _categories()])


def _event_rows(window):
    for entry, day, timestamp in _occurrences(window):
        yield {
            'id': entry.id,
            'time': timestamp,
            'date': day.isoformat(),
            'original_date': entry.date,
            'title': entry.title,
            'description': entry.description or '',
            'category': entry.category.name,
            'category_id': entry.category.id,
            'symbol': entry.category.symbol,
            'color': entry.category.color_hex,
            'url': entry.url,
            'recurring': entry.category.repeat_annually,
            'cancelled': entry.cancelled,
            **calculate_milestone_info(date.fromisoformat(entry.date), day, entry.category.repeat_annually),
        }


@grafana_api.get('/events')
def events():
    rows = _limited_rows(_event_rows(QueryRange.from_request()))
    rows.sort(key=lambda row: (row['time'], row['category'], row['id']))
    return jsonify(rows)


@grafana_api.get('/annotations')
def annotations():
    window = QueryRange.from_request()
    rows = _limited_rows({
        'time': timestamp,
        'title': entry.title,
        'text': entry.title + ('\n\n' + entry.description if entry.description else ''),
        'tags': entry.category.name,
    } for entry, day, timestamp in _occurrences(window))
    rows.sort(key=lambda row: (row['time'], row['title']))
    return jsonify(rows)


def _bucket(day, interval):
    if interval == 'week':
        return day - timedelta(days=day.weekday())
    if interval == 'month':
        return day.replace(day=1)
    return day


def _buckets(window, interval):
    day = _bucket(window.first_date, interval)
    last = _bucket(window.last_date, interval)
    while True:
        yield day
        if day == last:
            break
        if interval == 'month':
            day = date(day.year + (day.month == 12), day.month % 12 + 1, 1)
        else:
            day += timedelta(days=7 if interval == 'week' else 1)


@grafana_api.get('/timeseries')
def timeseries():
    window = QueryRange.from_request({'interval'})
    interval = request.args.get('interval', 'day')
    if interval not in {'day', 'week', 'month'}:
        raise BadRequest('interval must be day, week or month')
    selected_categories = _categories(window.categories)
    buckets = list(_buckets(window, interval))
    if len(buckets) * len(selected_categories) > MAX_ROWS:
        raise UnprocessableEntity('More than 10000 rows; use a coarser interval or fewer categories')
    counts = Counter((_bucket(day, interval), entry.category_id)
                     for entry, day, timestamp in _occurrences(window))
    return jsonify([{
        'time': _milliseconds(max(window.start, window.midnight(day))),
        'category': category.name,
        'count': counts[(day, category.id)],
    } for day in buckets for category in selected_categories])
