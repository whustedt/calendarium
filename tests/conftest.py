import pytest
from app import create_app, db
from app.config import TestConfig
from app.models import Entry, Category
from unittest import mock

@pytest.fixture(scope='function')
def test_client():
    # Create a Flask app instance with test configurations
    flask_app = create_app(TestConfig)
    
    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            db.create_all()  # Setup the database schema
            yield testing_client  # This is where the testing happens
            db.session.remove()
            db.drop_all()

@pytest.fixture(scope='function')
def init_database():
    # Creating necessary categories
    category1 = db.session.query(Category).filter_by(name="Birthday").first()
    if not category1:
        category1 = Category(name="Birthday", symbol="🥳", color_hex="#FFD700", repeat_annually=True, display_celebration=True, is_protected=True)
        db.session.add(category1)
        db.session.commit()
    
    category2 = db.session.query(Category).filter_by(name="Release").first()
    if not category2:
        category2 = Category(name="Release", symbol="🚀", color_hex="#FF6347", repeat_annually=False, display_celebration=False, is_protected=False)
        db.session.add(category2)
        db.session.commit()

    # Populate the database with a single entry
    entry = Entry(date="2021-05-20", category_id=category1.id, title="John's Birthday", description="Birthday party")
    db.session.add(entry)
    db.session.commit()

    yield  # This yields control back to the test function

    # Cleanup: Empty the database after tests
    db.session.query(Entry).delete()
    db.session.query(Category).delete()
    db.session.commit()

@pytest.fixture
def mock_file():
    mock_file = mock.Mock()
    mock_file.filename = 'test.jpg'
    return mock_file

@pytest.fixture
def mock_requests_get():
    with mock.patch('requests.get') as mock_get:
        yield mock_get

def test_search_gifs(test_client, mock_requests_get):
    # Setup mock
    mock_requests_get.return_value.json.return_value = {'data': 'mock data'}

    response = test_client.get('/search_gifs?q=cats')
    assert response.status_code == 200
    assert b'mock data' in response.data