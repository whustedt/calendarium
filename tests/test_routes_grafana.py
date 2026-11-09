"""Contract and calendar semantics for the Infinity REST API."""

from datetime import datetime, timezone
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models import Category, Entry


BASE = '/api/grafana/v1'
RANGE = {'from': '2025-01-01T00:00:00Z', 'to': '2025-01-03T23:59:59.999Z'}


def milliseconds(value):
    return int(datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp() * 1000)


@pytest.fixture(autouse=True)
def grafana_config(test_client):
    test_client.application.config.update(GRAFANA_API_TOKEN=None, GRAFANA_TIMEZONE='UTC')


@pytest.fixture
def entries(test_client, init_database):
    db.session.query(Entry).delete()
    birthday = db.session.query(Category).filter_by(name='Birthday').one()
    release = db.session.query(Category).filter_by(name='Release').one()
    special = Category(name='Conference, Zürich & "Friends"', symbol='🎉', color_hex='#123456')
    db.session.add(special)
    db.session.flush()
    examples = [
        Entry(date='2024-12-31', category=release, title='Before'),
        Entry(date='2025-01-01', category=release, title='Launch', description='Version 1', url='https://example.com'),
        Entry(date='2025-01-01', category=release, title='Another launch'),
        Entry(date='2025-01-02', category=release, title='Cancelled', cancelled=True),
        Entry(date='2025-01-03', category=release, title='Last day'),
        Entry(date='2025-01-04', category=release, title='After'),
        Entry(date='2000-01-02', category=birthday, title='Anniversary'),
        Entry(date='0001-01-03', category=birthday, title='Unknown birth year'),
        Entry(date='2020-02-29', category=birthday, title='Leap birthday'),
        Entry(date='2026-01-02', category=birthday, title='Not born yet'),
        Entry(date='2025-01-02', category=special, title='Conference'),
    ]
    db.session.add_all(examples)
    db.session.commit()
    return examples


def test_health_checks_database(test_client):
    response = test_client.get(BASE + '/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok', 'api_version': 1}
    assert response.headers['Cache-Control'] == 'no-store'


def test_categories_are_sorted_and_suitable_for_variables(test_client, entries):
    response = test_client.get(BASE + '/categories')
    assert response.status_code == 200
    names = [row['name'] for row in response.json]
    assert names == sorted(names)
    birthday = next(row for row in response.json if row['name'] == 'Birthday')
    assert birthday['repeat_annually'] is True
    assert birthday['symbol'] == '🥳'
    assert birthday['id'] > 0
    assert birthday['color'] == '#AED581'


def test_events_filter_the_range_and_preserve_event_details(test_client, entries):
    response = test_client.get(BASE + '/events', query_string=RANGE)
    assert response.status_code == 200
    rows = response.json
    assert len(rows) == 6
    assert [row['time'] for row in rows] == sorted(row['time'] for row in rows)
    assert {row['title'] for row in rows} == {
        'Launch', 'Another launch', 'Last day', 'Anniversary', 'Unknown birth year', 'Conference',
    }
    launch = next(row for row in rows if row['title'] == 'Launch')
    assert launch['time'] == milliseconds('2025-01-01T00:00:00Z')
    assert launch['date'] == launch['original_date'] == '2025-01-01'
    assert launch['category'] == 'Release'
    assert launch['description'] == 'Version 1'
    assert launch['url'] == 'https://example.com'
    assert launch['cancelled'] is False
    assert launch['recurring'] is False
    assert launch['years_since'] is None
    unknown = next(row for row in rows if row['title'] == 'Unknown birth year')
    assert unknown['original_date'] == '0001-01-03'
    assert unknown['date'] == '2025-01-03'
    assert unknown['years_since'] is None
    anniversary = next(row for row in rows if row['title'] == 'Anniversary')
    assert anniversary['years_since'] == 25
    assert anniversary['is_milestone'] is True


