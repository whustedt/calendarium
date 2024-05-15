from flask import request, jsonify, render_template, redirect, url_for, make_response, send_from_directory, current_app
from .models import Entry
from app import db
from datetime import datetime, date, time
from babel.dates import format_date
from os import path, remove, makedirs
    
def init_app(app):
    def handle_image(file, entry_id):
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1]
            filename = f"{entry_id}.{ext}"
            filepath = path.join(app.config['UPLOAD_FOLDER'], filename)
            create_upload_folder(app.config['UPLOAD_FOLDER'])
            file.save(filepath)
            return filename
        return None
    
    def parse_date(date_str):
        """Parses a date string formatted as 'YYYY-MM-DD' into a datetime.date object."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    def create_upload_folder(upload_folder):
        if not path.exists(upload_folder):
            makedirs(upload_folder) 
    
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
        entries = Entry.query.order_by(Entry.date).all()
        return render_template('admin/index.html', entries=entries)
        
    @app.route('/create', methods=['POST'])
    def create():
        """Creates a new entry and handles associated image upload."""
        try:
            category = request.form['category']
            if category not in Entry.CATEGORIES:
                return jsonify({"error": "Invalid category"}), 400
    
            if not parse_date(request.form['date']):
                return jsonify({"error": "Invalid date format, must be YYYY-MM-DD"}), 400
     
            new_entry = Entry(
                date=request.form['date'],
                category=category,
                title=request.form['title'],
                description=request.form.get('description', None) or None
            )
            db.session.add(new_entry)
            db.session.flush()  # Ensures the ID is assigned without committing the transaction
    
            filename = handle_image(request.files.get('entryImage'), new_entry.id)
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
            
            if not parse_date(request.form['date']):
                return jsonify({"error": "Invalid date format, must be YYYY-MM-DD"}), 400
            
            # Handle image upload or removal
            file = request.files.get('entryImage')
            if file and file.filename:
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
    
    def get_formatted_entries():
        """Fetches and formats entries from the database."""
        today = str(date.today()) # like 2024-05-10
        entries = Entry.query.order_by(Entry.date).all()
        data = []
        index = next((i for i, entry in enumerate(entries) if entry.date >= today), len(entries))
    
        for i, entry in enumerate(entries):
            entry_data = {
                'date': entry.date,
                'date_formatted': format_date(parse_date(entry.date), 'd. MMMM', locale='de_DE'),
                'category': entry.category,
                'title': entry.title,
                'description': entry.description,
                'image_url': url_for('uploaded_file', filename=entry.image_filename) if entry.image_filename else None,
                'image_url_external': url_for('uploaded_file', filename=entry.image_filename, _external=True) if entry.image_filename else None,
                'index': i - index,
                'isToday': entry.date == today
            }
            data.append(entry_data)
    
        return data
    
    @app.route('/timeline', methods=['GET'])
    def timeline():
        """Generates a timeline view of entries, calculating positions based on dates."""
        timeline_height = request.args.get('timeline-height', default='calc(50vh - 20px)')[:25]
        font_family = request.args.get('font-family', default='sans-serif')[:35]
        font_scale = request.args.get('font-scale', default='1')[:5]
        entries = get_formatted_entries()
        return make_response(render_template('timeline/timeline.html', entries=entries, timeline_height=timeline_height, font_family=font_family, font_scale=font_scale))
    
    @app.route('/api/data', methods=['GET'])
    def api_data():
        """Returns a JSON response with data for all entries, including image URLs.""" 
        return jsonify(get_formatted_entries())
    
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
            if not parse_date(item['date']):
                return jsonify({"error": f"Invalid date format for {item.get('date', 'None')}, must be YYYY-MM-DD"}), 400 
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
