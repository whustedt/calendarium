from flask import request, jsonify, current_app
from datetime import datetime
from .models import Entry, Category
from app import db

def init_grafana_routes(app):
    """
    Initialize Grafana routes for the Flask application.

    :param app: Flask application instance
    """

    @app.route('/grafana/')
    def grafana_test_connection():
        """
        Endpoint to test connection with Grafana.

        :return: A message confirming connection establishment
        """
        return "Connection established", 200

    @app.route('/grafana/search', methods=['POST'])
    def grafana_search():
        """
        Endpoint for Grafana to search available targets based on dynamic categories.
        """
        try:
            categories = db.session.query(Category.name).all()
            targets = [category.name for category in categories]
            return jsonify(targets)
        except Exception as e:
            current_app.logger.error(f"Search failed: {e}")
            return jsonify({"error": "Search failed"}), 500

    @app.route('/grafana/query', methods=['POST'])
    def grafana_query():
        """
        Endpoint for Grafana to query data dynamically based on category names.
        """
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
    
            return jsonify(response)
        except Exception as e:
            current_app.logger.error(f"Query failed: {e}")
            return jsonify({"error": "Query failed"}), 500

    @app.route('/grafana/annotations', methods=['POST'])
    def grafana_annotations():
        """
        Endpoint for Grafana to fetch annotations based on multiple category names.
        """
        req = request.get_json()
        try:
            annotations = []
            query_categories = req['annotation']['query'].split(',')  # Split the query by commas
            query_categories = [name.strip() for name in query_categories]  # Clean whitespace
    
            categories = db.session.query(Category).filter(Category.name.in_(query_categories)).all()
            category_ids = [cat.id for cat in categories]  # List of category IDs from the query
    
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
            return jsonify(annotations)
        except Exception as e:
            current_app.logger.error(f"Annotations failed: {e}")
            return jsonify({"error": "Annotations failed"}), 500

    @app.route('/grafana/tag-keys', methods=['POST'])
    def grafana_tag_keys():
        """
        Endpoint for Grafana to fetch tag keys.

        :return: JSON list of tag keys
        """
        return jsonify([
            {"type": "string", "text": "category"},
            {"type": "string", "text": "date"}
        ])

    @app.route('/grafana/tag-values', methods=['POST'])
    def grafana_tag_values():
        """
        Endpoint for Grafana to fetch tag values based on key dynamically.
        """
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
            return jsonify(values)
        except Exception as e:
            current_app.logger.error(f"Failed to fetch tag values: {e}")
            return jsonify({"error": "Failed to fetch tag values"}), 500

    app.add_url_rule('/grafana/', view_func=grafana_test_connection)
    app.add_url_rule('/grafana/search', view_func=grafana_search, methods=['POST'])
    app.add_url_rule('/grafana/query', view_func=grafana_query, methods=['POST'])
    app.add_url_rule('/grafana/annotations', view_func=grafana_annotations, methods=['POST'])
    app.add_url_rule('/grafana/tag-keys', view_func=grafana_tag_keys, methods=['POST'])
    app.add_url_rule('/grafana/tag-values', view_func=grafana_tag_values, methods=['POST'])