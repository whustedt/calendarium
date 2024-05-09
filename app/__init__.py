from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from flask_babel import Babel
from babel.dates import format_date
import time
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////app/data/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/app/data/uploads'  # Directory to save uploaded images
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)
babel = Babel(app)

# Add format_date as a filter
app.jinja_env.filters['format_date'] = format_date

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def create_upload_folder(upload_folder):
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

# Import models to ensure they are known to SQLAlchemy
from app import models

def create_tables_with_retry(db, retries=5, delay=5):
    """
    Attempts to create all tables with retries if it encounters an operational error.
    :param db: The SQLAlchemy database instance.
    :param retries: Maximum number of retries.
    :param delay: Delay between retries in seconds.
    """
    attempt = 0
    while attempt < retries:
        try:
            with app.app_context():
                db.create_all()
            print("Database tables created successfully.")
            break
        except OperationalError as e:
            attempt += 1
            if attempt < retries:
                print(f"Attempt {attempt} failed with error: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"All attempts failed. Final failure with error: {e}.")
                raise

# Call the retry logic during app initialization
create_tables_with_retry(db)

# Import routes
from . import routes
