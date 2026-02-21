from datetime import datetime, date
from flask import jsonify, url_for
from babel.dates import format_date
from os import path, makedirs
import zipfile
from io import BytesIO
from urllib.parse import urlparse, unquote_plus
import requests
from werkzeug.utils import secure_filename
from colorsys import rgb_to_hls, hls_to_rgb
from .models import Entry, Category
from sqlalchemy.orm import joinedload


def handle_image_upload(entry_id, file, giphy_url, upload_folder, allowed_extensions):
    """Handle Giphy URL or file upload."""
    if giphy_url:
        filename = download_giphy_image(giphy_url, entry_id, upload_folder)
    else:
        filename = handle_image(file, entry_id, upload_folder, allowed_extensions)

    return filename

def download_giphy_image(url, entry_id, upload_folder):
    """Download and save a Giphy image from a valid URL to the specified folder."""
    if not is_valid_giphy_url(url):
        return None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = f"{entry_id}.gif"
            filepath = path.join(upload_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filename
    except requests.RequestException:
        return None

def is_valid_giphy_url(url):
    """Check if a URL is a valid Giphy URL by its domain and path."""
    try:
        parsed_url = urlparse(url)
        return parsed_url.netloc.startswith("media") and parsed_url.netloc.endswith(".giphy.com") and parsed_url.path.startswith("/media/")
    except ValueError:
        return False

def handle_image(file, entry_id, upload_folder, allowed_extensions):
    """Handles image upload and saves it with a new filename based on entry ID."""
    if file and allowed_file(file.filename, allowed_extensions):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1]
        filename = f"{entry_id}.{ext}"
        filepath = path.join(upload_folder, filename)
        file.save(filepath)
        return filename
    return None

def parse_date(date_str):
    """Parses a date string formatted as 'YYYY-MM-DD' into a date object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None

def allowed_file(filename, allowed_extensions):
    """Checks if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def create_upload_folder(upload_folder):
    """Creates the upload folder if it doesn't exist."""
    if not path.exists(upload_folder):
        makedirs(upload_folder, exist_ok=True)

def calculate_display_date(entry_date, is_recurring, today):
    """Calculate the display date for an entry.
    
    For recurring events, returns the next occurrence (current or next year).
    For non-recurring events, returns the original date.
    
    Args:
        entry_date: date object of the original entry date
        is_recurring: boolean indicating if the event repeats annually
        today: date object for today's date
        
    Returns:
        date object for the display date
    """
    if not is_recurring:
        return entry_date
    
    # Handle leap year edge case (Feb 29) separately
    if entry_date.month == 2 and entry_date.day == 29:
        try:
            current_year_date = date(today.year, 2, 29)
        except ValueError:
            # Not a leap year, use Feb 28
            current_year_date = date(today.year, 2, 28)
        
        # If the date has already passed this year, use next year
        if current_year_date < today:
            next_year = today.year + 1
            try:
                return date(next_year, 2, 29)
            except ValueError:
                return date(next_year, 2, 28)
        return current_year_date
    
    # For regular recurring events, calculate the next occurrence
    current_year_date = entry_date.replace(year=today.year)
    
    # If the date has already passed this year, use next year
    if current_year_date < today:
        return entry_date.replace(year=today.year + 1)
    
    return current_year_date


def calculate_milestone_info(entry_date, display_date_obj, is_recurring):
    """Calculate milestone information for an entry.
    
    Args:
        entry_date: date object of the original entry date
        display_date_obj: date object of the display date
        is_recurring: boolean indicating if the event repeats annually
        
    Returns:
        dict with 'years_since', 'milestone_year', and 'is_milestone' keys
    """
    years_since = None
    milestone_year = None
    is_milestone = False
    
    if is_recurring and entry_date.year > 1:  # Year 0001 means "year unknown"
        years_since = display_date_obj.year - entry_date.year
        
        if years_since % 5 == 0 or years_since == 1:
            is_milestone = True
            milestone_year = years_since
    
    return {
        'years_since': years_since,
        'milestone_year': milestone_year,
        'is_milestone': is_milestone
    }


