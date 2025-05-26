from app.models import Quote, Category, QuoteConstants
from app import db
from datetime import datetime, date, timedelta
from unittest.mock import patch
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

def test_create_quote_validation(test_client, init_database):
    """
    GIVEN a Flask application
    WHEN a new quote is created with invalid data
    THEN check that appropriate validation errors are returned
    """
    # Test missing required fields
    response = test_client.post('/quotes/create', data={'text': 'Quote without author'}, follow_redirects=True)
    assert response.status_code == 400
    assert b"Please provide both quote and author" in response.data

    # Test text too long
    long_text = "x" * (QuoteConstants.MAX_TEXT_LENGTH + 1)
    response = test_client.post('/quotes/create', data={
        'text': long_text, 
        'author': 'Author'
    }, follow_redirects=True)
    assert response.status_code == 400
    assert b"Quote text is too long" in response.data

    # Test author too long
    long_author = "x" * (QuoteConstants.MAX_AUTHOR_LENGTH + 1)
    response = test_client.post('/quotes/create', data={
        'text': 'Valid quote', 
        'author': long_author
    }, follow_redirects=True)
    assert response.status_code == 400
    assert b"Author name is too long" in response.data
    
    # Test category too long
    long_category = "x" * (QuoteConstants.MAX_CATEGORY_LENGTH + 1)
    response = test_client.post('/quotes/create', data={
        'text': 'Valid quote', 
        'author': 'Valid author',
        'category': long_category
    }, follow_redirects=True)
    assert response.status_code == 400
    assert b"Category is too long" in response.data
    
    # Test URL too long
    long_url = "x" * (QuoteConstants.MAX_URL_LENGTH + 1)
    response = test_client.post('/quotes/create', data={
        'text': 'Valid quote', 
        'author': 'Valid author',
        'url': long_url
    }, follow_redirects=True)
    assert response.status_code == 400
    assert b"URL is too long" in response.data

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

def test_seeded_random_quote_consistency(test_client, init_database):
    """
    GIVEN a Flask application with multiple quotes
    WHEN getting a random quote with the same seed
    THEN verify it returns the same quote consistently
    """
    # Create multiple test quotes
    quotes = [
        Quote(text=f"Quote {i}", author=f"Author {i}", category="Test", last_updated_by="127.0.0.1")
        for i in range(3)
    ]
    db.session.add_all(quotes)
    db.session.commit()

    from app.routes_quotes import get_random_quote
    
    # Same seed should return same quote
    seed = 12345
    first_quote = get_random_quote(seed=seed)
    second_quote = get_random_quote(seed=seed)
    assert first_quote.id == second_quote.id
    
    # Different seed should possibly return different quote
    different_seed = 67890
    different_quote = get_random_quote(seed=different_seed)
    # Note: There's a small chance this could be the same quote due to randomness
    # but with different seeds it's less likely

def test_daily_quote_fair_rotation(test_client, init_database):
    """
    GIVEN a Flask application with multiple quotes
    WHEN getting daily quotes over a full rotation cycle
    THEN verify it uses fair rotation without repetition until all quotes are used
    """
    # Create exactly 5 quotes for testing
    quotes = [
        Quote(text=f"Rotation Quote {i}", author=f"Author {i}", category="Test", last_updated_by="127.0.0.1")
        for i in range(5)
    ]
    db.session.add_all(quotes)
    db.session.commit()

    from app.routes_quotes import select_daily_quote
    
    # Track quotes selected over multiple cycles
    selected_quotes = []
    base_date = date(2025, 6, 1)
    
    # Test two complete cycles (10 days)
    for i in range(10):
        test_date = base_date + timedelta(days=i)
        with patch('app.routes_quotes.date') as mock_date:
            mock_date.today.return_value = test_date
            quote = select_daily_quote()
            selected_quotes.append(quote.id)
    
    # Verify first 5 selections are all different (fair rotation)
    first_cycle = selected_quotes[:5]
    assert len(set(first_cycle)) == 5, "First cycle should include all quotes"
    
    # Verify second cycle starts fresh rotation
    second_cycle = selected_quotes[5:10]
    assert len(set(second_cycle)) == 5, "Second cycle should include all quotes"

def test_daily_quote_deterministic_selection(test_client, init_database):
    """
    GIVEN a Flask application with multiple quotes having the same last_shown date
    WHEN getting daily quotes multiple times on the same day
    THEN verify it returns the same quote consistently (deterministic tiebreaker)
    """
    # Create quotes with same last_shown date
    yesterday = date.today() - timedelta(days=1)
    quotes = [
        Quote(text=f"Deterministic Quote {i}", author=f"Author {i}", 
              category="Test", last_shown=yesterday, last_updated_by="127.0.0.1")
        for i in range(3)
    ]
    db.session.add_all(quotes)
    db.session.commit()

    from app.routes_quotes import select_daily_quote
    
    # Get quote multiple times on same day
    selected_quotes = []
    for _ in range(5):
        quote = select_daily_quote()
        selected_quotes.append(quote.id)
    
    # All selections should be the same
    assert len(set(selected_quotes)) == 1, "Should return same quote consistently on same day"

