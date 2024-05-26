from flask import request, jsonify, current_app
from datetime import datetime
from .models import Entry
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
        Endpoint for Grafana to search available targets.

        :return: JSON list of available categories as targets
        """
        try:
            targets = [category for category in Entry.CATEGORIES]
            return jsonify(targets)
        except Exception as e:
            current_app.logger.error(f"Search failed: {e}")
            return jsonify({"error": "Search failed"}), 500

    @app.route('/grafana/query', methods=['POST'])
    def grafana_query():
        """
        Endpoint for Grafana to query data.

        :return: JSON formatted data points for Grafana
        """
        req = request.get_json()
        try:
            response = []
            # Iterate over each target provided by Grafana
            for target in req['targets']:
                # Check if the target type is 'timeserie' and target exists in categories
                if target['type'] == 'timeserie' and target['target'] in Entry.CATEGORIES:
                    # Query to get date and count of entries matching the category
                    data_points = db.session.query(
                        Entry.date,
                        db.func.count(Entry.id).label('count')
                    ).filter(Entry.category == target['target']).group_by(Entry.date).all()

                    # Format data points to fit Grafana's expected format: [value, timestamp]
                    datapoints = [
                        [count, datetime.strptime(date, '%Y-%m-%d').timestamp() * 1000] 
                        for date, count in data_points
                    ]

                    # Add this to response
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
        Endpoint for Grafana to fetch annotations.

        :return: JSON list of annotations
        """
        req = request.get_json()
        try:
            annotations = []
            query = req['annotation']['query']
            if query == '#deploy':
                entries = db.session.query(Entry).filter(Entry.category == 'release').all()
                for entry in entries:
                    annotations.append({
                        "annotation": req['annotation'],
                        "time": datetime.strptime(entry.date, '%Y-%m-%d').timestamp() * 1000,
                        "title": entry.title,
                        "tags": [entry.category],
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
        Endpoint for Grafana to fetch tag values based on key.

        :return: JSON list of tag values
        """
        req = request.get_json()
        key = req['key']
        if key == "category":
            values = [{"text": cat} for cat in Entry.CATEGORIES]
        elif key == "date":
            dates = db.session.query(Entry.date).distinct().all()
            values = [{"text": date[0]} for date in dates]
        else:
            values = []
        return jsonify(values)

    app.add_url_rule('/grafana/', view_func=grafana_test_connection)
    app.add_url_rule('/grafana/search', view_func=grafana_search, methods=['POST'])
    app.add_url_rule('/grafana/query', view_func=grafana_query, methods=['POST'])
    app.add_url_rule('/grafana/annotations', view_func=grafana_annotations, methods=['POST'])
    app.add_url_rule('/grafana/tag-keys', view_func=grafana_tag_keys, methods=['POST'])
    app.add_url_rule('/grafana/tag-values', view_func=grafana_tag_values, methods=['POST'])