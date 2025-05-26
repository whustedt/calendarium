from flask import render_template, request, redirect, url_for, flash, jsonify
from markdown import markdown
from markupsafe import Markup
from .models import Quote
from datetime import date
import hashlib
import random
from app import db
from sqlalchemy import func, asc

def generate_hsl_color(hue):
    return f"hsl({hue}, 70%, 30%)" if hue is not None else None

def get_random_quote(seed=None, category=None):
    """
    Get a random quote, optionally filtered by category.
    
    Args:
        seed (int, optional): Random seed for deterministic selection
        category (str, optional): Comma-separated list of categories to filter by
        
    Returns:
        Quote: Selected quote or None if no quotes match criteria
    """
    query = Quote.query
    if category:
        category_list = [c.strip() for c in category.split(',') if c.strip()]
        if category_list:
            query = query.filter(Quote.category.in_(category_list))
    
    quotes = query.all()
    if not quotes:
        return None
    
    if seed is not None:
        return random.Random(seed).choice(quotes)
    else:
        return random.choice(quotes)

def generate_day_seed():
    """Creates a seed based on day, month and year (e.g. '26032025')"""
    return int(date.today().strftime("%d%m%Y"))

def generate_color_hue(seed=None):
    return random.Random(seed).randint(0, 360) if seed is not None else random.randint(0, 360)

def format_quote(quote, color_hue=None):
    return {
        "id": quote.id,
        "text": quote.text,
        "author": quote.author,
        "category": quote.category,
        "url": quote.url,
        "backgroundColor": generate_hsl_color(color_hue),
        "lastShown": quote.last_shown.isoformat() if quote.last_shown else None,
        "lastUpdatedBy": quote.last_updated_by
    }

def select_daily_quote(category=None):
    """
    Selects a daily quote using fair rotation system.
    
    The algorithm ensures all quotes are shown before any repeats by:
    1. Checking if a quote was already selected today
    2. Finding quotes with the earliest last_shown date (prioritizing never-shown quotes)
    3. Using deterministic tiebreaker for consistent daily selection
    4. Updating the selected quote's last_shown date
    
    Args:
        category (str, optional): Comma-separated list of categories to filter by
        
    Returns:
        Quote: Selected quote or None if no quotes match criteria
    """
    today = date.today()
    
    # Parse categories if provided
    category_list = None
    if category:
        category_list = [c.strip() for c in category.split(',') if c.strip()]
        if not category_list:
            category_list = None

    # Check if quote already selected today
    existing_query = Quote.query.filter(Quote.last_shown == today)
    if category_list:
        existing_query = existing_query.filter(Quote.category.in_(category_list))
    
    existing = existing_query.first()
    if existing:
        return existing

    # Build base query with category filter
    base_query = Quote.query
    if category_list:
        base_query = base_query.filter(Quote.category.in_(category_list))

    # Find earliest last_shown date (NULL values first)
    earliest_date = (base_query
                    .order_by(asc(Quote.last_shown).nullsfirst())
                    .with_entities(Quote.last_shown)
                    .limit(1)
                    .scalar())

    # Get all candidates with earliest date
    candidates = (base_query
                 .filter(Quote.last_shown == earliest_date)
                 .all())
    
    if not candidates:
        return None

    # Deterministic tiebreaker using SHA-256 hash
    def deterministic_score(quote):
        key = f"{today.isoformat()}-{quote.id}"
        return int(hashlib.sha256(key.encode()).hexdigest(), 16)

    selected_quote = min(candidates, key=deterministic_score)

    # Update last_shown date
    selected_quote.last_shown = today
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return selected_quote

def init_quote_routes(app):
    @app.template_filter('markdown')
    def markdown_filter(text):
        return Markup(markdown(text, extensions=['extra', 'nl2br']))

    def get_quote_response(json_response, quote, seed, period_label):
        if not quote:
            if json_response:
                return jsonify({"error": "No quotes found"}), 404
            return render_template('quotes/no_quote.html'), 404

        hue = generate_color_hue(seed) if request.args.get('color') else None
        if json_response:
            data = format_quote(quote, hue)
            data["period"] = period_label
            return jsonify(data)
        return render_template(
            'quotes/quote.html',
            quote=quote,
            period=period_label,
            background_color=generate_hsl_color(hue)
        )

    @app.route('/quotes/', methods=['GET'])
    def list_quotes():
        quotes = Quote.query.all()
        return render_template('admin/quotes.html', quotes=quotes)

    @app.route('/quotes/create', methods=['POST'])
    def create_quote():
        text = request.form.get('text', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        url = request.form.get('url', '').strip()

        if not text or not author:
            return "Please provide both quote and author.", 400
        
        # Validate text length
        if len(text) > 1000:
            return "Quote text is too long (maximum 1000 characters).", 400
            
        # Validate author length
        if len(author) > 200:
            return "Author name is too long (maximum 200 characters).", 400
        
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
            return redirect(url_for('list_quotes'))
        except Exception as e:
            db.session.rollback()
            return f"Error creating quote: {str(e)}", 500

    @app.route('/quotes/edit/<int:id>', methods=['POST'])
    def edit_quote(id):
        quote = Quote.query.get_or_404(id)
        
        text = request.form.get('text', '').strip()
        author = request.form.get('author', '').strip()
        category = request.form.get('category', '').strip()
        url = request.form.get('url', '').strip()
        
        if not text or not author:
            return "Please provide both quote and author.", 400
        
        # Validate text length
        if len(text) > 1000:
            return "Quote text is too long (maximum 1000 characters).", 400
            
        # Validate author length
        if len(author) > 200:
            return "Author name is too long (maximum 200 characters).", 400
        
        try:
            quote.text = text
            quote.author = author
            quote.category = category or None
            quote.url = url or None
            quote.last_updated_by = request.remote_addr
            db.session.commit()
            return redirect(url_for('list_quotes'))
        except Exception as e:
            db.session.rollback()
            return f"Error updating quote: {str(e)}", 500

    @app.route('/quotes/delete/<int:id>', methods=['POST'])
    def delete_quote(id):
        quote = Quote.query.get_or_404(id)
        db.session.delete(quote)
        db.session.commit()
        return redirect(url_for('list_quotes'))

    @app.route('/quotes/random', methods=['GET'])
    def random_quote():
        """JSON endpoint for random quote"""
        cat = request.args.get('category')
        q = get_random_quote(category=cat)
        return get_quote_response(json_response=True, quote=q, seed=None, period_label="Random")

    @app.route('/quotes/random/view', methods=['GET'])
    def random_quote_view():
        """HTML endpoint for random quote"""
        cat = request.args.get('category')
        q = get_random_quote(category=cat)
        return get_quote_response(json_response=False, quote=q, seed=None, period_label="Random")

    @app.route('/quotes/daily', methods=['GET'])
    def daily_quote():
        """JSON endpoint for daily quote"""
        cat = request.args.get('category')
        q = select_daily_quote(category=cat)
        day_seed = generate_day_seed()
        return get_quote_response(json_response=True, quote=q, seed=day_seed, period_label="Daily")

    @app.route('/quotes/daily/view', methods=['GET'])
    def daily_quote_view():
        """HTML endpoint for daily quote"""
        cat = request.args.get('category')
        q = select_daily_quote(category=cat)
        day_seed = generate_day_seed()
        return get_quote_response(json_response=False, quote=q, seed=day_seed, period_label="Daily")