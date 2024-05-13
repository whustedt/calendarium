from app.models import Entry

def test_home_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check the response is valid
    """
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"Cake" in response.data

def test_create_entry(test_client, init_database):
    data = {
        'date': "2021-06-01",
        'category': "release",
        'title': "New Product Launch",
        'description': "Launching the new product"
    }

    response = test_client.post('/create', data=data, follow_redirects=True)
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.data.decode('utf-8')}"
    assert Entry.query.count() == 2  # Assuming one entry was already in the database from setup

def test_update_entry(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/update/<id>' page is posted to (POST) with updated data
    THEN check the response is valid and the entry is updated correctly
    """
    response = test_client.post('/update/1', data={
        'date': "2021-06-01",
        'category': "custom",
        'title': "Updated Title",
        'description': "Updated description"
    }, follow_redirects=True)
    assert response.status_code == 200
    entry = Entry.query.get(1)
    assert entry.title == "Updated Title"

def test_delete_entry(test_client, init_database):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/delete/<id>' endpoint is called (POST)
    THEN check that the entry is removed from the database
    """
    initial_count = Entry.query.count()
    response = test_client.post('/delete/1', follow_redirects=True)
    assert response.status_code == 200
    assert Entry.query.count() == initial_count - 1

def test_timeline_view(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/timeline' page is requested (GET)
    THEN check the response is valid and potentially some data is returned
    """
    response = test_client.get('/timeline')
    assert response.status_code == 200
    # Additional assertions can check specific content or data structures1