@pytest.mark.parametrize('endpoint', ['events', 'timeseries', 'annotations'])
def test_cancelled_entries_are_opt_in_consistently(test_client, entries, endpoint):
    def get(include):
        return test_client.get(BASE + '/' + endpoint, query_string={
            **RANGE, 'category': 'Release', 'include_cancelled': include,
        }).json
    without, with_cancelled = get('false'), get('true')
    if endpoint == 'timeseries':
        assert sum(row['count'] for row in without) == 3
        assert sum(row['count'] for row in with_cancelled) == 4
    else:
        assert len(without) == 3
        assert len(with_cancelled) == 4


def test_exact_inclusive_range_accepts_epoch_milliseconds(test_client, entries):
    boundary = milliseconds('2025-01-01T00:00:00Z')
    response = test_client.get(BASE + '/events', query_string={'from': boundary, 'to': boundary})
    assert response.status_code == 200
    assert {row['title'] for row in response.json} == {'Launch', 'Another launch'}
    response = test_client.get(BASE + '/events', query_string={**RANGE, 'from': boundary + 1})
    assert 'Launch' not in {row['title'] for row in response.json}


@pytest.mark.parametrize('endpoint', ['events', 'timeseries', 'annotations'])
def test_category_filters_support_json_and_repeated_names(test_client, entries, endpoint):
    special = 'Conference, Zürich & "Friends"'
    query = {**RANGE, 'categories': json.dumps(['Release', special])}
    response = test_client.get(BASE + '/' + endpoint, query_string=query)
    assert response.status_code == 200
    repeated = test_client.get(BASE + '/' + endpoint, query_string={
        **RANGE, 'category': ['Release', special],
    })
    assert repeated.json == response.json
    assert len(response.json) > 0
    if endpoint != 'annotations':
        assert {row['category'] for row in response.json} == {'Release', special}
    for names in [[], ['Unknown'], ["' OR 1=1 --"]]:
        response = test_client.get(BASE + '/' + endpoint, query_string={**RANGE, 'categories': json.dumps(names)})
        assert response.status_code == 200
        assert response.json == []


def test_recurring_entries_expand_every_year_in_range_without_future_birthdays(test_client, entries):
    response = test_client.get(BASE + '/events', query_string={
        'from': '2024-01-01T00:00:00Z', 'to': '2026-12-31T23:59:59Z', 'category': 'Birthday',
    })
    assert response.status_code == 200
    rows = response.json
    assert [row['date'] for row in rows if row['title'] == 'Anniversary'] == [
        '2024-01-02', '2025-01-02', '2026-01-02',
    ]
    assert [row['date'] for row in rows if row['title'] == 'Not born yet'] == ['2026-01-02']
    assert [row['date'] for row in rows if row['title'] == 'Leap birthday'] == [
        '2024-02-29', '2025-02-28', '2026-02-28',
    ]


def test_explicit_timezone_and_iso_offsets_define_midnight(test_client, entries):
    response = test_client.get(BASE + '/events', query_string={
        'from': '2025-01-01T00:00:00+01:00', 'to': '2025-01-01T00:00:00+01:00',
        'timezone': 'Europe/Berlin',
    })
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['time'] == milliseconds('2024-12-31T23:00:00Z')
    test_client.application.config['GRAFANA_TIMEZONE'] = 'Europe/Berlin'
    same = test_client.get(BASE + '/events', query_string={
        'from': '2024-12-31T23:00:00Z', 'to': '2024-12-31T23:00:00Z',
    })
    assert same.json == response.json


def test_calendar_buckets_respect_daylight_saving_time(test_client):
    response = test_client.get(BASE + '/timeseries', query_string={
        'from': '2025-03-29T00:00:00+01:00', 'to': '2025-03-31T00:00:00+02:00',
        'timezone': 'Europe/Berlin', 'category': 'Birthday',
    })
    assert response.status_code == 200
    rows = response.json
    assert [row['count'] for row in rows] == [0, 0, 0]
    assert rows[1]['time'] - rows[0]['time'] == 24 * 3600000
    assert rows[2]['time'] - rows[1]['time'] == 23 * 3600000


