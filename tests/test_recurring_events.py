"""Tests for recurring event functionality with display_date and milestones."""
import pytest
from datetime import date, timedelta
from app import db
from app.models import Entry, Category
from app.helpers import get_entry_data


def test_recurring_event_display_date_current_year(test_client, init_database):
    """
    GIVEN a recurring event with a date earlier this year
    WHEN get_entry_data is called
    THEN the display_date should be this year
    """
    category = db.session.query(Category).filter_by(name="Birthday").first()
    
    # Create an entry with original date from 1990, but month/day haven't passed yet this year
    today = date.today()
    future_month_day = today + timedelta(days=30)
    original_date = date(1990, future_month_day.month, min(future_month_day.day, 28))
    
    entry = Entry(
        date=original_date.isoformat(),
        category_id=category.id,
        title="Test Birthday",
        description="Test"
    )
    db.session.add(entry)
    db.session.commit()
    
    data = get_entry_data(db)
    
    # Find our entry
    test_entry = next((e for e in data['entries'] if e['title'] == "Test Birthday"), None)
    assert test_entry is not None
    assert test_entry['date'] == original_date.isoformat()
    # Display date should be this year since the month/day hasn't passed
    assert test_entry['display_date'].startswith(str(today.year))


def test_recurring_event_display_date_next_year(test_client, init_database):
    """
    GIVEN a recurring event with a date that has already passed this year
    WHEN get_entry_data is called
    THEN the display_date should be next year
    """
    category = db.session.query(Category).filter_by(name="Birthday").first()
    
    # Create an entry with a date that has passed this year
    today = date.today()
    past_month_day = today - timedelta(days=30)
    original_date = date(1990, past_month_day.month, min(past_month_day.day, 28))
    
    entry = Entry(
        date=original_date.isoformat(),
        category_id=category.id,
        title="Past Birthday",
        description="Test"
    )
    db.session.add(entry)
    db.session.commit()
    
    data = get_entry_data(db)
    
    # Find our entry
    test_entry = next((e for e in data['entries'] if e['title'] == "Past Birthday"), None)
    assert test_entry is not None
    assert test_entry['date'] == original_date.isoformat()
    # Display date should be next year since the date has passed
    assert test_entry['display_date'].startswith(str(today.year + 1))


def test_anniversary_years_calculation(test_client, init_database):
    """
    GIVEN a recurring event from 1990
    WHEN get_entry_data is called
    THEN anniversary_years should be correctly calculated
    """
    category = db.session.query(Category).filter_by(name="Birthday").first()
    
    # Create an entry from 1990
    today = date.today()
    future_month_day = today + timedelta(days=30)
    original_date = date(1990, future_month_day.month, min(future_month_day.day, 28))
    
    entry = Entry(
        date=original_date.isoformat(),
        category_id=category.id,
        title="Anniversary Birthday",
        description="Test"
    )
    db.session.add(entry)
    db.session.commit()
    
    data = get_entry_data(db)
    
    test_entry = next((e for e in data['entries'] if e['title'] == "Anniversary Birthday"), None)
    assert test_entry is not None
    assert test_entry['anniversary_years'] == today.year - 1990


def test_milestone_detection(test_client, init_database):
    """
    GIVEN recurring events at various anniversary years
    WHEN get_entry_data is called
    THEN milestone anniversaries should be correctly identified
    """
    category = db.session.query(Category).filter_by(name="Birthday").first()
    
    today = date.today()
    future_month_day = today + timedelta(days=30)
    
    # Test various milestone years
    # 5th anniversary
    date_5_years = date(today.year - 5, future_month_day.month, min(future_month_day.day, 28))
    # 10th anniversary
    date_10_years = date(today.year - 10, future_month_day.month, min(future_month_day.day, 28))
    # 7th anniversary (not a milestone)
    date_7_years = date(today.year - 7, future_month_day.month, min(future_month_day.day, 28))
    
    entries = [
        Entry(date=date_5_years.isoformat(), category_id=category.id, title="5 year", description="Test"),
        Entry(date=date_10_years.isoformat(), category_id=category.id, title="10 year", description="Test"),
        Entry(date=date_7_years.isoformat(), category_id=category.id, title="7 year", description="Test"),
    ]
    db.session.add_all(entries)
    db.session.commit()
    
    data = get_entry_data(db)
    
    entry_5 = next((e for e in data['entries'] if e['title'] == "5 year"), None)
    entry_10 = next((e for e in data['entries'] if e['title'] == "10 year"), None)
    entry_7 = next((e for e in data['entries'] if e['title'] == "7 year"), None)
    
    assert entry_5 is not None
    assert entry_5['anniversary_years'] == 5
    assert entry_5['is_milestone'] is True
    
    assert entry_10 is not None
    assert entry_10['anniversary_years'] == 10
    assert entry_10['is_milestone'] is True
    
    assert entry_7 is not None
    assert entry_7['anniversary_years'] == 7
    assert entry_7['is_milestone'] is False


def test_non_recurring_event_no_anniversary(test_client, init_database):
    """
    GIVEN a non-recurring event
    WHEN get_entry_data is called
    THEN anniversary_years and is_milestone should be None/False
    """
    category = db.session.query(Category).filter_by(name="Release").first()
    
    entry = Entry(
        date="2023-05-20",
        category_id=category.id,
        title="Release Event",
        description="Test"
    )
    db.session.add(entry)
    db.session.commit()
    
    data = get_entry_data(db)
    
    test_entry = next((e for e in data['entries'] if e['title'] == "Release Event"), None)
    assert test_entry is not None
    assert test_entry['anniversary_years'] is None
    assert test_entry['is_milestone'] is False


def test_recurring_events_sorted_by_display_date(test_client, init_database):
    """
    GIVEN multiple recurring events
    WHEN get_entry_data is called
    THEN entries should be sorted by display_date, not original date
    """
    category = db.session.query(Category).filter_by(name="Birthday").first()
    
    today = date.today()
    
    # Create events with different original years but same month/day pattern
    # One in the past (should appear next year)
    past_date = today - timedelta(days=10)
    entry_past = Entry(
        date=date(1980, past_date.month, min(past_date.day, 28)).isoformat(),
        category_id=category.id,
        title="Past Event",
        description="Test"
    )
    
    # One in the future (should appear this year)
    future_date = today + timedelta(days=10)
    entry_future = Entry(
        date=date(1990, future_date.month, min(future_date.day, 28)).isoformat(),
        category_id=category.id,
        title="Future Event",
        description="Test"
    )
    
    db.session.add_all([entry_past, entry_future])
    db.session.commit()
    
    data = get_entry_data(db)
    
    # Find indices of our entries
    past_idx = next((i for i, e in enumerate(data['entries']) if e['title'] == "Past Event"), None)
    future_idx = next((i for i, e in enumerate(data['entries']) if e['title'] == "Future Event"), None)
    
    assert past_idx is not None
    assert future_idx is not None
    
    # Future event (this year) should come before past event (next year)
    assert future_idx < past_idx
