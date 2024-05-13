import pytest
from app import create_app, db
from app.config import TestConfig
from app.models import Entry

@pytest.fixture(scope='module')
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

@pytest.fixture(scope='module')
def init_database():
    # Populate the database with a single entry before each test
    entry = Entry(date="2021-05-20", category="birthday", title="John's Birthday", description="Birthday party")
    db.session.add(entry)
    db.session.commit()

    yield  # This yields control back to the test function

    # Cleanup: Empty the database after tests
    db.session.query(Entry).delete()
    db.session.commit()