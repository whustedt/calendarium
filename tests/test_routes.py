from app.models import Entry, Category
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import not_
import json

def test_home_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"Cake" in response.data

def test_create_entry_with_valid_data(test_client, init_database):
    category = db.session.query(Category).filter_by(name="Release").first()
    data = {
        'date': "2021-06-01",
        'category': category.name,
        'title': "New Product Launch",
        'description': "Launching the new product"
    }

    response = test_client.post('/create', data=data, follow_redirects=True)
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.data.decode('utf-8')}"
    assert db.session.query(Entry).count() == 2  # Assuming one entry was already in the database from setup

def test_update_entry(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/update/<id>' page is posted to (POST) with updated data
    THEN check the response is valid and the entry is updated correctly
    """
    response = test_client.post('/update/1', data={
        'date': "2021-06-01",
        'category': "Birthday",
        'title': "Updated Title",
        'description': "Updated description"
    }, follow_redirects=True)
    assert response.status_code == 200
    entry = db.session.get(Entry, 1)
    assert entry.title == "Updated Title"

def test_delete_entry(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/delete/<id>' endpoint is called (POST)
    THEN check that the entry is removed from the database
    """
    initial_count = db.session.query(Entry).count()
    response = test_client.post('/delete/1', follow_redirects=True)
    assert response.status_code == 200
    assert db.session.query(Entry).count() == initial_count - 1

def test_timeline_view(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/timeline' page is requested (GET)
    THEN check the response is valid and potentially some data is returned
    """
    response = test_client.get('/timeline')
    assert response.status_code == 200
    # Additional assertions can check specific content or data structures1

def test_create_entry_with_invalid_data(test_client):
    """
    GIVEN a Flask application
    WHEN an attempt is made to create an entry with invalid data
    THEN check that the application responds with an appropriate error message
    """
    # Test case 1: Invalid category
    data = {
        'date': "2021-06-01",
        'category': "invalid_category",
        'title': "Invalid Category Test",
        'description': "This should fail"
    }
    response = test_client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 400
    assert b"Invalid category" in response.data

    # Test case 2: Invalid date format
    data = {
        'date': "06-01-2021",
        'category': "Release",
        'title': "Invalid Date Format Test",
        'description': "This should also fail"
    }
    response = test_client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 400
    assert b"Invalid date format" in response.data
        
def test_api_data(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN the '/api/data' endpoint is requested (GET)
    THEN check that the response is a valid JSON with expected data
    """
    response = test_client.get('/api/data')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2  # categories and entries
    entry = data.get('entries')[0]
    assert entry['date'] == "2021-05-20"
    assert entry['category']['name'] == "Birthday"
    assert entry['title'] == "John's Birthday"
    assert entry['description'] == "Birthday party"

def test_batch_import(test_client, init_database):
    # Data should include categories and entries
    data = {
        'categories': [
            {'name': "Webinar", 'symbol': "🌐", 'color_hex': "#008000"}
        ],
        'entries': [
            {'date': "2021-07-01", 'category': {'name': "Webinar"}, 'title': "Online Event"}
        ]
    }
    response = test_client.post('/batch-import', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert db.session.query(Entry).count() == 2  # Assuming one existing entry
    assert db.session.query(Category).count() == 5 # Including existing categories

def test_update_serial_entries(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN the '/update-serial-entries' endpoint is called (POST)
    THEN check that all serial entries are updated to the current year
    """
    # Create a new birthday entry with a different year
    old_year = 2020
    category = db.session.query(Category).filter_by(name="Birthday").first()
    entry = Entry(date=f"{old_year}-05-20", category=category, title="Another Birthday", description="Test birthday")
    db.session.add(entry)
    db.session.commit()

    response = test_client.post('/update-serial-entries', follow_redirects=True)
    assert response.status_code == 200

    current_year = datetime.now().year
    birthday_entries = db.session.query(Entry).filter_by(category=category).all()
    for entry in birthday_entries:
        assert str(current_year) in entry.date

def test_purge_old_entries(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN the '/purge-old-entries' endpoint is called (POST)
    THEN check that old non-birthday entries are deleted from the database
    """
    # Create an old non-birthday entry
    category = db.session.query(Category).filter_by(name="Release").first()
    old_date = date.today() - timedelta(days=365)  # One year ago
    entry = Entry(date=str(old_date), category=category, title="Old Entry", description="This should be purged")
    db.session.add(entry)
    db.session.commit()

    response = test_client.post('/purge-old-entries', follow_redirects=True)
    assert response.status_code == 200

    old_entries = db.session.query(Entry).join(Entry.category).filter(
        Entry.date < str(date.today()), 
        not_(Category.is_protected)
    ).all()
    
    assert len(old_entries) == 0

def test_entries_sorted_by_date(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN entries are retrieved from the database
    THEN check that the entries are sorted by date in ascending order
    """
    # Create some entries with different dates
    category1 = db.session.query(Category).filter_by(name="Cake").first()
    category2 = db.session.query(Category).filter_by(name="Release").first()
    category3 = db.session.query(Category).filter_by(name="Birthday").first()
    entry1 = Entry(date=str(date.today()), category=category1, title="Today's Entry")
    entry2 = Entry(date=str(date.today() - timedelta(days=7)), category=category2, title="Last Week's Entry")
    entry3 = Entry(date=str(date.today() + timedelta(days=3)), category=category3, title="Future Entry")
    db.session.add_all([entry1, entry2, entry3])
    db.session.commit()

    response = test_client.get('/api/data')
    assert response.status_code == 200
    data = json.loads(response.data)
    dates = [entry['date'] for entry in data['entries']]
    assert dates == sorted(dates)