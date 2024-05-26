import json

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
    assert "birthday" in data

def test_grafana_query(test_client, init_database):
    """
    Test the /grafana/query endpoint to ensure it returns the correct timeseries data.
    """
    query_data = {
        "targets": [
            {"target": "birthday", "type": "timeserie"}
        ]
    }
    response = test_client.post('/grafana/query', data=json.dumps(query_data), content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]['target'] == "birthday"
    assert isinstance(data[0]['datapoints'], list)

def test_grafana_annotations(test_client, init_database):
    """
    Test the /grafana/annotations endpoint to ensure it returns the correct annotations based on the query.
    """
    annotation_data = {
        "annotation": {
            "query": "#deploy"
        }
    }
    response = test_client.post('/grafana/annotations', data=json.dumps(annotation_data), content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

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
    assert {"text": "birthday"} in data

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