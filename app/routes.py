from flask import request, jsonify, render_template, redirect, url_for, make_response, send_from_directory, current_app, abort
import requests
from .models import Entry, Category
from app import db
from datetime import datetime
from .helpers import handle_image_upload, parse_date, get_entry_data, create_zip
import os
import validators

def init_app(app, scheduler):
    @app.after_request
    def after_request(response):
        """Apply CORS headers to all responses."""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        return response
    
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """Send the requested file from the upload directory."""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    @app.route('/favicon.ico')
    def favicon():
        """Send the favicon."""
        return send_from_directory(os.path.join(app.root_path, 'static/favicon'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route('/search_gifs', methods=['GET'])
    def search_gifs():
        """
        Fetches GIFs from the Giphy API based on a user's search query. This endpoint
        directly interacts with the Giphy API from the backend server using an API key
        stored in environment variables, providing a secure method to handle sensitive API keys.
        
        The function queries the Giphy API for GIFs matching the provided search term,
        limits the number of results, and returns them in JSON format.
        
        Args:
            None directly. Utilizes query parameters from the request.
        
        Query Parameters:
            q (str): The search query string input by the user.
        
        Returns:
            json: A JSON response containing an array of GIFs from Giphy if a query is provided.
                If no query is provided, it returns an empty JSON array.
        
        Examples:
            Request: GET /search_gifs?q=cats
            Response: JSON array with GIFs information related to 'cats'.
            
            If no query is provided:
            Request: GET /search_gifs
            Response: []
        """
        query = request.args.get('q')
        if not query:
            return jsonify([])  # Return empty array if no query
        response = requests.get(
            'https://api.giphy.com/v1/gifs/search',
            params={
                'api_key': os.getenv('GIPHY_API_TOKEN'),
                'q': query,
                'limit': 15
            }
        )
        return jsonify(response.json()['data'])

    @app.route('/get-giphy-url')
    def get_giphy_url():
        """
        Generates a full request URL for Giphy's search API including the API key and returns it to the client.

        This endpoint acts as a secure means to provide the Giphy API request URL to the frontend without exposing
        the API key directly in the client-side code. It takes a search query as a parameter, constructs the URL
        for Giphy's API, and returns this URL securely encapsulated in a JSON response.

        Returns:
            json: A JSON object containing the full URL to access Giphy's search API or an error message if the
            query parameter is missing.

        Example:
            Request: GET /get-giphy-url?q=cats
            Response: {"url": "https://api.giphy.com/v1/gifs/search?api_key=your_giphy_api_key&q=cats&limit=10"}
        """
        query = request.args.get('q')
        if not query:
            return jsonify(error="Query is required"), 400
        url = f"https://api.giphy.com/v1/gifs/search?api_key={os.getenv('GIPHY_API_TOKEN')}&q={query}&limit=15"
        return jsonify(url=url)

    @app.route('/check-giphy-enabled')
    def check_giphy_enabled():
        """
        Checks if GIPHY integration is enabled by verifying the presence of the GIPHY API token in the environment variables.

        This endpoint is useful for front-end applications to conditionally enable or disable features that require GIPHY integration, 
        based on the availability of the API token.
    
        Returns:
            json: A JSON object with a boolean 'enabled' key that indicates whether the GIPHY API token is available.
        """
        # Check if the 'GIPHY_API_TOKEN' environment variable is set and not empty
        is_enabled = 'GIPHY_API_TOKEN' in os.environ and bool(os.getenv('GIPHY_API_TOKEN'))

        return jsonify(enabled=is_enabled)

    @app.route('/', methods=['GET'])
    def index():
        """Display the main admin page."""
        data = get_entry_data(db)
        return render_template('admin/index.html', entries=data['entries'], categories=data['categories'])

    @app.route('/create', methods=['POST'])
    def create():
        """Create a new entry and handle associated image upload."""
        try:
            date_str = request.form.get('date', '').strip()
            title = request.form.get('title', '').strip()
            category_name = request.form.get('category', '').strip()
            
            errors = []
            if not date_str:
                errors.append("Date is required")
            if not title:
                errors.append("Title is required")
            if not category_name:
                errors.append("Category is required")
            
            if errors:
                return jsonify({"errors": errors}), 400
                
            category = db.session.query(Category).filter_by(name=category_name).first()
            if not category:
                return jsonify({"error": "Invalid category"}), 400
            if not parse_date(date_str):
                return jsonify({"error": "Invalid date format, must be YYYY-MM-DD"}), 400
            if request.form.get('url') and not validators.url(request.form.get('url')):
                return jsonify({"error": "Invalid URL"}), 400

            new_entry = Entry(
                date = date_str,
                category_id = category.id,  # use the ID of the category
                title = title,
                description = request.form.get('description'),
                url = request.form.get('url'),
                last_updated_by = request.remote_addr
            )
            db.session.add(new_entry)
            db.session.flush()  # Ensure the ID is assigned without committing the transaction

            filename = handle_image_upload(new_entry.id, request.files.get('entryImage'), request.form.get('giphyUrl'), app.config['UPLOAD_FOLDER'], app.config['ALLOWED_EXTENSIONS'])
            if filename:
                new_entry.image_filename = filename

            db.session.commit()
            return redirect(url_for('index'))

        except Exception as e:
            current_app.logger.error(f"Failed to create entry: {e}")
            return jsonify({"error": "Failed to create entry"}), 500

    @app.route('/update/<int:id>', methods=['GET', 'POST'])
    def update(id):
        """Update an entry by ID, handling image uploads or deletions as necessary."""
        entry = db.session.get(Entry, id)
        if not entry:
            abort(404)

        if request.method == 'POST':
            category_name = request.form['category']
            category = db.session.query(Category).filter_by(name=category_name).first()
            if not category:
                return jsonify({"error": "Invalid category"}), 400
            if not parse_date(request.form['date']):
                return jsonify({"error": "Invalid date format, must be YYYY-MM-DD"}), 400
            if request.form.get('url') and not validators.url(request.form.get('url')):
                return jsonify({"error": "Invalid URL"}), 400
            
            giphy_url = request.form.get('giphyUrl')
            file = request.files.get('entryImage')

            # Remove current image if applicable
            if 'remove_image' in request.form or giphy_url or file:
                if entry.image_filename:
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], entry.image_filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                    entry.image_filename = None

            filename = handle_image_upload(entry.id, file, giphy_url, app.config['UPLOAD_FOLDER'], app.config['ALLOWED_EXTENSIONS'])
            if filename:
                entry.image_filename = filename

            # Update the entry with the new category ID and other fields
            entry.category_id = category.id
            entry.date = request.form['date']
            entry.title = request.form['title']
            entry.description = request.form.get('description')
            entry.url = request.form.get('url')
            entry.last_updated_by = request.remote_addr
            db.session.commit()
            return redirect(url_for('index'))

        return render_template('admin/update.html', entry=entry, categories=get_entry_data(db)['categories'])

    @app.route('/delete/<int:id>', methods=['POST'])
    def delete(id):
        """Delete an entry by ID, including any associated image."""
        entry = db.session.get(Entry, id)
        if entry is None:
            abort(404)
        if entry.image_filename:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], entry.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        db.session.delete(entry)
        db.session.commit()
        return redirect(url_for('index'))
    
    @app.route('/toggle_cancelled/<int:id>', methods=['POST'])
    def toggle_cancelled(id):
        """Toggle the cancelled state of an entry."""
        try:
            entry = db.session.get(Entry, id)
            if entry is None:
                return jsonify({"error": "Entry not found"}), 404
    
            # Toggle the cancelled state
            entry.cancelled = not entry.cancelled
            db.session.commit()
    
            return redirect(url_for('index'))
        except Exception as e:
            current_app.logger.error(f"Error toggling the cancelled state of the entry: {e}")
            return jsonify({"error": "Failed to update entry"}), 500

    @app.route('/timeline', methods=['GET'])
    def timeline():
        """Generate a timeline view of entries, calculating positions based on dates.
        
        Accepts the following query parameters:
          - timeline-height: CSS height value for the timeline.
          - font-family: CSS font-family value.
          - font-scale: Scale factor for font sizes.
          - categories: Comma-separated list of category names to filter entries.
          - max-past-entries: Maximum number of past entries to include.
        """
        timeline_height = request.args.get('timeline-height', default='calc(50vh - 20px)')[:25]
        font_family = request.args.get('font-family', default='sans-serif')[:35]
        font_scale = request.args.get('font-scale', default='1')[:5]
        category_filter = request.args.get('categories')
        max_past_entries = request.args.get('max-past-entries', default=None, type=int)
        
        data = get_entry_data(db, category_filter, max_past_entries)
        display_celebration = any(entry.get('is_today') and entry.get('category').get('display_celebration')
                                   for entry in data.get('entries'))
        
        return make_response(render_template('timeline/timeline.html', 
                                             entries=data.get('entries'), 
                                             categories=data.get('categories'),
                                             display_celebration=display_celebration,
                                             timeline_height=timeline_height, 
                                             font_family=font_family, 
                                             font_scale=font_scale))
    
    @app.route('/api/data', methods=['GET'])
    def api_data():
        """Return a JSON response with data for all data, including image URLs.""" 
        return jsonify(get_entry_data(db))
    
    @scheduler.task('cron', id='update_serial_entries', month=1, day=1, hour=3, minute=0)
    @app.route('/update-serial-entries', methods=['POST'])
    def update_serial_entries():
        """Update all serial entries to the current year for categories that repeat annually."""
        with scheduler.app.app_context():
            current_year = datetime.now().year
            serial_categories = db.session.query(Category).filter_by(repeat_annually=True).all()
            category_ids = [category.id for category in serial_categories]
        
            serial_entries = db.session.query(Entry).filter(Entry.category_id.in_(category_ids)).all()
            for entry in serial_entries:
                entry.date = f"{current_year}-{entry.date.split('-')[1]}-{entry.date.split('-')[2]}"
            db.session.commit()
            scheduler.app.logger.info("All serial entries have been updated to the current year")
            return jsonify({"message": "All serial entries have been updated to the current year"}), 200

    @scheduler.task('cron', id='purge_old_entries', month='*', day=1, hour=5, minute=0)
    @app.route('/purge-old-entries', methods=['POST'])
    def purge_old_entries():
        """Delete old entries that are linked to categories that are not protected and are past the current date."""
        with scheduler.app.app_context():
            current_date = datetime.now().date()
            unprotected_categories = db.session.query(Category).filter_by(is_protected=False).all()
            category_ids = [category.id for category in unprotected_categories]
            
            # Only purge entries that are both:
            # 1. From unprotected categories
            # 2. Have dates in the past
            old_entries = db.session.query(Entry).filter(
                Entry.category_id.in_(category_ids),
                Entry.date < str(current_date)
            ).all()
            for entry in old_entries:
                if entry.image_filename:
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], entry.image_filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                db.session.delete(entry)
            db.session.commit()
            scheduler.app.logger.info("Old entries have been purged")
            return jsonify({"message": "Old entries have been purged"}), 200
