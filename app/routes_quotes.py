from flask import render_template, request, redirect, url_for, flash, jsonify
from markdown import markdown
from markupsafe import Markup
from .models import Quote
from datetime import date
import random
from app import db

def init_quote_routes(app):
    @app.template_filter('markdown')
    def markdown_filter(text):
        return Markup(markdown(text, extensions=['extra', 'nl2br']))

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
            category=category if category else None,
            url=url if url else None,
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
 
    def get_random_quote(seed=None, category=None):
        query = Quote.query
        if category:
            categories = [cat.strip() for cat in category.split(',')]
            query = query.filter(Quote.category.in_(categories))
        quotes = query.all()
        if not quotes:
            return None
        if seed is not None:
            rand = random.Random(seed)
            return rand.choice(quotes)
        return random.choice(quotes)
   
    def generate_day_seed():
        """Erstellt einen Seed basierend auf Tag, Monat und Jahr (z.B. '26032025')"""
        return int(date.today().strftime("%d%m%Y"))
   
    def generate_week_seed():
        """Erstellt einen Seed basierend auf Jahr und Kalenderwoche (z.B. '202512')"""
        today = date.today()
        return int(f"{today.year}{today.isocalendar()[1]:02d}")
   
    def format_quote(quote):
        """Formatiert den Quote als Dictionary"""
        return {
            "id": quote.id,
            "text": quote.text,
            "author": quote.author,
            "category": quote.category,
            "url": quote.url
        }
   
    def get_quote_response(json_response=False, seed=None, category=None, period_label=None):
        """
        Hilfsfunktion, die den Quote basierend auf Seed und Kategorie abruft und
        entweder als JSON oder HTML-Antwort zurückgibt.
        """
        quote = get_random_quote(seed=seed, category=category)
        if not quote:
            if json_response:
                return jsonify({"error": "No quotes found matching the criteria"}), 404
            return render_template('quotes/no_quote.html'), 404
   
        if json_response:
            return jsonify(format_quote(quote))
        return render_template('quotes/quote.html', quote=quote, period=period_label)
   
    @app.route('/quotes/random', methods=['GET'])
    def random_quote():
        """JSON endpoint for completely random quote (kein deterministischer Seed)"""
        category = request.args.get('category')
        return get_quote_response(json_response=True, seed=None, category=category, period_label="Random")
   
    @app.route('/quotes/random/view', methods=['GET'])
    def random_quote_view():
        """HTML endpoint for random quote"""
        category = request.args.get('category')
        return get_quote_response(json_response=False, seed=None, category=category, period_label="Random")
   
    @app.route('/quotes/weekly', methods=['GET'])
    def weekly_quote():
        """JSON endpoint for weekly quote"""
        category = request.args.get('category')
        week_seed = generate_week_seed()
        return get_quote_response(json_response=True, seed=week_seed, category=category, period_label="Weekly")
   
    @app.route('/quotes/weekly/view', methods=['GET'])
    def weekly_quote_view():
        """HTML endpoint for weekly quote"""
        category = request.args.get('category')
        week_seed = generate_week_seed()
        return get_quote_response(json_response=False, seed=week_seed, category=category, period_label="Weekly")
   
    @app.route('/quotes/daily', methods=['GET'])
    def daily_quote():
        """JSON endpoint for daily quote"""
        category = request.args.get('category')
        day_seed = generate_day_seed()
        return get_quote_response(json_response=True, seed=day_seed, category=category, period_label="Daily")
   
    @app.route('/quotes/daily/view', methods=['GET'])
    def daily_quote_view():
        """HTML endpoint for daily quote"""
        category = request.args.get('category')
        day_seed = generate_day_seed()
        return get_quote_response(json_response=False, seed=day_seed, category=category, period_label="Daily")