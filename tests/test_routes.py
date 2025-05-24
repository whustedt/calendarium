from app.helpers import get_entry_data
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

def test_create_entry_with_empty_fields(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN an attempt is made to create an entry with empty required fields
    THEN check that appropriate error messages are returned
    """
    data = {
        'date': "",  # Empty date
        'category': "Birthday",
        'title': "",  # Empty title
        'description': "Test description"
    }
    response = test_client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 400
    assert b"Date is required" in response.data
    assert b"Title is required" in response.data

def test_create_entry_with_future_date(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN an entry is created with a future date
    THEN check that the entry is created successfully
    """
    category = db.session.query(Category).filter_by(name="Release").first()
    future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    data = {
        'date': future_date,
        'category': category.name,
        'title': "Future Release",
        'description': "This is a future event"
    }
    
    response = test_client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # Verify the entry was created
    entry = db.session.query(Entry).filter_by(title="Future Release").first()
    assert entry is not None
    assert str(entry.date) == future_date

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

def test_update_nonexistent_entry(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN an attempt is made to update a non-existent entry
    THEN check that a 404 error is returned
    """
    response = test_client.post('/update/999999', data={
        'date': "2021-06-01",
        'category': "Birthday",
        'title': "Updated Title",
        'description': "Updated description"
    }, follow_redirects=True)
    assert response.status_code == 404

def test_concurrent_entry_updates(test_client, init_database):
    """
    GIVEN a Flask application with an existing entry
    WHEN multiple updates are attempted concurrently
    THEN check that the last update is preserved
    """
    # Get the first entry
    entry = db.session.query(Entry).first()
    entry_id = entry.id

    # Simulate concurrent updates
    update_data_1 = {
        'date': "2021-06-01",
        'category': "Birthday",
        'title': "Update 1",
        'description': "First update"
    }
    update_data_2 = {
        'date': "2021-06-01",
        'category': "Birthday",
        'title': "Update 2",
        'description': "Second update"
    }

    response1 = test_client.post(f'/update/{entry_id}', data=update_data_1)
    response2 = test_client.post(f'/update/{entry_id}', data=update_data_2)

    assert response1.status_code == 302  # Redirect after success
    assert response2.status_code == 302

    # Verify final state
    updated_entry = db.session.get(Entry, entry_id)
    assert updated_entry.title == "Update 2"
    assert updated_entry.description == "Second update"

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

def test_delete_nonexistent_entry(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN an attempt is made to delete a non-existent entry
    THEN check that a 404 error is returned
    """
    response = test_client.post('/delete/999999', follow_redirects=True)
    assert response.status_code == 404

def test_timeline_view(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/timeline' page is requested (GET)
    THEN check the response is valid and potentially some data is returned
    """
    response = test_client.get('/timeline')
    assert response.status_code == 200
    # Additional assertions can check specific content or data structures1

def test_timeline_view_with_category_filter(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/timeline' page is requested (GET) with a category filter
    THEN check the response is valid and only entries from specified categories are returned
    """
    # Add another category and entry to test filtering
    category = db.session.query(Category).filter_by(name="Release").first()
    if not category:
        category = Category(name="Release", symbol="🚀", color_hex="#FF6347", repeat_annually=False, display_celebration=False, is_protected=False)
        db.session.add(category)
        db.session.commit()

    entry = Entry(date="2023-06-01", category_id=category.id, title="Release Update", description="Major software release.")
    db.session.add(entry)
    db.session.commit()

    # Request timeline with category filter
    response = test_client.get('/timeline?categories=Release')
    assert response.status_code == 200
    assert b"Release Update" in response.data
    assert b"Birthday" not in response.data  # Entry from another category should not appear

def test_timeline_view_without_category_filter(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/timeline' page is requested (GET) without a category filter
    THEN check the response is valid and all entries are returned
    """
    # Add another category and entry to test filtering
    category = db.session.query(Category).filter_by(name="Release").first()
    if not category:
        category = Category(name="Release", symbol="🚀", color_hex="#FF6347", repeat_annually=False, display_celebration=False, is_protected=False)
        db.session.add(category)
        db.session.commit()
    
    entry = Entry(date="2023-06-01", category_id=category.id, title="Release Update", description="Major software release.")
    db.session.add(entry)
    db.session.commit()

    response = test_client.get('/timeline')
    assert response.status_code == 200
    assert b"Birthday" in response.data  # Ensure entries from all categories are displayed
    assert b"Release Update" in response.data  # Assuming this entry was added in the previous test

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
    GIVEN a Flask application with entries
    WHEN the purge old entries endpoint is called
    THEN check that old non-repeating entries are removed while keeping protected ones
    """
    # First, count existing entries
    initial_count = db.session.query(Entry).count()

    # Add some old entries
    category_release = db.session.query(Category).filter_by(name="Release").first()
    category_birthday = db.session.query(Category).filter_by(name="Birthday").first()

    # Create entries from different years
    old_entry = Entry(
        date="2020-01-01",
        category_id=category_release.id,
        title="Old Release",
        description="This should be purged"
    )
    protected_old_entry = Entry(
        date="2020-02-01",
        category_id=category_birthday.id,  # Birthday category is protected
        title="Old Birthday",
        description="This should not be purged"
    )

    db.session.add_all([old_entry, protected_old_entry])
    db.session.commit()

    # Call the purge endpoint
    response = test_client.post('/purge-old-entries')
    assert response.status_code == 200

    # Verify that only the old non-protected entry was purged
    remaining_entries = db.session.query(Entry).all()
    
    # Check specific entries
    assert not db.session.query(Entry).filter_by(title="Old Release").first()  # Should be purged
    assert db.session.query(Entry).filter_by(title="Old Birthday").first()  # Should be kept

    # Check final count (should be initial count + 1 for the protected entry)
    assert db.session.query(Entry).count() == initial_count + 1

    # Cleanup
    db.session.query(Entry).filter_by(title="Old Birthday").delete()
    db.session.commit()

def test_entries_sorted_by_date(test_client, init_database):
    """
    GIVEN a Flask application with multiple entries
    WHEN entries are retrieved
    THEN check that they are properly sorted by date
    """
    # Add entries with different dates
    category = db.session.query(Category).filter_by(name="Release").first()
    dates = ["2023-03-15", "2024-01-01", "2023-12-25"]
    
    for i, date_str in enumerate(dates):
        entry = Entry(
            date=date_str,
            category_id=category.id,
            title=f"Entry {i+1}",
            description=f"Test entry {i+1}"
        )
        db.session.add(entry)
    db.session.commit()

    # Get entries through API
    response = test_client.get('/api/data')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Extract dates from entries
    entry_dates = [entry['date'] for entry in data['entries']]
    
    # Verify dates are in ascending order
    sorted_dates = sorted(entry_dates)
    assert entry_dates == sorted_dates

    # Verify the order is correct
    assert entry_dates[0] < entry_dates[-1]  # First date should be earlier than last date