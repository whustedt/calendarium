from flask import current_app, request, jsonify, send_file, make_response
from .models import Entry, Category, Quote
from .helpers import get_entry_data, create_zip, get_entry_data
from urllib.parse import unquote_plus
from os import path
from app import db 

def init_maintenance_routes(app):

    @app.route('/batch-import', methods=['POST'])
    def batch_import():
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Kategorien importieren
        if 'categories' in data:
            for category_data in data['categories']:
                category = Category.query.filter_by(name=category_data['name']).first()
                if not category:
                    category = Category(
                        name=category_data['name'],
                        symbol=category_data.get('symbol', ''),
                        color_hex=category_data.get('color_hex', '#FFFFFF'),
                        repeat_annually=category_data.get('repeat_annually', False),
                        display_celebration=category_data.get('display_celebration', False),
                        is_protected=category_data.get('is_protected', False),
                        last_updated_by=category_data.get('last_updated_by', request.remote_addr)
                    )
                    db.session.add(category)
                else:
                    category.symbol = category_data.get('symbol', category.symbol)
                    category.color_hex = category_data.get('color_hex', category.color_hex)
                    category.repeat_annually = category_data.get('repeat_annually', category.repeat_annually)
                    category.display_celebration = category_data.get('display_celebration', category.display_celebration)
                    category.is_protected = category_data.get('is_protected', category.is_protected)
                    category.last_updated_by = category_data.get('last_updated_by', request.remote_addr)

        db.session.flush()

        # Kalendereinträge importieren
        if 'entries' in data:
            for entry_data in data['entries']:
                category = Category.query.filter_by(name=entry_data.get('category').get('name')).first()
                if not category:
                    return jsonify({"error": f"Category '{entry_data.get('category')}' not found"}), 400
                new_entry = Entry(
                    date=entry_data['date'],
                    category_id=category.id,
                    title=entry_data['title'],
                    description=entry_data.get('description', None),
                    url=entry_data.get('url', None),
                    cancelled=entry_data.get('cancelled', False),
                    last_updated_by=entry_data.get('last_updated_by', request.remote_addr)
                )
                db.session.add(new_entry)
        
        # Zitate importieren
        if 'quotes' in data:
            for quote_data in data['quotes']:
                existing = Quote.query.filter_by(text=quote_data['text'], author=quote_data['author']).first()
                if not existing:
                    new_quote = Quote(
                        text=quote_data['text'],
                        author=quote_data['author'],
                        category=quote_data.get('category', None),
                        url=quote_data.get('url', None),
                        last_updated_by=quote_data.get('last_updated_by', request.remote_addr)
                    )
                    db.session.add(new_quote)

        db.session.commit()
        return jsonify({"message": "Import erfolgreich"}), 201

    @app.route('/export-data', methods=['GET'])
    def export_data():
        # Kombinierte Daten aus Kalender und Zitaten exportieren
        data = get_entry_data(db)  # Enthält entries und categories
        quotes = [{
            "id": quote.id,
            "text": quote.text,
            "author": quote.author,
            "category": quote.category,
            "url": quote.url,
            "last_updated_by": quote.last_updated_by,
            "last_shown": quote.last_shown
        } for quote in Quote.query.all()]
        data["quotes"] = quotes

        zip_buffer = create_zip(data, current_app.config['UPLOAD_FOLDER'], current_app.config['SQLALCHEMY_DATABASE_URI'])
        response = make_response(send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='data_export.zip'))
        response.headers['Content-Disposition'] = 'attachment; filename=data_export.zip'
        return response
