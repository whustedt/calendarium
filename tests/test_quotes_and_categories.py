from app.models import Quote, Category
from app import db
from datetime import datetime
import json

def test_create_quote_with_valid_data(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN a new quote is created with valid data
    THEN check that the quote is created successfully
    """
    data = {
        'text': "Test quote",
        'author': "Test Author",
        'category': "Inspiration",
        'url': "https://example.com"
    }

    response = test_client.post('/quotes/create', data=data, follow_redirects=True)
    assert response.status_code == 200

    quote = Quote.query.filter_by(text="Test quote").first()
    assert quote is not None
    assert quote.author == "Test Author"
    assert quote.category == "Inspiration"
    assert quote.url == "https://example.com"

def test_get_random_quote(test_client, init_database):
    """
    GIVEN a Flask application with quotes
    WHEN the random quote endpoint is called
    THEN check that it returns a valid quote
    """
    # Create a test quote
    quote = Quote(
        text="Random test quote",
        author="Random Author",
        category="Test",
        last_updated_by="127.0.0.1"
    )
    db.session.add(quote)
    db.session.commit()

    response = test_client.get('/quotes/random')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'text' in data
    assert 'author' in data
    assert 'category' in data

def test_get_daily_quote(test_client, init_database):
    """
    GIVEN a Flask application with quotes
    WHEN the daily quote endpoint is called multiple times on the same day
    THEN check that it returns the same quote
    """
    # Create test quotes
    quotes = [
        Quote(text=f"Daily test quote {i}", author=f"Author {i}", last_updated_by="127.0.0.1")
        for i in range(3)
    ]
    db.session.add_all(quotes)
    db.session.commit()

    # Get quote twice on the same day
    response1 = test_client.get('/quotes/daily')
    response2 = test_client.get('/quotes/daily')

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = json.loads(response1.data)
    data2 = json.loads(response2.data)

    # Should return the same quote for the same day
    assert data1['text'] == data2['text']
    assert data1['author'] == data2['author']

def test_category_filtering(test_client, init_database):
    """
    GIVEN a Flask application with quotes in different categories
    WHEN quotes are filtered by category
    THEN check that only quotes from the requested category are returned
    """
    # Create test quotes in different categories
    quotes = [
        Quote(text="Quote 1", author="Author 1", category="Technology", last_updated_by="127.0.0.1"),
        Quote(text="Quote 2", author="Author 2", category="Inspiration", last_updated_by="127.0.0.1"),
        Quote(text="Quote 3", author="Author 3", category="Technology", last_updated_by="127.0.0.1")
    ]
    db.session.add_all(quotes)
    db.session.commit()

    response = test_client.get('/quotes/random?category=Technology')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data['category'] == "Technology"

def test_create_category(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN a new category is created with valid data
    THEN check that the category is created successfully
    """
    data = {
        'name': 'NewCategory',
        'symbol': '🌟',
        'color_hex': '#FF5733',
        'repeat_annually': 'true',
        'display_celebration': 'true',
        'is_protected': 'false'
    }

    response = test_client.post('/categories', data=data, follow_redirects=True)
    assert response.status_code == 200

    category = Category.query.filter_by(name='NewCategory').first()
    assert category is not None
    assert category.symbol == '🌟'
    assert category.color_hex == '#FF5733'
    assert category.repeat_annually is True
    assert category.display_celebration is True
    assert category.is_protected is False

def test_update_category(test_client, init_database):
    """
    GIVEN a Flask application with an existing category
    WHEN the category is updated
    THEN check that the changes are saved correctly
    """
    # Create a test category
    category = Category(
        name='TestCategory',
        symbol='🌟',
        color_hex='#FF5733',
        repeat_annually=False,
        display_celebration=False,
        is_protected=False,
        last_updated_by='127.0.0.1'
    )
    db.session.add(category)
    db.session.commit()

    update_data = {
        'name': 'UpdatedCategory',
        'symbol': '🎉',
        'color_hex': '#33FF57',
        'repeat_annually': 'true',
        'display_celebration': 'true',
        'is_protected': 'true'
    }

    response = test_client.post(f'/categories/update/{category.id}', data=update_data, follow_redirects=True)
    assert response.status_code == 200

    updated_category = Category.query.get(category.id)
    assert updated_category.name == 'UpdatedCategory'
    assert updated_category.symbol == '🎉'
    assert updated_category.color_hex == '#33FF57'
    assert updated_category.repeat_annually is True
    assert updated_category.display_celebration is True
    assert updated_category.is_protected is True

def test_delete_category_with_no_entries(test_client, init_database):
    """
    GIVEN a Flask application with a category that has no entries
    WHEN the category is deleted
    THEN check that the deletion is successful
    """
    # Create a test category
    category = Category(
        name='ToDelete',
        symbol='❌',
        color_hex='#FF0000',
        repeat_annually=False,
        display_celebration=False,
        is_protected=False,
        last_updated_by='127.0.0.1'
    )
    db.session.add(category)
    db.session.commit()

    category_id = category.id
    response = test_client.post(f'/categories/delete/{category_id}', follow_redirects=True)
    assert response.status_code == 200

    # Verify category was deleted
    deleted_category = Category.query.get(category_id)
    assert deleted_category is None

def test_delete_category_with_entries(test_client, init_database):
    """
    GIVEN a Flask application with a category that has associated entries
    WHEN attempting to delete the category
    THEN check that the deletion is prevented
    """
    # Create a test category with an associated entry
    category = Category(
        name='CategoryWithEntries',
        symbol='📝',
        color_hex='#0000FF',
        repeat_annually=False,
        display_celebration=False,
        is_protected=False,
        last_updated_by='127.0.0.1'
    )
    db.session.add(category)
    db.session.commit()

    # Create an entry associated with the category
    from app.models import Entry
    entry = Entry(
        date="2025-01-01",
        category_id=category.id,
        title="Test Entry",
        description="Test Description",
        last_updated_by="127.0.0.1"
    )
    db.session.add(entry)
    db.session.commit()

    response = test_client.post(f'/categories/delete/{category.id}', follow_redirects=True)
    assert response.status_code == 400

    # Verify category still exists
    category_exists = Category.query.get(category.id) is not None
    assert category_exists is True
