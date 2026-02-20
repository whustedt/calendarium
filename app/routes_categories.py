from flask import request, jsonify, render_template, redirect, url_for
from .models import Category, Entry
from app import db


def _parse_checkbox_value(form, field_name):
    value = form.get(field_name)
    if value is None:
        return False
    return value.lower() in {'true', '1', 'on', 'yes'}

def init_categories_routes(app):
    @app.route('/categories', methods=['GET', 'POST'])
    def categories():
        if request.method == 'POST':
            # Add a new category
            name = request.form.get('name')
            symbol = request.form.get('symbol')
            color_hex = request.form.get('color_hex')
            repeat_annually = _parse_checkbox_value(request.form, 'repeat_annually')
            display_celebration = _parse_checkbox_value(request.form, 'display_celebration')
            is_protected = _parse_checkbox_value(request.form, 'is_protected')
            last_updated_by = request.remote_addr

            new_category = Category(
                name=name, symbol=symbol, color_hex=color_hex,
                repeat_annually=repeat_annually, display_celebration=display_celebration,
                is_protected=is_protected, last_updated_by=last_updated_by
            )
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('categories'))

        categories = db.session.query(Category).all()
        return render_template('admin/categories.html', categories=categories)

    @app.route('/categories/update/<int:id>', methods=['POST'])
    def update_category(id):
        category = db.session.get(Category, id)
        if category:
            category.name = request.form.get('name', category.name)
            category.symbol = request.form.get('symbol', category.symbol)
            category.color_hex = request.form.get('color_hex', category.color_hex)
            category.repeat_annually = _parse_checkbox_value(request.form, 'repeat_annually')
            category.display_celebration = _parse_checkbox_value(request.form, 'display_celebration')
            category.is_protected = _parse_checkbox_value(request.form, 'is_protected')
            category.last_updated_by = request.remote_addr
            db.session.commit()
            return redirect(url_for('categories'))
        return jsonify({"error": "Category not found"}), 404
    
    @app.route('/categories/delete/<int:id>', methods=['POST'])
    def delete_category(id):
        category = db.session.get(Category, id)
        if category:
            if db.session.query(Entry).filter_by(category_id=id).first():
                return jsonify({"error": "Cannot delete category because it has associated entries"}), 400
            db.session.delete(category)
            db.session.commit()
            return redirect(url_for('categories'))
        return jsonify({"error": "Category not found"}), 404 