def get_entry_data(db, category_filter=None, max_past_entries=None, sort_order='display_date'):
    """Returns formatted entries and categories data with complete category details for each entry.
    
    If max_past_entries is provided, only the most recent past entries up to that count will be included.
    For recurring events, calculates display_date based on current/next year occurrence.

    sort_order values:
      - 'display_date' (default): timeline-oriented display date sorting with past/future pivot
      - 'created_desc': preserve DB order by newest created entry first
    """
    # Parse the category_filter if provided
    filter_categories = category_filter.split(',') if category_filter else None

    # Preload categories to avoid N+1 query issues
    query = db.session.query(Entry).options(joinedload(Entry.category))

    if sort_order == 'created_desc':
        query = query.order_by(Entry.id.desc())
    else:
        query = query.order_by(Entry.date)
    
    if filter_categories:
        # Filter entries based on the category names
        query = query.join(Category).filter(Category.name.in_(filter_categories))
    
    entries = query.all()
    categories = db.session.query(Category).all()

    today = date.today()
    today_str = str(today)
    
    # Calculate display dates for all entries and sort by display date
    entries_with_display = []
    for entry in entries:
        entry_date = parse_date(entry.date)
        if entry_date:
            display_date_obj = calculate_display_date(entry_date, entry.category.repeat_annually, today)
            milestone_info = calculate_milestone_info(entry_date, display_date_obj, entry.category.repeat_annually)
            entries_with_display.append((entry, entry_date, display_date_obj, milestone_info))
    
    if sort_order == 'created_desc':
        filtered_entries = entries_with_display
        filtered_pivot = 0
    else:
        # Sort by display date
        entries_with_display.sort(key=lambda x: x[2])

        # Determine the pivot: the first upcoming or current entry (based on display date)
        pivot = next((i for i, (entry, entry_date, display_date_obj, milestone_info) in enumerate(entries_with_display)
                    if str(display_date_obj) >= today_str), len(entries_with_display))

        # Split past and upcoming entries. Limit past entries if max_past_entries is provided.
        past_entries = entries_with_display[:pivot]
        future_entries = entries_with_display[pivot:]
        if max_past_entries is not None:
            past_entries = past_entries[-max_past_entries:]
        filtered_entries = past_entries + future_entries
        # The pivot for the filtered list is now the count of past entries kept
        filtered_pivot = len(past_entries)
    
    formatted_entries = []
    for i, (entry, entry_date, display_date_obj, milestone_info) in enumerate(filtered_entries):
        formatted_entry = {
            "id": entry.id,
            "date": entry.date,
            "display_date": str(display_date_obj),
            "display_date_formatted": format_date(display_date_obj, 'd. MMMM', locale='de_DE'),
            "date_formatted": format_date(entry_date, 'd. MMMM', locale='de_DE'),
            "title": entry.title,
            "description": entry.description,
            "category": {
                "id": entry.category.id,
                "name": entry.category.name,
                "symbol": entry.category.symbol,
                "color_hex": entry.category.color_hex,
                "color_hex_variation": adjust_lightness(entry.category.color_hex),
                "repeat_annually": entry.category.repeat_annually,
                "display_celebration": entry.category.display_celebration,
                "is_protected": entry.category.is_protected,
                "last_updated_by": entry.category.last_updated_by
            },
            "url": entry.url,
            "image_url": url_for('uploaded_file', filename=entry.image_filename) if entry.image_filename else None,
            "image_url_external": url_for('uploaded_file', filename=entry.image_filename, _external=True) if entry.image_filename else None,
            "index": i - filtered_pivot,
            "is_today": str(display_date_obj) == today_str,
            "cancelled": entry.cancelled,
            "last_updated_by": entry.last_updated_by,
            "years_since": milestone_info['years_since'],
            "milestone_year": milestone_info['milestone_year'],
            "is_milestone": milestone_info['is_milestone']
        }
        formatted_entries.append(formatted_entry)
    
    formatted_categories = [{
        "id": category.id,
        "name": category.name,
        "symbol": category.symbol,
        "color_hex": category.color_hex,
        "color_hex_variation": adjust_lightness(category.color_hex),
        "repeat_annually": category.repeat_annually,
        "display_celebration": category.display_celebration,
        "is_protected": category.is_protected,
        "last_updated_by": category.last_updated_by
    } for category in categories]

    return {"entries": formatted_entries, "categories": formatted_categories}
    
def create_zip(data, upload_folder, db_uri):
    """Creates a zip file containing entries data, associated images, and the database file."""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Add entries.json file
        entries_json = jsonify(data).get_data(as_text=True)
        zip_file.writestr('data.json', entries_json)
        
        # Add image files
        for entry in data.get('entries'):
            if entry['image_url']:
                image_filename = entry['image_url'].split('/')[-1]
                image_path = path.join(upload_folder, image_filename)
                if path.exists(image_path):
                    zip_file.write(image_path, arcname=image_filename)

        # Add the database file if the URI points to a SQLite database
        if db_uri.startswith("sqlite:///"):
            db_path = unquote_plus(db_uri[10:])  # Strip 'sqlite:///' and decode URI encoding
            if path.exists(db_path):
                zip_file.write(db_path, arcname='data.db')

    zip_buffer.seek(0)
    return zip_buffer

def hex_to_rgb(value):
    """Convert hex to RGB"""
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb_to_hex(rgb):
    """Convert RGB to hex"""
    return '#%02x%02x%02x' % rgb

def adjust_lightness(color, adjustment_factor=0.9):
    """Adjust the lightness of the color"""
    r, g, b = hex_to_rgb(color)
    h, l, s = rgb_to_hls(r/255., g/255., b/255.)
    l = max(0, min(1, l * adjustment_factor))  # Ensure lightness stays within 0 to 1
    r, g, b = hls_to_rgb(h, l, s)
    return rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))
