from datetime import datetime

from flask import current_app, jsonify, request

from app import db
from .models import Category, Entry


DATE_FMT = "%Y-%m-%d"


def _parse_iso_date(iso_date):
    """Parse an ISO timestamp into a YYYY-MM-DD date string."""
    if not iso_date:
        return None

    try:
        return datetime.fromisoformat(iso_date.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def _to_timestamp_ms(date_str):
    return int(datetime.strptime(date_str, DATE_FMT).timestamp() * 1000)


def init_grafana_routes(app):
    """Initialize Grafana routes for the Flask application."""

    @app.route('/grafana/')
    def grafana_test_connection():
        """Health endpoint for Grafana connectivity checks."""
        return "Connection established", 200

    @app.route('/grafana/infinity/categories', methods=['GET'])
    def grafana_infinity_categories():
        """Return category rows for Grafana Infinity variable queries."""
        try:
            categories = db.session.query(Category.name).order_by(Category.name.asc()).all()
            return jsonify([{"category": category.name} for category in categories])
        except Exception as exc:
            current_app.logger.error(f"Infinity categories failed: {exc}")
            return jsonify({"error": "Failed to fetch categories"}), 500

    @app.route('/grafana/infinity/timeseries', methods=['GET'])
    def grafana_infinity_timeseries():
        """
        Return time-series rows for Grafana Infinity.

        Query params:
        - category: optional category name filter
        - from: optional ISO datetime lower bound
        - to: optional ISO datetime upper bound
        """
        try:
            category_name = request.args.get('category')
            start_date = _parse_iso_date(request.args.get('from'))
            end_date = _parse_iso_date(request.args.get('to'))

            query = db.session.query(
                Category.name.label('category'),
                Entry.date.label('date'),
                db.func.count(Entry.id).label('count'),
            ).join(Category, Category.id == Entry.category_id)

            if category_name:
                query = query.filter(Category.name == category_name)
            if start_date:
                query = query.filter(Entry.date >= start_date)
            if end_date:
                query = query.filter(Entry.date <= end_date)

            rows = query.group_by(Category.name, Entry.date).order_by(Entry.date.asc()).all()

            return jsonify([
                {
                    "category": row.category,
                    "date": row.date,
                    "timestamp": _to_timestamp_ms(row.date),
                    "count": row.count,
                }
                for row in rows
            ])
        except Exception as exc:
            current_app.logger.error(f"Infinity timeseries failed: {exc}")
            return jsonify({"error": "Failed to fetch timeseries"}), 500

    @app.route('/grafana/infinity/annotations', methods=['GET'])
    def grafana_infinity_annotations():
        """
        Return annotation rows for Grafana Infinity.

        Query params:
        - categories: optional comma-separated list of category names
        - from: optional ISO datetime lower bound
        - to: optional ISO datetime upper bound
        """
        try:
            raw_categories = request.args.get('categories', '')
            categories = [name.strip() for name in raw_categories.split(',') if name.strip()]
            start_date = _parse_iso_date(request.args.get('from'))
            end_date = _parse_iso_date(request.args.get('to'))

            query = db.session.query(Entry).join(Category, Category.id == Entry.category_id)
            if categories:
                query = query.filter(Category.name.in_(categories))
            if start_date:
                query = query.filter(Entry.date >= start_date)
            if end_date:
                query = query.filter(Entry.date <= end_date)

            entries = query.order_by(Entry.date.asc()).all()

            return jsonify([
                {
                    "time": _to_timestamp_ms(entry.date),
                    "date": entry.date,
                    "title": entry.title,
                    "text": entry.description or "",
                    "category": entry.category.name,
                }
                for entry in entries
            ])
        except Exception as exc:
            current_app.logger.error(f"Infinity annotations failed: {exc}")
            return jsonify({"error": "Failed to fetch annotations"}), 500

    app.add_url_rule('/grafana/', view_func=grafana_test_connection)
    app.add_url_rule('/grafana/infinity/categories', view_func=grafana_infinity_categories, methods=['GET'])
    app.add_url_rule('/grafana/infinity/timeseries', view_func=grafana_infinity_timeseries, methods=['GET'])
    app.add_url_rule('/grafana/infinity/annotations', view_func=grafana_infinity_annotations, methods=['GET'])
