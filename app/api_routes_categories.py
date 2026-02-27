from flask import request, jsonify, current_app, abort
from flask_restx import Resource
from .models import Category, Entry
from app import db
from .api_models import (
    categories_ns, category_model, category_input_model, 
    error_model, success_model
)

@categories_ns.route('/')
class CategoriesListAPI(Resource):
    @categories_ns.doc('list_categories')
    @categories_ns.marshal_list_with(category_model)
    def get(self):
        """Get all categories"""
        categories = Category.query.all()
        return categories
    
    @categories_ns.doc('create_category')
    @categories_ns.expect(category_input_model)
    @categories_ns.marshal_with(category_model, code=201)
    @categories_ns.response(400, 'Validation error', error_model)
    def post(self):
        """Create a new category"""
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return {'error': 'Category name is required'}, 400
        
        # Check if category already exists
        existing_category = Category.query.filter_by(name=data.get('name')).first()
        if existing_category:
            return {'error': 'Category with this name already exists'}, 400
        
        try:
            new_category = Category(
                name=data.get('name'),
                symbol=data.get('symbol', ''),
                color_hex=data.get('color_hex', '#FFFFFF'),
                repeat_annually=data.get('repeat_annually', False),
                display_celebration=data.get('display_celebration', False),
                is_protected=data.get('is_protected', False),
                last_updated_by=request.remote_addr
            )
            db.session.add(new_category)
            db.session.commit()
            return new_category, 201
        except Exception as e:
            current_app.logger.error(f"Failed to create category: {e}")
            return {'error': 'Failed to create category'}, 500

@categories_ns.route('/<int:category_id>')
class CategoryAPI(Resource):
    @categories_ns.doc('get_category')
    @categories_ns.marshal_with(category_model)
    @categories_ns.response(404, 'Category not found', error_model)
    def get(self, category_id):
        """Get a specific category by ID"""
        category = db.session.get(Category, category_id)
        if not category:
            abort(404)
        return category
    
    @categories_ns.doc('update_category')
    @categories_ns.expect(category_input_model)
    @categories_ns.marshal_with(category_model)
    @categories_ns.response(400, 'Validation error', error_model)
    @categories_ns.response(404, 'Category not found', error_model)
    def put(self, category_id):
        """Update a category"""
        category = db.session.get(Category, category_id)
        if not category:
            abort(404)
        
        data = request.json
        
        # Validate name if provided
        if data.get('name') and data.get('name') != category.name:
            existing_category = Category.query.filter_by(name=data.get('name')).first()
            if existing_category:
                return {'error': 'Category with this name already exists'}, 400
        
        try:
            if data.get('name'):
                category.name = data.get('name')
            if 'symbol' in data:
                category.symbol = data.get('symbol')
            if 'color_hex' in data:
                category.color_hex = data.get('color_hex')
            if 'repeat_annually' in data:
                category.repeat_annually = data.get('repeat_annually')
            if 'display_celebration' in data:
                category.display_celebration = data.get('display_celebration')
            if 'is_protected' in data:
                category.is_protected = data.get('is_protected')
            
            category.last_updated_by = request.remote_addr
            db.session.commit()
            return category
        except Exception as e:
            current_app.logger.error(f"Failed to update category: {e}")
            return {'error': 'Failed to update category'}, 500
    
    @categories_ns.doc('delete_category')
    @categories_ns.response(204, 'Category deleted')
    @categories_ns.response(400, 'Cannot delete category with entries', error_model)
    @categories_ns.response(404, 'Category not found', error_model)
    def delete(self, category_id):
        """Delete a category (only if no entries are associated)"""
        category = db.session.get(Category, category_id)
        if not category:
            abort(404)
        
        # Check if category has associated entries
        if db.session.query(Entry).filter_by(category_id=category_id).first():
            return {'error': 'Cannot delete category because it has associated entries'}, 400
        
        try:
            db.session.delete(category)
            db.session.commit()
            return '', 204
        except Exception as e:
            current_app.logger.error(f"Failed to delete category: {e}")
            return {'error': 'Failed to delete category'}, 500

@categories_ns.route('/names')
class CategoryNamesAPI(Resource):
    @categories_ns.doc('get_category_names')
    def get(self):
        """Get list of category names (for dropdowns/selects)"""
        categories = Category.query.all()
        return [{'id': cat.id, 'name': cat.name, 'symbol': cat.symbol} for cat in categories]
