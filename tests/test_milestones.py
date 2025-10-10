from app.helpers import calculate_milestone
from app.models import Entry, Category
from app import db
from datetime import datetime, date


def test_calculate_milestone_first_anniversary():
    """Test that the first anniversary is detected as a milestone."""
    is_milestone, years, milestone_type = calculate_milestone(2020, 2021)
    assert is_milestone is True
    assert years == 1
    assert milestone_type == "1st"


def test_calculate_milestone_fifth_anniversary():
    """Test that the 5th anniversary is detected as a milestone."""
    is_milestone, years, milestone_type = calculate_milestone(2015, 2020)
    assert is_milestone is True
    assert years == 5
    assert milestone_type == "5th"


def test_calculate_milestone_tenth_anniversary():
    """Test that the 10th anniversary is detected as a milestone."""
    is_milestone, years, milestone_type = calculate_milestone(2010, 2020)
    assert is_milestone is True
    assert years == 10
    assert milestone_type == "10th"


def test_calculate_milestone_fifteenth_anniversary():
    """Test that the 15th anniversary is detected as a milestone."""
    is_milestone, years, milestone_type = calculate_milestone(2005, 2020)
    assert is_milestone is True
    assert years == 15
    assert milestone_type == "15th"


def test_calculate_milestone_twenty_fifth_anniversary():
    """Test that the 25th anniversary is detected as a milestone."""
    is_milestone, years, milestone_type = calculate_milestone(1995, 2020)
    assert is_milestone is True
    assert years == 25
    assert milestone_type == "25th"


def test_calculate_milestone_fiftieth_anniversary():
    """Test that the 50th anniversary is detected as a milestone."""
    is_milestone, years, milestone_type = calculate_milestone(1970, 2020)
    assert is_milestone is True
    assert years == 50
    assert milestone_type == "50th"


def test_calculate_milestone_non_milestone():
    """Test that non-milestone years are not detected."""
    # 2nd year - not a milestone
    is_milestone, years, milestone_type = calculate_milestone(2018, 2020)
    assert is_milestone is False
    assert years == 2
    assert milestone_type is None
    
    # 7th year - not a milestone
    is_milestone, years, milestone_type = calculate_milestone(2013, 2020)
    assert is_milestone is False
    assert years == 7
    assert milestone_type is None


def test_calculate_milestone_no_start_year():
    """Test that entries without a start year return no milestone."""
    is_milestone, years, milestone_type = calculate_milestone(None, 2020)
    assert is_milestone is False
    assert years is None
    assert milestone_type is None


def test_calculate_milestone_same_year():
    """Test that the same year (0 years) is not a milestone."""
    is_milestone, years, milestone_type = calculate_milestone(2020, 2020)
    assert is_milestone is False
    assert years == 0
    assert milestone_type is None


def test_entry_with_original_start_year(test_client, init_database):
    """Test that creating a recurring entry stores the original start year."""
    # Get a category with repeat_annually=True
    category = db.session.query(Category).filter_by(name="Birthday").first()
    assert category.repeat_annually is True
    
    data = {
        'date': "2020-05-15",
        'category': category.name,
        'title': "Test Birthday",
        'description': "Should have start year"
    }
    
    response = test_client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # Check that the entry was created with original_start_year
    entry = db.session.query(Entry).filter_by(title="Test Birthday").first()
    assert entry is not None
    assert entry.original_start_year == 2020


def test_entry_without_original_start_year_non_recurring(test_client, init_database):
    """Test that non-recurring entries don't get a start year."""
    # Get a category with repeat_annually=False
    category = db.session.query(Category).filter_by(name="Release").first()
    assert category.repeat_annually is False
    
    data = {
        'date': "2021-06-01",
        'category': category.name,
        'title': "One-time Release",
        'description': "Should not have start year"
    }
    
    response = test_client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # Check that the entry was created without original_start_year
    entry = db.session.query(Entry).filter_by(title="One-time Release").first()
    assert entry is not None
    assert entry.original_start_year is None


def test_milestone_preserved_after_roll_forward(test_client, init_database):
    """Test that original_start_year is preserved when creating entries."""
    category = db.session.query(Category).filter_by(name="Birthday").first()
    
    # Create an entry with original_start_year for a recurring event
    entry = Entry(
        date="2020-05-15",
        category=category,
        title="Anniversary Event",
        description="Started in 2020",
        original_start_year=2020
    )
    db.session.add(entry)
    db.session.commit()
    entry_id = entry.id
    
    # Verify that original_start_year is preserved
    saved_entry = db.session.get(Entry, entry_id)
    assert saved_entry.original_start_year == 2020


def test_new_recurring_entry_gets_start_year(test_client, init_database):
    """Test that newly created recurring entries get original_start_year set."""
    category = db.session.query(Category).filter_by(name="Birthday").first()
    assert category.repeat_annually is True
    
    data = {
        'date': "2023-06-15",
        'category': category.name,
        'title': "New Recurring Event",
        'description': "Should get start year"
    }
    
    response = test_client.post('/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # Check that the entry was created with original_start_year
    entry = db.session.query(Entry).filter_by(title="New Recurring Event").first()
    assert entry is not None
    assert entry.original_start_year == 2023