def test_category_filtered_random_quote(test_client, init_database):
    """
    GIVEN a Flask application with quotes in different categories
    WHEN getting a random quote with category filter
    THEN verify it only returns quotes from that category
    """
    # Create quotes in different categories
    quotes = [
        Quote(text="Tech Quote 1", author="Author 1", category="Technology", last_updated_by="127.0.0.1"),
        Quote(text="Tech Quote 2", author="Author 2", category="Technology", last_updated_by="127.0.0.1"),
        Quote(text="Inspiration Quote", author="Author 3", category="Inspiration", last_updated_by="127.0.0.1")
    ]
    db.session.add_all(quotes)
    db.session.commit()

    # Test category filter
    response = test_client.get('/quotes/random?category=Technology')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['category'] == "Technology"

    # Multiple categories
    response = test_client.get('/quotes/random?category=Technology,Inspiration')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['category'] in ["Technology", "Inspiration"]

def test_empty_category_filter(test_client, init_database):
    """
    GIVEN a Flask application with quotes
    WHEN getting quotes with empty category filter
    THEN verify it returns quotes normally (ignores empty filter)
    """
    quote = Quote(text="Test quote", author="Test Author", category="Test", last_updated_by="127.0.0.1")
    db.session.add(quote)
    db.session.commit()

    # Empty category should be ignored
    response = test_client.get('/quotes/random?category=')
    assert response.status_code == 200

    # Whitespace-only category should be ignored
    response = test_client.get('/quotes/random?category=   ')
    assert response.status_code == 200    

def test_no_quotes_available(test_client, init_database):
    """
    GIVEN a Flask application with no quotes
    WHEN requesting quotes
    THEN verify appropriate responses are returned
    """
    # Test daily quote with no quotes
    response = test_client.get('/quotes/daily')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data
    assert "No quotes found" in data["error"]

    # Test random quote with no quotes
    response = test_client.get('/quotes/random')
    assert response.status_code == 404

    # Test with non-existent category
    quote = Quote(text="Test", author="Author", category="Existing", last_updated_by="127.0.0.1")
    db.session.add(quote)
    db.session.commit()

    response = test_client.get('/quotes/daily?category=NonExistent')
    assert response.status_code == 404

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

    updated_category = db.session.get(Category, category.id)
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
    deleted_category = db.session.get(Category, category_id)
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
    category_exists = db.session.get(Category, category.id) is not None
    assert category_exists is True

def test_quote_endpoints_with_color_parameter(test_client, init_database):
    """
    GIVEN a Flask application with quotes
    WHEN requesting quotes with color parameter
    THEN verify it returns background color in response
    """
    quote = Quote(text="Color test", author="Author", category="Test", last_updated_by="127.0.0.1")
    db.session.add(quote)
    db.session.commit()

    # Test random quote with color
    response = test_client.get('/quotes/random?color=true')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'backgroundColor' in data
    assert data['backgroundColor'] is not None
    assert data['backgroundColor'].startswith('hsl(')

    # Test daily quote with color
    response = test_client.get('/quotes/daily?color=true')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'backgroundColor' in data
    assert data['backgroundColor'] is not None

def test_quote_html_views(test_client, init_database):
    """
    GIVEN a Flask application with quotes
    WHEN accessing HTML view endpoints
    THEN verify they return proper HTML responses
    """
    quote = Quote(text="HTML test", author="Author", category="Test", last_updated_by="127.0.0.1")
    db.session.add(quote)
    db.session.commit()

    # Test random quote view
    response = test_client.get('/quotes/random/view')
    assert response.status_code == 200
    assert response.content_type.startswith('text/html')

    # Test daily quote view
    response = test_client.get('/quotes/daily/view')
    assert response.status_code == 200
    assert response.content_type.startswith('text/html')

def test_quote_edit_validation(test_client, init_database):
    """
    GIVEN a Flask application with an existing quote
    WHEN editing a quote with invalid data
    THEN verify appropriate validation errors are returned
    """
    quote = Quote(text="Original text", author="Original Author", last_updated_by="127.0.0.1")
    db.session.add(quote)
    db.session.commit()

    # Test empty text
    response = test_client.post(f'/quotes/edit/{quote.id}', data={
        'text': '',
        'author': 'Author'
    }, follow_redirects=True)
    assert response.status_code == 400
    assert b"Please provide both quote and author" in response.data

    # Test text too long
    long_text = "x" * (QuoteConstants.MAX_TEXT_LENGTH + 1)
    response = test_client.post(f'/quotes/edit/{quote.id}', data={
        'text': long_text,
        'author': 'Author'
    }, follow_redirects=True)
    assert response.status_code == 400
    assert b"Quote text is too long" in response.data

