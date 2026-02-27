from flask import request, jsonify, current_app
from flask_restx import Resource
from datetime import datetime
from .models import Category, Entry
from app import db
from .api_models import (
    grafana_ns, grafana_query_request_model, grafana_datapoint_model,
    grafana_annotation_request_model, grafana_annotation_model,
    grafana_tag_key_model, grafana_tag_value_request_model, 
    grafana_tag_value_model, error_model
)

@grafana_ns.route('/test')
class GrafanaTestConnectionAPI(Resource):
    @grafana_ns.doc('test_grafana_connection')
    def get(self):
        """Test connection with Grafana"""
        return "Connection established", 200

@grafana_ns.route('/search')
class GrafanaSearchAPI(Resource):
    @grafana_ns.doc('grafana_search')
    def post(self):
        """Search available targets based on dynamic categories"""
        try:
            categories = db.session.query(Category.name).all()
            targets = [category.name for category in categories]
            return targets
        except Exception as e:
            current_app.logger.error(f"Search failed: {e}")
            return {'error': 'Search failed'}, 500

@grafana_ns.route('/query')
class GrafanaQueryAPI(Resource):
    @grafana_ns.doc('grafana_query')
    @grafana_ns.expect(grafana_query_request_model)
    @grafana_ns.marshal_list_with(grafana_datapoint_model)
    @grafana_ns.response(500, 'Query failed', error_model)
    def post(self):
        """Query data dynamically based on category names"""
        req = request.get_json()
        try:
            response = []
            for target in req['targets']:
                category = db.session.query(Category).filter_by(name=target['target']).first()
                if category and target['type'] == 'timeserie':
                    data_points = db.session.query(
                        Entry.date, 
                        db.func.count(Entry.id).label('count')
                    ).filter(Entry.category_id == category.id).group_by(Entry.date).all()

                    datapoints = [
                        [count, datetime.strptime(date, '%Y-%m-%d').timestamp() * 1000]
                        for date, count in data_points
                    ]

                    response.append({
                        "target": target['target'],
                        "datapoints": datapoints
                    })

            return response
        except Exception as e:
            current_app.logger.error(f"Query failed: {e}")
            return {'error': 'Query failed'}, 500

@grafana_ns.route('/annotations')
class GrafanaAnnotationsAPI(Resource):
    @grafana_ns.doc('grafana_annotations')
    @grafana_ns.expect(grafana_annotation_request_model)
    @grafana_ns.marshal_list_with(grafana_annotation_model)
    @grafana_ns.response(500, 'Annotations failed', error_model)
    def post(self):
        """Fetch annotations based on multiple category names"""
        req = request.get_json()
        try:
            annotations = []
            query_categories = req['annotation']['query'].split(',')
            query_categories = [name.strip() for name in query_categories]

            categories = db.session.query(Category).filter(Category.name.in_(query_categories)).all()
            category_ids = [cat.id for cat in categories]

            if category_ids:
                entries = db.session.query(Entry).filter(Entry.category_id.in_(category_ids)).all()
                for entry in entries:
                    annotations.append({
                        "annotation": req['annotation'],
                        "time": datetime.strptime(entry.date, '%Y-%m-%d').timestamp() * 1000,
                        "title": entry.title,
                        "tags": [entry.category.name],
                        "text": entry.description or ""
                    })

            return annotations
        except Exception as e:
            current_app.logger.error(f"Annotations failed: {e}")
            return {'error': 'Annotations failed'}, 500

@grafana_ns.route('/tag-keys')
class GrafanaTagKeysAPI(Resource):
    @grafana_ns.doc('grafana_tag_keys')
    @grafana_ns.marshal_list_with(grafana_tag_key_model)
    def post(self):
        """Fetch tag keys for ad hoc filtering"""
        return [
            {"type": "string", "text": "category"},
            {"type": "string", "text": "date"}
        ]

@grafana_ns.route('/tag-values')
class GrafanaTagValuesAPI(Resource):
    @grafana_ns.doc('grafana_tag_values')
    @grafana_ns.expect(grafana_tag_value_request_model)
    @grafana_ns.marshal_list_with(grafana_tag_value_model)
    @grafana_ns.response(500, 'Failed to fetch tag values', error_model)
    def post(self):
        """Fetch tag values based on key dynamically"""
        req = request.get_json()
        key = req['key']
        try:
            if key == "category":
                categories = db.session.query(Category.name).distinct().all()
                values = [{"text": category.name} for category in categories]
            elif key == "date":
                dates = db.session.query(Entry.date).distinct().all()
                values = [{"text": date[0]} for date in dates]
            else:
                values = []
            return values
        except Exception as e:
            current_app.logger.error(f"Failed to fetch tag values: {e}")
            return {'error': 'Failed to fetch tag values'}, 500