@pytest.mark.parametrize('interval, expected', [('day', [2, 0, 1]), ('week', [3]), ('month', [3])])
def test_counts_are_aggregated_zero_filled_and_sorted(test_client, entries, interval, expected):
    response = test_client.get(BASE + '/timeseries', query_string={
        **RANGE, 'interval': interval, 'category': 'Release',
    })
    assert response.status_code == 200
    assert [row['count'] for row in response.json] == expected
    assert response.json[0]['time'] == milliseconds(RANGE['from'])


def test_month_buckets_cross_year_boundary_and_clip_first_bucket(test_client, entries):
    response = test_client.get(BASE + '/timeseries', query_string={
        'from': '2024-12-30T12:34:00Z', 'to': '2025-02-02T00:00:00Z',
        'interval': 'month', 'category': 'Release',
    })
    assert response.status_code == 200
    assert [row['count'] for row in response.json] == [1, 4, 0]
    assert [row['time'] for row in response.json] == [
        milliseconds('2024-12-30T12:34:00Z'), milliseconds('2025-01-01T00:00:00Z'),
        milliseconds('2025-02-01T00:00:00Z'),
    ]


def test_annotations_have_infinity_dataframe_fields(test_client, entries):
    response = test_client.get(BASE + '/annotations', query_string={**RANGE, 'category': 'Release'})
    assert response.status_code == 200
    launch = next(row for row in response.json if row['title'] == 'Launch')
    assert launch == {
        'time': milliseconds('2025-01-01T00:00:00Z'), 'title': 'Launch',
        'text': 'Launch\n\nVersion 1', 'tags': 'Release',
    }
    assert next(row for row in response.json if row['title'] == 'Another launch')['text'] == 'Another launch'


@pytest.mark.parametrize('endpoint', ['events', 'timeseries', 'annotations'])
@pytest.mark.parametrize('overrides', [
    {'from': ''}, {'to': ''}, {'from': 'not-a-date'}, {'from': '2025-01-01'},
    {'to': '2025-01-04T00:00:00'}, {'from': '2025-01-04T00:00:00Z'},
    {'from': '2000-01-01T00:00:00Z'}, {'to': '999999999999999999999999'},
    {'timezone': 'Unknown/Zone'}, {'timezone': '../etc/passwd'}, {'timezone': ''},
    {'include_cancelled': '1'}, {'categories': 'Release'}, {'categories': 'null'},
    {'categories': '[1]'}, {'categories': '[""]'}, {'categories': json.dumps(['Release'] * 101)},
    {'category': 'Release', 'categories': '["Release"]'}, {'typo': 'ignored?'},
])
def test_bad_queries_fail_with_json_instead_of_unbounded_results(test_client, endpoint, overrides):
    response = test_client.get(BASE + '/' + endpoint, query_string={**RANGE, **overrides})
    assert response.status_code == 400
    assert isinstance(response.json['error'], str)


@pytest.mark.parametrize('endpoint', ['events', 'timeseries', 'annotations'])
def test_ranges_are_required_and_singular(test_client, endpoint):
    for query in [{}, {'from': RANGE['from']}, {'to': RANGE['to']}, {**RANGE, 'to': [RANGE['to']] * 2}]:
        response = test_client.get(BASE + '/' + endpoint, query_string=query)
        assert response.status_code == 400
        assert 'error' in response.json


def test_invalid_interval_is_rejected(test_client):
    response = test_client.get(BASE + '/timeseries', query_string={**RANGE, 'interval': 'hour'})
    assert response.status_code == 400


@pytest.mark.parametrize('endpoint', ['health', 'categories', 'events', 'timeseries', 'annotations'])
def test_optional_bearer_auth_covers_every_endpoint(test_client, endpoint):
    test_client.application.config['GRAFANA_API_TOKEN'] = 'test-token'
    query = RANGE if endpoint in {'events', 'timeseries', 'annotations'} else {}
    for auth in [None, 'Bearer wrong', 'Basic dXNlcjpwYXNz', 'Bearer']:
        headers = {'Authorization': auth} if auth else {}
        response = test_client.get(BASE + '/' + endpoint, query_string=query, headers=headers)
        assert response.status_code == 401
        assert response.headers['WWW-Authenticate'] == 'Bearer'
        assert response.headers['Cache-Control'] == 'no-store'
    response = test_client.get(BASE + '/' + endpoint, query_string=query, headers={'Authorization': 'Bearer test-token'})
    assert response.status_code == 200


