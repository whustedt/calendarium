from flask import request, jsonify, render_template, redirect, url_for, make_response, send_from_directory, current_app
from . import app, db, allowed_file, create_upload_folder
from .models import Entry
from datetime import datetime, time
from babel.dates import format_date
from os import path, remove
from functools import wraps

def handle_image(file, entry_id):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1]
        filename = f"{entry_id}.{ext}"
        filepath = path.join(app.config['UPLOAD_FOLDER'], filename)
        create_upload_folder(app.config['UPLOAD_FOLDER'])
        file.save(filepath)
        return filename
    return None

@app.after_request
def after_request(response):
    """Applies CORS headers to all responses."""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Sends the requested file from the upload directory."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/', methods=['GET'])
def index():
    """Displays the main admin page with entries."""
    entries = Entry.query.all()
    return render_template('admin/index.html', entries=entries)

@app.route('/create', methods=['POST'])
def create():
    """Creates a new entry and handles associated image upload."""
    try:
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
        db.session.flush()  # Ensures the ID is assigned without committing the transaction

        filename = handle_image(request.files['entryImage'], new_entry.id)
        if filename:
            new_entry.image_filename = filename

        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        current_app.logger.error(f"Failed to create entry: {e}")
        return jsonify({"error": "Failed to create entry"}), 500

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    """Updates an entry by ID, handling image uploads or deletions as necessary."""
    entry = Entry.query.get_or_404(id)
    if request.method == 'POST':
        if request.form['category'] not in Entry.CATEGORIES:
            return jsonify({"error": "Invalid category"}), 400
        
        # Handle image upload or removal
        file = request.files['entryImage']
        if file.filename:
            filename = handle_image(file, entry.id)
            if filename:
                entry.image_filename = filename
        elif 'remove_image' in request.form and entry.image_filename:
            image_path = path.join(app.config['UPLOAD_FOLDER'], entry.image_filename)
            if path.exists(image_path):
                remove(image_path)
            entry.image_filename = None

        # Update other fields
        entry.date = request.form['date']
        entry.category = request.form['category']
        entry.title = request.form['title']
        entry.description = request.form.get('description', None) or None

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('admin/update.html', entry=entry)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Deletes an entry by ID, including any associated image."""
    entry = Entry.query.get_or_404(id)
    if entry.image_filename:
        image_path = path.join(app.config['UPLOAD_FOLDER'], entry.image_filename)
        if path.exists(image_path):
            remove(image_path)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/timeline', methods=['GET'])
def timeline():
    """Generates a timeline view of entries, calculating positions based on dates."""
    timeline_height = request.args.get('timeline-height', default='calc(50vh - 20px)')[:15]
    entries = Entry.query.all()
    for entry in entries:
        entry.date = datetime.strptime(entry.date, '%Y-%m-%d')
    entries_sorted = sorted(entries, key=lambda x: x.date)
    today = datetime.combine(datetime.now().date(), time(0, 0))
    past_items_indices = [i for i, entry in enumerate(entries_sorted) if entry.date < today]
    second_to_last_past_index = past_items_indices[-2] if len(past_items_indices) > 1 else None
    return make_response(render_template('timeline/timeline.html', timeline_height=timeline_height, entries=entries_sorted, today=today, second_to_last_past_index=second_to_last_past_index))

@app.route('/api/data', methods=['GET'])
def api_data():
    """Returns a JSON response with data for all entries, including image URLs."""
    data = []
    for entry in Entry.query.all():
        image_url = url_for('uploaded_file', filename=entry.image_filename, _external=True) if entry.image_filename else None
        entry_data = {
            'date': entry.date,
            'category': entry.category,
            'title': entry.title,
            'description': entry.description,
            'image_url': image_url
        }
        data.append(entry_data)
    return jsonify(data)

@app.route('/update-birthdays', methods=['POST'])
def update_birthdays():
    """Updates all birthday entries to the current year."""
    current_year = datetime.now().year
    birthday_entries = Entry.query.filter_by(category='birthday').all()
    for entry in birthday_entries:
        entry.date = f"{current_year}-{entry.date.split('-')[1]}-{entry.date.split('-')[2]}"
    db.session.commit()
    return jsonify({"message": "All birthday entries have been updated to the current year"}), 200

@app.route('/purge-old-entries', methods=['POST'])
def purge_old_entries():
    """Deletes old entries that are not marked as birthdays and are past the current date."""
    current_date = datetime.now().date()
    old_entries = Entry.query.filter(Entry.date < str(current_date), Entry.category != 'birthday').all()
    for entry in old_entries:
        if entry.image_filename:
            image_path = path.join(app.config['UPLOAD_FOLDER'], entry.image_filename)
            if path.exists(image_path):
                remove(image_path)
        db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Old entries have been purged"}), 200

@app.route('/batch-import', methods=['POST'])
def batch_import():
    """Imports multiple entries from a JSON payload."""
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
