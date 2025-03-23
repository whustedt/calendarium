from flask import render_template, request, redirect, url_for, flash, jsonify
from .models import Quote
from datetime import date
import random
from app import db

def init_quote_routes(app):

    @app.route('/quotes/', methods=['GET'])
    def list_quotes():
        quotes = Quote.query.all()
        return render_template('admin/quotes.html', quotes=quotes)

    @app.route('/quotes/create', methods=['POST'])
    def create_quote():
        text = request.form.get('text')
        author = request.form.get('author')
        if not text or not author:
            flash("Please provide both quote and author.")
            return redirect(url_for('list_quotes'))
        new_quote = Quote(text=text, author=author, last_updated_by=request.remote_addr)
        db.session.add(new_quote)
        db.session.commit()
        return redirect(url_for('list_quotes'))

    @app.route('/quotes/edit/<int:id>', methods=['POST'])
    def edit_quote(id):
        quote = Quote.query.get_or_404(id)
        quote.text = request.form.get('text')
        quote.author = request.form.get('author')
        quote.last_updated_by = request.remote_addr
        db.session.commit()
        return redirect(url_for('list_quotes'))

    @app.route('/quotes/delete/<int:id>', methods=['POST'])
    def delete_quote(id):
        quote = Quote.query.get_or_404(id)
        db.session.delete(quote)
        db.session.commit()
        return redirect(url_for('list_quotes'))

    def get_random_quote(seed):
        quotes = Quote.query.all()
        if not quotes:
            return jsonify({"error": "No quotes available"}), 404
        random.seed(seed)
        quote = random.choice(quotes)
        return jsonify({
            "id": quote.id,
            "text": quote.text,
            "author": quote.author
        })

    @app.route('/quotes/weekly', methods=['GET'])
    def weekly_quote():
        week_seed = date.today().isocalendar()[1]
        return get_random_quote(week_seed)

    @app.route('/quotes/daily', methods=['GET'])
    def daily_quote():
        day_seed = date.today().day
        return get_random_quote(day_seed)