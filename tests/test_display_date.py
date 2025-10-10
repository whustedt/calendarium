"""Tests for display_date calculation and milestone detection for recurring events."""
from datetime import date, timedelta
from app.helpers import calculate_display_date, calculate_milestone_info
from app.models import Entry, Category
from app import db
import json


def test_calculate_display_date_non_recurring():
    """Test that non-recurring events return the original date."""
    entry_date = date(2020, 5, 15)
    today = date(2025, 10, 10)
    
    display_date = calculate_display_date(entry_date, is_recurring=False, today=today)
    
    assert display_date == entry_date


def test_calculate_display_date_recurring_future():
    """Test that recurring events in the future this year return current year date."""
    entry_date = date(2020, 12, 25)  # Christmas
    today = date(2025, 10, 10)  # Before Christmas
    
    display_date = calculate_display_date(entry_date, is_recurring=True, today=today)
    
    assert display_date == date(2025, 12, 25)


def test_calculate_display_date_recurring_past():
    """Test that recurring events already past this year return next year date."""
    entry_date = date(2020, 5, 15)
    today = date(2025, 10, 10)  # After May 15
    
    display_date = calculate_display_date(entry_date, is_recurring=True, today=today)
    
    assert display_date == date(2026, 5, 15)


def test_calculate_display_date_leap_year():
    """Test leap year handling (Feb 29)."""
    entry_date = date(2020, 2, 29)
    
    # In a leap year
    today = date(2024, 1, 1)
    display_date = calculate_display_date(entry_date, is_recurring=True, today=today)
    assert display_date == date(2024, 2, 29)
    
    # In a non-leap year, should use Feb 28
    today = date(2025, 1, 1)
    display_date = calculate_display_date(entry_date, is_recurring=True, today=today)
    assert display_date == date(2025, 2, 28)
    
    # Past in non-leap year, should go to next year
    today = date(2025, 3, 1)
    display_date = calculate_display_date(entry_date, is_recurring=True, today=today)
    assert display_date == date(2026, 2, 28)


def test_calculate_milestone_info_known_year():
    """Test milestone calculation for events with known start year."""
    entry_date = date(2020, 5, 15)
    display_date_obj = date(2025, 5, 15)
    
    milestone_info = calculate_milestone_info(entry_date, display_date_obj, is_recurring=True)
    
    assert milestone_info['years_since'] == 5
    assert milestone_info['milestone_year'] == 5
    assert milestone_info['is_milestone'] is True


def test_calculate_milestone_info_non_milestone():
    """Test that non-milestone years are correctly identified."""
    entry_date = date(2020, 5, 15)
    display_date_obj = date(2023, 5, 15)
    
    milestone_info = calculate_milestone_info(entry_date, display_date_obj, is_recurring=True)
    
    assert milestone_info['years_since'] == 3
    assert milestone_info['milestone_year'] is None
    assert milestone_info['is_milestone'] is False


def test_calculate_milestone_info_unknown_year():
    """Test that year 0001 (unknown year) doesn't show milestones."""
    entry_date = date(1, 5, 15)  # Year 0001
    display_date_obj = date(2025, 5, 15)
    
    milestone_info = calculate_milestone_info(entry_date, display_date_obj, is_recurring=True)
    
    assert milestone_info['years_since'] is None
    assert milestone_info['milestone_year'] is None
    assert milestone_info['is_milestone'] is False


def test_calculate_milestone_info_non_recurring():
    """Test that non-recurring events don't show milestones."""
    entry_date = date(2020, 5, 15)
    display_date_obj = date(2025, 5, 15)
    
    milestone_info = calculate_milestone_info(entry_date, display_date_obj, is_recurring=False)
    
    assert milestone_info['years_since'] is None
    assert milestone_info['milestone_year'] is None
    assert milestone_info['is_milestone'] is False


def test_milestone_years():
    """Test various milestone years."""
    entry_date = date(2000, 1, 1)
    
    # Test different milestone years
    milestones = {
        1: True, 5: True, 10: True, 15: True, 20: True, 25: True,
        30: True, 40: True, 50: True, 60: True, 75: True, 100: True,
        2: False, 3: False, 7: False, 12: False, 35: False
    }
    
    for years, should_be_milestone in milestones.items():
        display_date_obj = date(2000 + years, 1, 1)
        milestone_info = calculate_milestone_info(entry_date, display_date_obj, is_recurring=True)
        
        assert milestone_info['years_since'] == years
        assert milestone_info['is_milestone'] == should_be_milestone
        if should_be_milestone:
            assert milestone_info['milestone_year'] == years
        else:
            assert milestone_info['milestone_year'] is None


def test_api_returns_display_date(test_client, init_database):
    """Test that the API returns display_date for entries."""
    response = test_client.get('/api/data')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    entries = data['entries']
    
    # Check that all entries have the new fields
    for entry in entries:
        assert 'display_date' in entry
        assert 'display_date_formatted' in entry
        assert 'years_since' in entry
        assert 'milestone_year' in entry
        assert 'is_milestone' in entry


def test_recurring_event_display_date_in_api(test_client, init_database):
    """Test that recurring events show the correct display_date."""
    # Get the birthday entry (recurring)
    response = test_client.get('/api/data')
    data = json.loads(response.data)
    
    birthday_entry = next((e for e in data['entries'] if e['category']['name'] == 'Birthday'), None)
    assert birthday_entry is not None
    
    # The original date is 2021-05-20
    assert birthday_entry['date'] == '2021-05-20'
    
    # Display date should be in current or next year (depending on whether it's passed)
    display_date = date.fromisoformat(birthday_entry['display_date'])
    today = date.today()
    
    # Display date should be either this year or next year
    assert display_date.year in [today.year, today.year + 1]
    assert display_date.month == 5
    assert display_date.day == 20
    
    # Check milestone info
    assert birthday_entry['years_since'] is not None
    expected_years = display_date.year - 2021
    assert birthday_entry['years_since'] == expected_years


def test_non_recurring_event_display_date_in_api(test_client, init_database):
    """Test that non-recurring events show the original date as display_date."""
    # Add a non-recurring entry
    category = db.session.query(Category).filter_by(name="Release").first()
    entry = Entry(
        date="2023-06-15",
        category_id=category.id,
        title="Past Release",
        description="A past release"
    )
    db.session.add(entry)
    db.session.commit()
    
    response = test_client.get('/api/data')
    data = json.loads(response.data)
    
    release_entry = next((e for e in data['entries'] if e['title'] == 'Past Release'), None)
    assert release_entry is not None
    
    # For non-recurring, display_date should equal date
    assert release_entry['date'] == '2023-06-15'
    assert release_entry['display_date'] == '2023-06-15'
    
    # No milestone info for non-recurring
    assert release_entry['years_since'] is None
    assert release_entry['milestone_year'] is None
    assert release_entry['is_milestone'] is False
