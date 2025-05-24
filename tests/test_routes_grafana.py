import json
from app.models import Entry, Category
from app import db

def test_grafana_test_connection(test_client):
    """
    Test the /grafana/ endpoint to ensure it returns a successful connection message.
    """
    response = test_client.get('/grafana/')
    assert response.status_code == 200
    assert response.data == b"Connection established"

def test_grafana_search(test_client, init_database):
    """
    Test the /grafana/search endpoint to ensure it returns a list of available categories.
    """

    response = test_client.post('/grafana/search')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert "Birthday" in data
    assert "Release" in data

def test_grafana_query(test_client, init_database):
    """
    Test the /grafana/query endpoint to ensure it returns the correct timeseries data.
    """
    # Set up category and entry for testing
    category = Category(name="Party", symbol="🎉", color_hex="#FFD700")
    db.session.add(category)
    db.session.flush()  # to obtain the category id
    db.session.add(Entry(date="2021-05-20", category_id=category.id, title="John's Birthday", description="Birthday party"))
    db.session.commit()

    query_data = {
        "targets": [
            {"target": "Party", "type": "timeserie"}
        ]
    }
    response = test_client.post('/grafana/query', data=json.dumps(query_data), content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['target'] == "Party"
    assert isinstance(data[0]['datapoints'], list)

def test_grafana_query_with_invalid_category(test_client, init_database):
    """
    Test the /grafana/query endpoint with an invalid category
    """
    query_data = {
        "targets": [
            {"target": "NonExistentCategory", "type": "timeserie"}
        ]
    }
    response = test_client.post('/grafana/query', 
                              data=json.dumps(query_data), 
                              content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    # For invalid category, expect empty list
    assert len(data) == 0

def test_grafana_query_with_date_range(test_client, init_database):
    """
    Test the /grafana/query endpoint with a specific date range
    """
    # Add test entries
    category = Category(name="Test", symbol="🔍", color_hex="#123456")
    db.session.add(category)
    db.session.flush()

    dates = ["2023-01-01", "2023-06-01", "2024-01-01"]
    for date_str in dates:
        entry = Entry(
            date=date_str,
            category_id=category.id,
            title=f"Test Entry {date_str}",
            description="Test entry"
        )
        db.session.add(entry)
    db.session.commit()

    query_data = {
        "range": {
            "from": "2023-01-01T00:00:00.000Z",
            "to": "2023-12-31T23:59:59.999Z"
        },
        "targets": [
            {"target": "Test", "type": "timeserie"}
        ]
    }
    
    response = test_client.post('/grafana/query', 
                              data=json.dumps(query_data), 
                              content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Expect entries from within the time range and nearby
    datapoints = data[0]['datapoints']
    assert len([d for d in datapoints if d[1] is not None]) == 3

def test_grafana_annotations(test_client, init_database):
    """
    Test the /grafana/annotations endpoint to ensure it returns the correct annotations based on the query.
    """
    category = Category(name="Launch", symbol="🚀", color_hex="#FF6347")
    db.session.add(category)
    db.session.flush()
    db.session.add(Entry(date="2021-05-21", category_id=category.id, title="Product Launch", description="Launching a new product"))
    db.session.commit()

    annotation_data = {
        "annotation": {
            "query": "Launch"
        }
    }
    response = test_client.post('/grafana/annotations', data=json.dumps(annotation_data), content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['title'] == "Product Launch"
    assert data[0]['text'] == "Launching a new product"

def test_grafana_annotations_with_empty_query(test_client, init_database):
    """
    Test the /grafana/annotations endpoint with an empty query
    """
    annotation_data = {
        "annotation": {
            "query": ""
        }
    }
    response = test_client.post('/grafana/annotations', 
                              data=json.dumps(annotation_data), 
                              content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    # Empty query returns empty list
    assert len(data) == 0

def test_grafana_tag_keys(test_client):
    """
    Test the /grafana/tag-keys endpoint to ensure it returns the correct tag keys.
    """
    response = test_client.post('/grafana/tag-keys')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert {"type": "string", "text": "category"} in data
    assert {"type": "string", "text": "date"} in data

def test_grafana_tag_values_category(test_client, init_database):
    """
    Test the /grafana/tag-values endpoint with key='category' to ensure it returns the correct category values.
    """
    request_data = {
        "key": "category"
    }
    response = test_client.post('/grafana/tag-values', data=json.dumps(request_data), content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert {"text": "Birthday"} in data

def test_grafana_tag_values_date(test_client, init_database):
    """
    Test the /grafana/tag-values endpoint with key='date' to ensure it returns the correct date values.
    """
    request_data = {
        "key": "date"
    }
    response = test_client.post('/grafana/tag-values', data=json.dumps(request_data), content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert {"text": "2021-05-20"} in data

def test_grafana_tag_values_invalid_key(test_client, init_database):
    """
    Test the /grafana/tag-values endpoint with an invalid key
    """
    request_data = {
        "key": "invalid_key"
    }
    response = test_client.post('/grafana/tag-values', 
                              data=json.dumps(request_data), 
                              content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 0  # Should return empty list for invalid key