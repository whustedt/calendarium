from flask import request, jsonify, render_template, redirect, url_for, make_response, send_from_directory, current_app, send_file, abort
import requests
from .models import Entry
from app import db
from datetime import datetime
from .helpers import handle_image_upload, parse_date, get_formatted_entries, create_zip
import os
import validators

def init_app(app):
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
                'limit': 5
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
        url = f"https://api.giphy.com/v1/gifs/search?api_key={os.getenv('GIPHY_API_TOKEN')}&q={query}&limit=10"
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
        """Display the main admin page with entries."""
        entries = db.session.query(Entry).order_by(Entry.date).all()
        return render_template('admin/index.html', entries=entries)

    @app.route('/create', methods=['POST'])
    def create():
        """Create a new entry and handle associated image upload."""
        try:
            # Validate category and date first
            if request.form['category'] not in Entry.CATEGORIES:
                return jsonify({"error": "Invalid category"}), 400
            if not parse_date(request.form['date']):
                return jsonify({"error": "Invalid date format, must be YYYY-MM-DD"}), 400
            if request.form.get('url') and not validators.url(request.form.get('url')):
                return jsonify({"error": "Invalid URL"}), 400

            new_entry = Entry(
                date = request.form['date'],
                category = request.form['category'],
                title = request.form['title'],
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
            # Validate category and date first
            if request.form['category'] not in Entry.CATEGORIES:
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

            # Update other fields
            entry.date = request.form['date']
            entry.category = request.form['category']
            entry.title = request.form['title']
            entry.description = request.form.get('description')
            entry.url = request.form.get('url')
            entry.last_updated_by = request.remote_addr
            db.session.commit()
            return redirect(url_for('index'))

        return render_template('admin/update.html', entry=entry)

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
            entry = db.session.query(Entry).get(id)
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
        """Generate a timeline view of entries, calculating positions based on dates."""
        timeline_height = request.args.get('timeline-height', default='calc(50vh - 20px)')[:25]
        font_family = request.args.get('font-family', default='sans-serif')[:35]
        font_scale = request.args.get('font-scale', default='1')[:5]
        entries = get_formatted_entries(db.session.query(Entry).order_by(Entry.date).all())
        return make_response(render_template('timeline/timeline.html', entries=entries, timeline_height=timeline_height, font_family=font_family, font_scale=font_scale))
    
    @app.route('/api/data', methods=['GET'])
    def api_data():
        """Return a JSON response with data for all entries, including image URLs.""" 
        return jsonify(get_formatted_entries(db.session.query(Entry).order_by(Entry.date).all()))
    
    @app.route('/update-birthdays', methods=['POST'])
    def update_birthdays():
        """Update all birthday entries to the current year."""
        current_year = datetime.now().year
        birthday_entries = db.session.query(Entry).filter_by(category='birthday').all()
        for entry in birthday_entries:
            entry.date = f"{current_year}-{entry.date.split('-')[1]}-{entry.date.split('-')[2]}"
        db.session.commit()
        return jsonify({"message": "All birthday entries have been updated to the current year"}), 200
    
    @app.route('/purge-old-entries', methods=['POST'])
    def purge_old_entries():
        """Delete old entries that are not marked as birthdays and are past the current date."""
        current_date = datetime.now().date()
        old_entries = db.session.query(Entry).filter(Entry.date < str(current_date), Entry.category != 'birthday').all()
        for entry in old_entries:
            if entry.image_filename:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], entry.image_filename)
                if os.path.exists(image_path):
                    os.remove(image_path)
            db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": "Old entries have been purged"}), 200
    
    @app.route('/batch-import', methods=['POST'])
    def batch_import():
        """Import multiple entries from a JSON payload."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
    
        for item in data:
            if 'category' not in item or item['category'] not in Entry.CATEGORIES:
                return jsonify({"error": f"Invalid category in data: {item.get('category', 'None')}"}), 400
            if not parse_date(item['date']):
                return jsonify({"error": f"Invalid date format for {item.get('date', 'None')}, must be YYYY-MM-DD"}), 400 
            if item.get('url') and not validators.url(item['url']):
                return jsonify({"error": f"Invalid URL in data: {item.get('url')}"}), 400
            
            try:
                new_entry = Entry(
                    date=item['date'],
                    category=item['category'],
                    title=item['title'],
                    description=item.get('description', None),
                    url = item.get('url', None),
                    cancelled = item.get('cancelled', False)
                )
                db.session.add(new_entry)
            except KeyError as e:
                return jsonify({"error": f"Missing key in data: {e}"}), 400
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
        db.session.commit()
        return jsonify({"message": "Entries successfully imported"}), 201
    
    @app.route('/export-data', methods=['GET'])
    def export_data():
        """Export all entries and associated images as a zip file."""
        entries = get_formatted_entries(db.session.query(Entry).order_by(Entry.date).all())
        zip_buffer = create_zip(entries, app.config['UPLOAD_FOLDER'])
        
        response = make_response(send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='data_export.zip'))
        response.headers['Content-Disposition'] = 'attachment; filename=data_export.zip'
        return response
