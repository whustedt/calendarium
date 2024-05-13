class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:////app/data/data.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = '/app/data/uploads'  # Directory to save uploaded images
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# for unittests
class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use an in-memory database for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF tokens in the form