def test_database_failures_return_sanitized_service_unavailable(test_client):
    with patch.object(db.session, 'execute', side_effect=SQLAlchemyError('private database details')):
        for endpoint, query in [('health', {}), ('categories', {}), ('events', RANGE),
                                ('annotations', RANGE), ('timeseries', RANGE)]:
            response = test_client.get(BASE + '/' + endpoint, query_string=query)
            assert response.status_code == 503
            assert response.json == {'error': 'Database unavailable'}


@pytest.mark.parametrize('endpoint', ['events', 'annotations', 'timeseries'])
def test_row_limits_fail_explicitly_without_partial_data(test_client, entries, endpoint, monkeypatch):
    monkeypatch.setattr('app.routes_grafana.MAX_ROWS', 2)
    response = test_client.get(BASE + '/' + endpoint, query_string=RANGE)
    assert response.status_code == 422
    assert 'error' in response.json


def test_occurrence_budget_also_bounds_aggregation(test_client, entries, monkeypatch):
    monkeypatch.setattr('app.routes_grafana.MAX_OCCURRENCES', 1)
    response = test_client.get(BASE + '/timeseries', query_string=RANGE)
    assert response.status_code == 422


@pytest.mark.parametrize('path, method', [
    ('/grafana/', 'get'), ('/grafana/search', 'post'), ('/grafana/query', 'post'),
    ('/grafana/annotations', 'post'), ('/grafana/tag-keys', 'post'), ('/grafana/tag-values', 'post'),
])
def test_simple_json_routes_are_removed(test_client, path, method):
    assert getattr(test_client, method)(path).status_code == 404


def test_api_is_read_only(test_client):
    assert test_client.post(BASE + '/events', json={}).status_code == 405


def test_invalid_stored_dates_do_not_break_valid_entries(test_client, entries):
    birthday = db.session.query(Category).filter_by(name='Birthday').one()
    db.session.add(Entry(date='invalid', category=birthday, title='Broken legacy entry'))
    db.session.commit()
    response = test_client.get(BASE + '/events', query_string=RANGE)
    assert response.status_code == 200
    assert len(response.json) == 6


def test_saved_dashboard_queries_match_the_api(test_client, entries):
    dashboard = json.loads((Path(__file__).parents[1] / 'grafana/dashboards/calendarium.json').read_text())
    variable = dashboard['templating']['list'][0]['query']['infinityQuery']
    annotation = dashboard['annotations']['list'][0]['target']
    queries = [variable, annotation] + [target for panel in dashboard['panels'] for target in panel['targets']]
    substitutions = {
        '${__timeFrom}': str(milliseconds(RANGE['from'])),
        '${__timeTo}': str(milliseconds(RANGE['to'])),
        '${categories:json}': json.dumps(['Birthday', 'Release']),
        '$__customInterval(90d,day,730d,week,month)': 'day',
    }
    for query in queries:
        assert query['parser'] == 'backend'
        assert query['source'] == 'url'
        assert query['root_selector'] == '$'
        parameters = {item['key']: substitutions.get(item['value'], item['value'])
                      for item in query['url_options']['params']}
        response = test_client.get(BASE + query['url'], query_string=parameters)
        assert response.status_code == 200
        assert len(response.json) > 0
        for column in query['columns']:
            assert column['selector'] in response.json[0]
        for row in response.json:
            for column in query['columns']:
                value = row[column['selector']]
                if value is None:
                    continue
                if column['type'] == 'string':
                    assert isinstance(value, str)
                else:
                    assert isinstance(value, (int, float))
