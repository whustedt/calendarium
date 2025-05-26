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
    query = Quote.query
    if category:
        cats = [c.strip() for c in category.split(',')]
        query = query.filter(Quote.category.in_(cats))
    quotes = query.all()
    if not quotes:
        return None
    return random.Random(seed).choice(quotes) if seed is not None else random.choice(quotes)

def generate_day_seed():
    """Erstellt einen Seed basierend auf Tag, Monat und Jahr (z.B. '26032025')"""
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
    """Wählt nach Tageszyklus ohne Wiederholung und schreibt last_shown."""
    today = date.today()

    # 1) Bereits heute gezogen?
    base_q = Quote.query.filter(Quote.last_shown == today)
    if category:
        cats = [c.strip() for c in category.split(',')]
        base_q = base_q.filter(Quote.category.in_(cats))
    existing = base_q.first()
    if existing:
        return existing

    # 2) Ermittle das "earliest" last_shown (NULLS FIRST)
    sub = (
        Quote.query
             .order_by(asc(Quote.last_shown).nullsfirst())
    )
    if category:
        sub = sub.filter(Quote.category.in_(cats))
    earliest_date = sub.with_entities(Quote.last_shown).limit(1).scalar()

    # 3) Alle mit diesem Datum holen
    candidates = Quote.query.filter(Quote.last_shown == earliest_date)
    if category:
        candidates = candidates.filter(Quote.category.in_(cats))
    candidates = candidates.all()
    if not candidates:
        return None

    # 4) Deterministischer Tiebreaker per SHA-256-Hash von "YYYY-MM-DD-id"
    def score(q):
        key = f"{today.isoformat()}-{q.id}"
        return int(hashlib.sha256(key.encode()).hexdigest(), 16)

    winner = min(candidates, key=score)

    # 5) last_shown updaten
    winner.last_shown = today
    db.session.commit()

    return winner

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