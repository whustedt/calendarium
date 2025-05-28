from flask import request, jsonify, current_app, abort
from flask_restx import Resource
from .models import Quote
from app import db
from .api_models import (
    quotes_ns, quote_model, quote_input_model, 
    quote_response_model, error_model
)

# Import quote-related functions
try:
    from .routes_quotes import (
        select_daily_quote, get_random_quote, 
        generate_day_seed, QuoteConstants,
        format_quote, generate_color_hue, generate_hsl_color
    )
except ImportError:
    # Fallback definitions if imports fail
    def select_daily_quote(category=None):
        return Quote.query.first()
    
    def get_random_quote(category=None):
        return Quote.query.order_by(db.func.random()).first()
    
    def generate_day_seed():
        return 42
    
    class QuoteConstants:
        MAX_TEXT_LENGTH = 1000
        MAX_AUTHOR_LENGTH = 200
        MAX_CATEGORY_LENGTH = 100
        MAX_URL_LENGTH = 500

@quotes_ns.route('/')
class QuotesListAPI(Resource):
    @quotes_ns.doc('list_quotes')
    @quotes_ns.marshal_list_with(quote_model)
    def get(self):
        """Get all quotes"""
        quotes = Quote.query.all()
        return quotes
    
    @quotes_ns.doc('create_quote')
    @quotes_ns.expect(quote_input_model)
    @quotes_ns.marshal_with(quote_model, code=201)
    @quotes_ns.response(400, 'Validation error', error_model)
    def post(self):
        """Create a new quote"""
        data = request.json
        
        # Validate required fields
        if not data.get('text') or not data.get('author'):
            return {'error': 'Please provide both quote text and author'}, 400
        
        # Validate field lengths
        text = data.get('text', '').strip()
        author = data.get('author', '').strip()
        category = data.get('category', '').strip()
        url = data.get('url', '').strip()
        
        if len(text) > QuoteConstants.MAX_TEXT_LENGTH:
            return {'error': f'Quote text is too long (maximum {QuoteConstants.MAX_TEXT_LENGTH} characters)'}, 400
        
        if len(author) > QuoteConstants.MAX_AUTHOR_LENGTH:
            return {'error': f'Author name is too long (maximum {QuoteConstants.MAX_AUTHOR_LENGTH} characters)'}, 400
        
        if category and len(category) > QuoteConstants.MAX_CATEGORY_LENGTH:
            return {'error': f'Category is too long (maximum {QuoteConstants.MAX_CATEGORY_LENGTH} characters)'}, 400
        
        if url and len(url) > QuoteConstants.MAX_URL_LENGTH:
            return {'error': f'URL is too long (maximum {QuoteConstants.MAX_URL_LENGTH} characters)'}, 400
        
        try:
            new_quote = Quote(
                text=text,
                author=author,
                category=category or None,
                url=url or None,
                last_updated_by=request.remote_addr
            )
            db.session.add(new_quote)
            db.session.commit()
            return new_quote, 201
        except Exception as e:
            current_app.logger.error(f"Failed to create quote: {e}")
            return {'error': 'Failed to create quote'}, 500

