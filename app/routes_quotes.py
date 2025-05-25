from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from markdown import markdown
from markupsafe import Markup
from .models import Quote
from datetime import date, timedelta
import random
from app import db

def generate_hsl_color(hue):
    return f"hsl({hue}, 70%, 30%)" if hue is not None else None

def get_random_quote(seed=None, category=None):
    query = Quote.query
    if category:
        cats = [c.strip() for c in category.split(',')]
        query = query.filter(Quote.category.in_(cats))
    quotes = query.all()
    if not quotes:
        return None
    return random.Random(seed).choice(quotes) if seed is not None else random.choice(quotes)

def generate_day_seed(offset=0):
    """DDMMYYYY as int for today+offset days."""
    target = date.today() + timedelta(days=offset)
    return int(target.strftime("%d%m%Y"))

def generate_week_seed(offset=0):
    """YYYYWW as int for current ISO week + offset weeks."""
    target = date.today() + timedelta(weeks=offset)
    year, week, _ = target.isocalendar()
    return int(f"{year}{week:02d}")

def generate_color_hue(seed=None):
    return random.Random(seed).randint(0, 360) if seed is not None else random.randint(0, 360)

def format_quote(quote, color_hue=None):
    return {
        "id": quote.id,
        "text": quote.text,
        "author": quote.author,
        "category": quote.category,
        "url": quote.url,
        "backgroundColor": generate_hsl_color(color_hue)
    }

# ─── deterministic "no-repeat" helpers ────────────────────────────────────

def get_last_n_seeds(generator, n):
    """Generic: call generator(offset=-i) for i in 1..n."""
    return [generator(offset=-i) for i in range(1, n + 1)]

def get_daily_quote_no_repeats(lookback_days=5, category=None):
    # Get all available quotes for this category first
    query = Quote.query
    if category:
        cats = [c.strip() for c in category.split(",")]
        query = query.filter(Quote.category.in_(cats))
    available_quotes = query.all()
    
    if not available_quotes:
        return None, generate_day_seed()
        
    # build set of IDs from the last N days
    recent_ids = {
        quote.id
        for s in get_last_n_seeds(generate_day_seed, lookback_days)
        if (quote := get_random_quote(seed=s, category=category)) is not None
    }
    
    base_seed = generate_day_seed()
    available_ids = {q.id for q in available_quotes}
    candidate_ids = available_ids - recent_ids
    
    # If we have candidates not recently used, try to use one of those
    if candidate_ids:
        for i in range(len(candidate_ids)):
            seed = base_seed + i
            q = get_random_quote(seed=seed, category=category)
            if q and q.id in candidate_ids:
                return q, seed
    
    # If all quotes were recently used or we couldn't find a good candidate,
    # fall back to true daily random from all quotes
    # Debug: Logging fallback reason for traceability
    current_app.logger.info("Fallback to true daily random: All quotes were recently used or no suitable candidate found.")
    return get_random_quote(seed=base_seed, category=category), base_seed

def get_weekly_quote_no_repeats(lookback_weeks=5, category=None):
    # Get all available quotes for this category first
    query = Quote.query
    if category:
        cats = [c.strip() for c in category.split(",")]
        query = query.filter(Quote.category.in_(cats))
    available_quotes = query.all()
    
    if not available_quotes:
        return None, generate_week_seed()
        
    # build set of IDs from the last N weeks
    recent_ids = {
        quote.id
        for s in get_last_n_seeds(generate_week_seed, lookback_weeks)
        if (quote := get_random_quote(seed=s, category=category)) is not None
    }
    
    base_seed = generate_week_seed()
    available_ids = {q.id for q in available_quotes}
    candidate_ids = available_ids - recent_ids
    
    # If we have candidates not recently used, try to use one of those
    if candidate_ids:
        for i in range(len(candidate_ids)):
            seed = base_seed + i
            q = get_random_quote(seed=seed, category=category)
            if q and q.id in candidate_ids:
                return q, seed
    
    # If all quotes were recently used or we couldn't find a good candidate,
    # fall back to true weekly random from all quotes
    # Debug: Logging fallback reason for traceability
    current_app.logger.info("Fallback to true weekly random: All quotes were recently used or no suitable candidate found.")
    return get_random_quote(seed=base_seed, category=category), base_seed

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
        text = request.form.get('text')
        author = request.form.get('author')
        category = request.form.get('category')
        url = request.form.get('url')
        if not text or not author:
            flash("Please provide both quote and author.")
            return redirect(url_for('list_quotes'))
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

    @app.route('/quotes/edit/<int:id>', methods=['POST'])
    def edit_quote(id):
        quote = Quote.query.get_or_404(id)
        quote.text = request.form.get('text')
        quote.author = request.form.get('author')
        quote.category = request.form.get('category')
        quote.url = request.form.get('url')
        quote.last_updated_by = request.remote_addr
        db.session.commit()
        return redirect(url_for('list_quotes'))

    @app.route('/quotes/delete/<int:id>', methods=['POST'])
    def delete_quote(id):
        quote = Quote.query.get_or_404(id)
        db.session.delete(quote)
        db.session.commit()
        return redirect(url_for('list_quotes'))

    @app.route('/quotes/random', methods=['GET'])
    def random_quote():
        cat = request.args.get('category')
        q = get_random_quote(category=cat)
        return get_quote_response(True, q, None, "Random")

    @app.route('/quotes/random/view', methods=['GET'])
    def random_quote_view():
        cat = request.args.get('category')
        q = get_random_quote(category=cat)
        return get_quote_response(False, q, None, "Random")

    @app.route('/quotes/weekly', methods=['GET'])
    def weekly_quote():
        """JSON: deterministic no-repeat weekly (last 5 weeks)"""
        cat = request.args.get('category')
        q, used_seed = get_weekly_quote_no_repeats(lookback_weeks=5, category=cat)
        return get_quote_response(True, q, used_seed, "Weekly")

    @app.route('/quotes/weekly/view', methods=['GET'])
    def weekly_quote_view():
        """HTML: deterministic no-repeat weekly (last 5 weeks)"""
        cat = request.args.get('category')
        q, used_seed = get_weekly_quote_no_repeats(lookback_weeks=5, category=cat)
        return get_quote_response(False, q, used_seed, "Weekly")

    @app.route('/quotes/daily', methods=['GET'])
    def daily_quote():
        """JSON: deterministic no-repeat daily (last 5 days)"""
        cat = request.args.get('category')
        q, used_seed = get_daily_quote_no_repeats(lookback_days=5, category=cat)
        return get_quote_response(True, q, used_seed, "Daily")

    @app.route('/quotes/daily/view', methods=['GET'])
    def daily_quote_view():
        """HTML: deterministic no-repeat daily (last 5 days)"""
        cat = request.args.get('category')
        q, used_seed = get_daily_quote_no_repeats(lookback_days=5, category=cat)
        return get_quote_response(False, q, used_seed, "Daily")