from flask import request, jsonify, current_app, send_file, make_response
from flask_restx import Resource
from .models import Entry, Category, Quote
from app import db
from .helpers import get_entry_data, create_zip
from .api_models import (
    maintenance_ns, batch_import_model, api_data_model,
    success_model, error_model
)

@maintenance_ns.route('/export')
class ExportDataAPI(Resource):
    @maintenance_ns.doc('export_data')
    def get(self):
        """Export all data (entries, categories, quotes) as a ZIP file"""
        try:
            # Get entry data (includes entries and categories)
            data = get_entry_data(db)
            
            # Add quotes data
            quotes = [{
                "id": quote.id,
                "text": quote.text,
                "author": quote.author,
                "category": quote.category,
                "url": quote.url,
                "last_updated_by": quote.last_updated_by,
                "last_shown": quote.last_shown.isoformat() if quote.last_shown else None
            } for quote in Quote.query.all()]
            data["quotes"] = quotes

            zip_buffer = create_zip(
                data, 
                current_app.config['UPLOAD_FOLDER'], 
                current_app.config['SQLALCHEMY_DATABASE_URI']
            )
            
            response = make_response(
                send_file(
                    zip_buffer, 
                    mimetype='application/zip', 
                    as_attachment=True, 
                    download_name='calendarium_export.zip'
                )
            )
            response.headers['Content-Disposition'] = 'attachment; filename=calendarium_export.zip'
            return response
        except Exception as e:
            current_app.logger.error(f"Export failed: {e}")
            return {'error': 'Failed to export data'}, 500

@maintenance_ns.route('/import')
class BatchImportAPI(Resource):
    @maintenance_ns.doc('batch_import')
    @maintenance_ns.expect(batch_import_model)
    @maintenance_ns.marshal_with(success_model, code=201)
    @maintenance_ns.response(400, 'Invalid data provided', error_model)
    @maintenance_ns.response(500, 'Import failed', error_model)
    def post(self):
        """Import batch data (categories, entries, quotes)"""
        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400

        try:
            # Import categories
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
                        # Update existing category
                        category.symbol = category_data.get('symbol', category.symbol)
                        category.color_hex = category_data.get('color_hex', category.color_hex)
                        category.repeat_annually = category_data.get('repeat_annually', category.repeat_annually)
                        category.display_celebration = category_data.get('display_celebration', category.display_celebration)
                        category.is_protected = category_data.get('is_protected', category.is_protected)
                        category.last_updated_by = category_data.get('last_updated_by', request.remote_addr)

            db.session.flush()

            # Import entries
            if 'entries' in data:
                for entry_data in data['entries']:
                    category_name = entry_data.get('category', {}).get('name') if isinstance(entry_data.get('category'), dict) else entry_data.get('category')
                    category = Category.query.filter_by(name=category_name).first()
                    if not category:
                        return {'error': f"Category '{category_name}' not found"}, 400
                    
                    # Check if entry already exists (avoid duplicates)
                    existing_entry = Entry.query.filter_by(
                        date=entry_data['date'],
                        title=entry_data['title'],
                        category_id=category.id
                    ).first()
                    
                    if not existing_entry:
                        new_entry = Entry(
                            date=entry_data['date'],
                            category_id=category.id,
                            title=entry_data['title'],
                            description=entry_data.get('description'),
                            url=entry_data.get('url'),
                            cancelled=entry_data.get('cancelled', False),
                            last_updated_by=entry_data.get('last_updated_by', request.remote_addr)
                        )
                        db.session.add(new_entry)

            # Import quotes
            if 'quotes' in data:
                for quote_data in data['quotes']:
                    # Check if quote already exists (avoid duplicates)
                    existing_quote = Quote.query.filter_by(
                        text=quote_data['text'], 
                        author=quote_data['author']
                    ).first()
                    
                    if not existing_quote:
                        new_quote = Quote(
                            text=quote_data['text'],
                            author=quote_data['author'],
                            category=quote_data.get('category'),
                            url=quote_data.get('url'),
                            last_updated_by=quote_data.get('last_updated_by', request.remote_addr)
                        )
                        db.session.add(new_quote)

            db.session.commit()
            return {'message': 'Import completed successfully'}, 201

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Import failed: {e}")
            return {'error': 'Import failed'}, 500

@maintenance_ns.route('/health')
class HealthCheckAPI(Resource):
    @maintenance_ns.doc('health_check')
    def get(self):
        """Health check endpoint"""
        try:
            # Test database connection
            db.session.execute(db.text('SELECT 1'))
            
            # Get basic stats
            entries_count = Entry.query.count()
            categories_count = Category.query.count()
            quotes_count = Quote.query.count()
            
            return {
                'status': 'healthy',
                'database': 'connected',
                'stats': {
                    'entries': entries_count,
                    'categories': categories_count,
                    'quotes': quotes_count
                }
            }
        except Exception as e:
            current_app.logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }, 500

@maintenance_ns.route('/stats')
class StatsAPI(Resource):
    @maintenance_ns.doc('get_stats')
    def get(self):
        """Get application statistics"""
        try:
            from datetime import datetime, timedelta
            
            # Basic counts
            total_entries = Entry.query.count()
            total_categories = Category.query.count()
            total_quotes = Quote.query.count()
            
            # Recent activity (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            recent_entries = Entry.query.filter(Entry.date >= thirty_days_ago).count()
            
            # Category breakdown
            category_stats = db.session.query(
                Category.name,
                db.func.count(Entry.id).label('entry_count')
            ).outerjoin(Entry).group_by(Category.name).all()
            
            category_breakdown = [
                {'category': name, 'count': count} 
                for name, count in category_stats
            ]
            
            return {
                'totals': {
                    'entries': total_entries,
                    'categories': total_categories,
                    'quotes': total_quotes
                },
                'recent_activity': {
                    'entries_last_30_days': recent_entries
                },
                'category_breakdown': category_breakdown
            }
        except Exception as e:
            current_app.logger.error(f"Stats retrieval failed: {e}")
            return {'error': 'Failed to retrieve statistics'}, 500