@quotes_ns.route('/<int:quote_id>')
class QuoteAPI(Resource):
    @quotes_ns.doc('get_quote')
    @quotes_ns.marshal_with(quote_model)
    @quotes_ns.response(404, 'Quote not found', error_model)
    def get(self, quote_id):
        """Get a specific quote by ID"""
        quote = db.session.get(Quote, quote_id)
        if not quote:
            abort(404)
        return quote
    
    @quotes_ns.doc('update_quote')
    @quotes_ns.expect(quote_input_model)
    @quotes_ns.marshal_with(quote_model)
    @quotes_ns.response(400, 'Validation error', error_model)
    @quotes_ns.response(404, 'Quote not found', error_model)
    def put(self, quote_id):
        """Update a quote"""
        quote = db.session.get(Quote, quote_id)
        if not quote:
            abort(404)
        
        data = request.json
        
        # Validate required fields
        text = data.get('text', '').strip()
        author = data.get('author', '').strip()
        
        if not text or not author:
            return {'error': 'Please provide both quote text and author'}, 400
        
        # Validate field lengths
        category = data.get('category', '').strip()
        url = data.get('url', '').strip()
        
        if len(text) > QuoteConstants.MAX_TEXT_LENGTH:
            return {'error': f'Quote text is too long (maximum {QuoteConstants.MAX_TEXT_LENGTH} characters)'}, 400
        
        if len(author) > QuoteConstants.MAX_AUTHOR_LENGTH:
            return {'error': f'Author name is too long (maximum {QuoteConstants.MAX_AUTHOR_LENGTH} characters)'}, 400
        
        if category and len(category) > QuoteConstants.MAX_CATEGORY_LENGTH:
            return {'error': f'Category is too long (maximum {QuoteConstants.MAX_CATEGORY_LENGTH} characters)'}, 400
        
        if url and len(url) > QuoteConstants.MAX_URL_LENGTH:
            return {'error': f'URL is too long (maximum {QuoteConstants.MAX_URL_LENGTH} characters)'}, 400
        
        try:
            quote.text = text
            quote.author = author
            quote.category = category or None
            quote.url = url or None
            quote.last_updated_by = request.remote_addr
            db.session.commit()
            return quote
        except Exception as e:
            current_app.logger.error(f"Failed to update quote: {e}")
            return {'error': 'Failed to update quote'}, 500
    
    @quotes_ns.doc('delete_quote')
    @quotes_ns.response(204, 'Quote deleted')
    @quotes_ns.response(404, 'Quote not found', error_model)
    def delete(self, quote_id):
        """Delete a quote"""
        quote = db.session.get(Quote, quote_id)
        if not quote:
            abort(404)
        
        try:
            db.session.delete(quote)
            db.session.commit()
            return '', 204
        except Exception as e:
            current_app.logger.error(f"Failed to delete quote: {e}")
            return {'error': 'Failed to delete quote'}, 500

@quotes_ns.route('/daily')
class DailyQuoteAPI(Resource):
    @quotes_ns.doc('get_daily_quote')
    @quotes_ns.param('category', 'Filter by category (comma-separated)', type=str, required=False)
    @quotes_ns.param('color', 'Generate background color', type=bool, required=False)
    @quotes_ns.marshal_with(quote_response_model)
    @quotes_ns.response(404, 'No quotes found', error_model)
    def get(self):
        """Get daily quote with consistent selection throughout the day"""
        category = request.args.get('category')
        generate_color = request.args.get('color') is not None
        
        quote = select_daily_quote(category=category)
        if not quote:
            return {'error': 'No quotes found'}, 404
        
        try:
            day_seed = generate_day_seed()
            hue = generate_color_hue(day_seed) if generate_color else None
            
            response_data = format_quote(quote, hue)
            response_data["period"] = "Daily"
            
            return response_data
        except Exception as e:
            current_app.logger.error(f"Failed to format daily quote: {e}")
            return {'error': 'Failed to format quote'}, 500

@quotes_ns.route('/random')
class RandomQuoteAPI(Resource):
    @quotes_ns.doc('get_random_quote')
    @quotes_ns.param('category', 'Filter by category (comma-separated)', type=str, required=False)
    @quotes_ns.param('color', 'Generate background color', type=bool, required=False)
    @quotes_ns.marshal_with(quote_response_model)
    @quotes_ns.response(404, 'No quotes found', error_model)
    def get(self):
        """Get a random quote"""
        category = request.args.get('category')
        generate_color = request.args.get('color') is not None
        
        quote = get_random_quote(category=category)
        if not quote:
            return {'error': 'No quotes found'}, 404
        
        try:
            hue = generate_color_hue() if generate_color else None
            
            response_data = format_quote(quote, hue)
            response_data["period"] = "Random"
            
            return response_data
        except Exception as e:
            current_app.logger.error(f"Failed to format random quote: {e}")
            return {'error': 'Failed to format quote'}, 500

@quotes_ns.route('/categories')
class QuoteCategoriesAPI(Resource):
    @quotes_ns.doc('get_quote_categories')
    def get(self):
        """Get list of unique quote categories"""
        try:
            categories = db.session.query(Quote.category).filter(Quote.category.isnot(None)).distinct().all()
            return [cat[0] for cat in categories if cat[0]]
        except Exception as e:
            current_app.logger.error(f"Failed to get quote categories: {e}")
            return {'error': 'Failed to get categories'}, 500
