from flask import request, jsonify, current_app, abort
from flask_restx import Resource
import validators
from .models import Entry, Category
from app import db
from .helpers import handle_image_upload, parse_date, get_entry_data
from .api_models import (
    entries_ns, entry_model, entry_input_model, 
    api_data_model, error_model, success_model
)

@entries_ns.route('/')
class EntriesListAPI(Resource):
    @entries_ns.doc('list_entries')
    @entries_ns.marshal_with(api_data_model)
    def get(self):
        """Get all entries and categories"""
        return get_entry_data(db)

@entries_ns.route('/data')
class EntriesDataAPI(Resource):
    @entries_ns.doc('get_entries_data')
    @entries_ns.marshal_with(api_data_model)
    def get(self):
        """Get all entries data with additional formatting"""
        return get_entry_data(db)

@entries_ns.route('/<int:entry_id>')
class EntryAPI(Resource):
    @entries_ns.doc('get_entry')
    @entries_ns.marshal_with(entry_model)
    @entries_ns.response(404, 'Entry not found', error_model)
    def get(self, entry_id):
        """Get a specific entry by ID"""
        entry = db.session.get(Entry, entry_id)
        if not entry:
            abort(404)
        return entry
    
    @entries_ns.doc('update_entry')
    @entries_ns.expect(entry_input_model)
    @entries_ns.marshal_with(entry_model)
    @entries_ns.response(400, 'Validation error', error_model)
    @entries_ns.response(404, 'Entry not found', error_model)
    def put(self, entry_id):
        """Update an entry"""
        entry = db.session.get(Entry, entry_id)
        if not entry:
            abort(404)
        
        data = request.json
        
        # Validate category
        category = db.session.query(Category).filter_by(name=data.get('category')).first()
        if not category:
            return {'error': 'Invalid category'}, 400
        
        # Validate date
        if not parse_date(data.get('date')):
            return {'error': 'Invalid date format, must be YYYY-MM-DD'}, 400
        
        # Validate URL if provided
        if data.get('url') and not validators.url(data.get('url')):
            return {'error': 'Invalid URL'}, 400
        
        # Update entry
        entry.category_id = category.id
        entry.date = data.get('date')
        entry.title = data.get('title')
        entry.description = data.get('description')
        entry.url = data.get('url')
        entry.last_updated_by = request.remote_addr
        
        try:
            db.session.commit()
            return entry
        except Exception as e:
            current_app.logger.error(f"Failed to update entry: {e}")
            return {'error': 'Failed to update entry'}, 500
    
    @entries_ns.doc('delete_entry')
    @entries_ns.response(204, 'Entry deleted')
    @entries_ns.response(404, 'Entry not found', error_model)
    def delete(self, entry_id):
        """Delete an entry"""
        entry = db.session.get(Entry, entry_id)
        if not entry:
            abort(404)
        
        try:
            # Remove associated image if exists
            if entry.image_filename:
                import os
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], entry.image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
            
            db.session.delete(entry)
            db.session.commit()
            return '', 204
        except Exception as e:
            current_app.logger.error(f"Failed to delete entry: {e}")
            return {'error': 'Failed to delete entry'}, 500

@entries_ns.route('')
class EntriesAPI(Resource):
    @entries_ns.doc('create_entry')
    @entries_ns.expect(entry_input_model)
    @entries_ns.marshal_with(entry_model, code=201)
    @entries_ns.response(400, 'Validation error', error_model)
    def post(self):
        """Create a new entry"""
        data = request.json
        
        # Validate required fields
        errors = []
        if not data.get('date'):
            errors.append("Date is required")
        if not data.get('title'):
            errors.append("Title is required")
        if not data.get('category'):
            errors.append("Category is required")
        
        if errors:
            return {'error': '; '.join(errors)}, 400
        
        # Validate category
        category = db.session.query(Category).filter_by(name=data.get('category')).first()
        if not category:
            return {'error': 'Invalid category'}, 400
        
        # Validate date
        if not parse_date(data.get('date')):
            return {'error': 'Invalid date format, must be YYYY-MM-DD'}, 400
        
        # Validate URL if provided
        if data.get('url') and not validators.url(data.get('url')):
            return {'error': 'Invalid URL'}, 400
        
        try:
            new_entry = Entry(
                date=data.get('date'),
                category_id=category.id,
                title=data.get('title'),
                description=data.get('description'),
                url=data.get('url'),
                last_updated_by=request.remote_addr
            )
            db.session.add(new_entry)
            db.session.commit()
            return new_entry, 201
        except Exception as e:
            current_app.logger.error(f"Failed to create entry: {e}")
            return {'error': 'Failed to create entry'}, 500

@entries_ns.route('/<int:entry_id>/toggle-cancelled')
class EntryToggleCancelledAPI(Resource):
    @entries_ns.doc('toggle_entry_cancelled')
    @entries_ns.marshal_with(entry_model)
    @entries_ns.response(404, 'Entry not found', error_model)
    def post(self, entry_id):
        """Toggle the cancelled state of an entry"""
        entry = db.session.get(Entry, entry_id)
        if not entry:
            abort(404)
        
        try:
            entry.cancelled = not entry.cancelled
            db.session.commit()
            return entry
        except Exception as e:
            current_app.logger.error(f"Failed to toggle entry cancelled state: {e}")
            return {'error': 'Failed to update entry'}, 500

@entries_ns.route('/update-serial')
class UpdateSerialEntriesAPI(Resource):
    @entries_ns.doc('update_serial_entries')
    @entries_ns.marshal_with(success_model)
    def post(self):
        """Update all serial entries to the current year"""
        try:
            from datetime import datetime
            current_year = datetime.now().year
            serial_categories = db.session.query(Category).filter_by(repeat_annually=True).all()
            category_ids = [category.id for category in serial_categories]
            
            serial_entries = db.session.query(Entry).filter(Entry.category_id.in_(category_ids)).all()
            for entry in serial_entries:
                entry.date = f"{current_year}-{entry.date.split('-')[1]}-{entry.date.split('-')[2]}"
            
            db.session.commit()
            current_app.logger.info("All serial entries have been updated to the current year")
            return {'message': 'All serial entries have been updated to the current year'}
        except Exception as e:
            current_app.logger.error(f"Failed to update serial entries: {e}")
            return {'error': 'Failed to update serial entries'}, 500

@entries_ns.route('/purge-old')
class PurgeOldEntriesAPI(Resource):
    @entries_ns.doc('purge_old_entries')
    @entries_ns.marshal_with(success_model)
    def post(self):
        """Delete old entries that are not protected and past current date"""
        try:
            from datetime import datetime
            import os
            
            current_date = datetime.now().date()
            unprotected_categories = db.session.query(Category).filter_by(is_protected=False).all()
            category_ids = [category.id for category in unprotected_categories]
            
            old_entries = db.session.query(Entry).filter(
                Entry.category_id.in_(category_ids),
                Entry.date < str(current_date)
            ).all()
            
            for entry in old_entries:
                if entry.image_filename:
                    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], entry.image_filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                db.session.delete(entry)
            
            db.session.commit()
            current_app.logger.info("Old entries have been purged")
            return {'message': 'Old entries have been purged'}
        except Exception as e:
            current_app.logger.error(f"Failed to purge old entries: {e}")
            return {'error': 'Failed to purge old entries'}, 500
