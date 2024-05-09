from flask import request, jsonify, render_template, redirect, url_for, make_response
from . import app, db
from .models import Entry
from datetime import datetime, time
from babel.dates import format_date

@app.route('/', methods=['GET'])
def index():
    entries = Entry.query.all()
    return render_template('admin/index.html', entries=entries)

@app.route('/create', methods=['POST'])
def create():
    category = request.form['category']
    if category not in Entry.CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400
    
    new_entry = Entry(
        date=request.form['date'],
        category=category,
        title=request.form['title'],
        description=request.form.get('description', None) or None
    )
    db.session.add(new_entry)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    entry = Entry.query.get_or_404(id)
    if request.method == 'POST':
        if request.form['category'] not in Entry.CATEGORIES:
            return jsonify({"error": "Invalid category"}), 400
        
        entry.date = request.form['date']
        entry.category = request.form['category']
        entry.title = request.form['title']
        entry.description = request.form.get('description', None) or None
        
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('admin/update.html', entry=entry)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    entry = Entry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/timeline', methods=['GET'])
def timeline():
    timeline_height = request.args.get('timeline-height', default='calc(50vh - 20px)')[:15]
    entries = Entry.query.all()
    # Convert date strings to date objects within each entry and sort them
    for entry in entries:
        entry.date = datetime.strptime(entry.date, '%Y-%m-%d')
    entries_sorted = sorted(entries, key=lambda x: x.date)
    today = datetime.combine(datetime.now().date(), time(0, 0))  # Today at midnight
    past_items_indices = [i for i, entry in enumerate(entries_sorted) if entry.date < today]
    second_to_last_past_index = past_items_indices[-2] if len(past_items_indices) > 1 else None
    response = make_response(render_template('timeline/timeline.html', timeline_height=timeline_height, entries=entries_sorted, today=today, second_to_last_past_index=second_to_last_past_index))
    # Add CORS headers
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

@app.route('/api/data', methods=['GET'])
def api_data():
    data = [{'date': entry.date, 'category': entry.category, 'title': entry.title, 'description': entry.description} for entry in Entry.query.all()]
    response = jsonify(data)
    # Add CORS headers
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

@app.route('/update-birthdays', methods=['POST'])
def update_birthdays():
    current_year = datetime.now().year
    # Fetch all entries with category "birthday"
    birthday_entries = Entry.query.filter_by(category='birthday').all()
    # Update the date of each birthday entry
    for entry in birthday_entries:
        entry.date = f"{current_year}-{entry.date.split('-')[1]}-{entry.date.split('-')[2]}"
        db.session.commit()
    return jsonify({"message": "All birthday entries have been updated to the current year"}), 200

@app.route('/purge-old-entries', methods=['POST'])
def purge_old_entries():
    current_date = datetime.now().date()
    # Fetch all entries where the date is in the past and category is not 'birthday'
    old_entries = Entry.query.filter(Entry.date < str(current_date), Entry.category != 'birthday').all()
    if not old_entries:
        return jsonify({"message": "No old entries to delete"}), 404
    for entry in old_entries:
        db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Old entries have been purged"}), 200

@app.route('/batch-import', methods=['POST'])
def batch_import():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    for item in data:
        if 'category' not in item or item['category'] not in Entry.CATEGORIES:
            return jsonify({"error": f"Invalid category in data: {item.get('category', 'None')}"}), 400
        
        try:
            new_entry = Entry(
                date=item['date'],
                category=item['category'],
                title=item['title'],
                description=item.get('description', None) or None
            )
            db.session.add(new_entry)
        except KeyError as e:
            return jsonify({"error": f"Missing key in data: {e}"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    db.session.commit()
    return jsonify({"message": "Entries successfully imported"}), 201