def test_quote_last_shown_tracking(test_client, init_database):
    """
    GIVEN a Flask application with quotes
    WHEN daily quotes are selected over time
    THEN verify last_shown dates are properly tracked
    """
    quotes = [
        Quote(text=f"Tracking Quote {i}", author=f"Author {i}", last_updated_by="127.0.0.1")
        for i in range(3)
    ]
    db.session.add_all(quotes)
    db.session.commit()

    from app.routes_quotes import select_daily_quote
    
    # Select quote on first day
    first_date = date(2025, 7, 1)
    with patch('app.routes_quotes.date') as mock_date:
        mock_date.today.return_value = first_date
        first_quote = select_daily_quote()
        assert first_quote.last_shown == first_date
    
    # Select quote on second day
    second_date = date(2025, 7, 2)
    with patch('app.routes_quotes.date') as mock_date:
        mock_date.today.return_value = second_date
        second_quote = select_daily_quote()
        assert second_quote.last_shown == second_date
        assert second_quote.id != first_quote.id  # Should be different quote

def test_quote_response_format(test_client, init_database):
    """
    GIVEN a Flask application with a quote
    WHEN requesting quote via API
    THEN verify response contains all expected fields
    """
    quote = Quote(
        text="Test quote with **markdown**",
        author="Test Author",
        category="Test Category",
        url="https://example.com",
        last_updated_by="127.0.0.1"
    )
    db.session.add(quote)
    db.session.commit()

    response = test_client.get('/quotes/random')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    expected_fields = ['id', 'text', 'author', 'category', 'url', 'lastUpdatedBy', 'period']
    for field in expected_fields:
        assert field in data
    
    assert data['text'] == "Test quote with **markdown**"
    assert data['author'] == "Test Author"
    assert data['category'] == "Test Category"
    assert data['url'] == "https://example.com"

def test_performance_large_quote_set(test_client, init_database):
    """
    GIVEN a Flask application with a large number of quotes
    WHEN selecting daily quotes over time
    THEN verify the system performs efficiently and maintains fair rotation
    """
    import time
    
    # Create a larger set of quotes for performance testing
    quotes = [
        Quote(text=f"Performance Quote {i}", author=f"Author {i}", 
              category=f"Category {i % 5}", last_updated_by="127.0.0.1")
        for i in range(100)
    ]
    db.session.add_all(quotes)
    db.session.commit()

    from app.routes_quotes import select_daily_quote
    
    # Measure performance of quote selection
    start_time = time.time()
    selected_quotes = []
    base_date = date(2025, 8, 1)
    
    # Test 50 days of selections
    for i in range(50):
        test_date = base_date + timedelta(days=i)
        with patch('app.routes_quotes.date') as mock_date:
            mock_date.today.return_value = test_date
            quote = select_daily_quote()
            selected_quotes.append(quote.id)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Performance should be reasonable (less than 1 second for 50 selections)
    assert execution_time < 1.0, f"Performance test failed: {execution_time}s for 50 quote selections"
    
    # Verify fair rotation - first 50 should cover most quotes
    unique_quotes = len(set(selected_quotes[:50]))
    assert unique_quotes >= 45, f"Fair rotation failed: only {unique_quotes} unique quotes in first 50 selections"

def test_category_performance(test_client, init_database):
    """
    GIVEN a Flask application with quotes in multiple categories
    WHEN filtering by category repeatedly
    THEN verify performance is acceptable
    """
    import time
    
    # Create quotes in different categories
    categories = ["Tech", "Inspiration", "Humor", "Philosophy", "Science"]
    quotes = []
    for category in categories:
        for i in range(20):  # 20 quotes per category
            quotes.append(Quote(
                text=f"{category} Quote {i}", 
                author=f"Author {i}", 
                category=category,
                last_updated_by="127.0.0.1"
            ))
    
    db.session.add_all(quotes)
    db.session.commit()

    from app.routes_quotes import get_random_quote, select_daily_quote
    
    start_time = time.time()
    
    # Test category filtering performance
    for category in categories:
        for _ in range(10):  # 10 selections per category
            random_quote = get_random_quote(category=category)
            assert random_quote is not None
            assert random_quote.category == category
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Should complete 50 category-filtered selections quickly
    assert execution_time < 0.5, f"Category filtering performance: {execution_time}s for 50 selections"
