from dotenv import load_dotenv
import os

class Config:
    load_dotenv()  # This loads the env variables from .env file
    SQLALCHEMY_DATABASE_URI = 'sqlite:////app/data/data.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
    UPLOAD_FOLDER = '/app/data/uploads'  # Directory to save uploaded images
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    GRAFANA_API_TOKEN = os.getenv('GRAFANA_API_TOKEN')
    GRAFANA_TIMEZONE = os.getenv('GRAFANA_TIMEZONE', 'Europe/Berlin')

# for unittests
class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use an in-memory database for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF tokens in the form
