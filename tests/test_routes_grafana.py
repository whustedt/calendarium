import json

from app import db
from app.models import Category, Entry


def test_grafana_test_connection(test_client):
    response = test_client.get('/grafana/')
    assert response.status_code == 200
    assert response.data == b"Connection established"


def test_grafana_infinity_categories(test_client, init_database):
    response = test_client.get('/grafana/infinity/categories')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert {"category": "Birthday"} in data
    assert {"category": "Release"} in data


def test_grafana_infinity_timeseries(test_client, init_database):
    category = Category(name="Party", symbol="🎉", color_hex="#FFD700")
    db.session.add(category)
    db.session.flush()
    db.session.add(Entry(date="2021-05-20", category_id=category.id, title="John's Birthday", description="Birthday party"))
    db.session.commit()

    response = test_client.get('/grafana/infinity/timeseries?category=Party')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['category'] == "Party"
    assert data[0]['date'] == "2021-05-20"
    assert data[0]['count'] == 1
    assert isinstance(data[0]['timestamp'], int)


def test_grafana_infinity_timeseries_with_date_range(test_client, init_database):
    category = Category(name="Test", symbol="🔍", color_hex="#123456")
    db.session.add(category)
    db.session.flush()

    for date_str in ["2023-01-01", "2023-06-01", "2024-01-01"]:
        db.session.add(Entry(date=date_str, category_id=category.id, title=f"Test Entry {date_str}", description="Test entry"))
    db.session.commit()

    response = test_client.get(
        '/grafana/infinity/timeseries?category=Test&from=2023-01-01T00:00:00.000Z&to=2023-12-31T23:59:59.999Z'
    )
    assert response.status_code == 200
    data = json.loads(response.data)

    assert len(data) == 2
    assert {row['date'] for row in data} == {"2023-01-01", "2023-06-01"}


def test_grafana_infinity_annotations(test_client, init_database):
    category = Category(name="Launch", symbol="🚀", color_hex="#FF6347")
    db.session.add(category)
    db.session.flush()
    db.session.add(Entry(date="2021-05-21", category_id=category.id, title="Product Launch", description="Launching a new product"))
    db.session.commit()

    response = test_client.get('/grafana/infinity/annotations?categories=Launch')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['title'] == "Product Launch"
    assert data[0]['text'] == "Launching a new product"
    assert data[0]['category'] == "Launch"


def test_grafana_infinity_annotations_with_empty_query(test_client, init_database):
    response = test_client.get('/grafana/infinity/annotations?categories=')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
