from . import db

# Validation constants
class QuoteConstants:
    MAX_TEXT_LENGTH = 1000
    MAX_AUTHOR_LENGTH = 200
    MAX_CATEGORY_LENGTH = 100
    MAX_URL_LENGTH = 1000

class CategoryConstants:
    MAX_NAME_LENGTH = 100
    MAX_SYMBOL_LENGTH = 10
    MAX_COLOR_HEX_LENGTH = 10

class EntryConstants:
    MAX_DATE_LENGTH = 100
    MAX_TITLE_LENGTH = 200
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_IMAGE_FILENAME_LENGTH = 100
    MAX_URL_LENGTH = 1000

# Common constants
MAX_LAST_UPDATED_BY_LENGTH = 130

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(CategoryConstants.MAX_NAME_LENGTH), unique=True, nullable=False)
    symbol = db.Column(db.String(CategoryConstants.MAX_SYMBOL_LENGTH), nullable=False)
    color_hex = db.Column(db.String(CategoryConstants.MAX_COLOR_HEX_LENGTH), nullable=False)
    repeat_annually = db.Column(db.Boolean, default=False, nullable=False)
    display_celebration = db.Column(db.Boolean, default=False, nullable=False)
    is_protected = db.Column(db.Boolean, default=False, nullable=False)
    last_updated_by = db.Column(db.String(MAX_LAST_UPDATED_BY_LENGTH), nullable=True)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(EntryConstants.MAX_DATE_LENGTH), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('entries', lazy=True))
    title = db.Column(db.String(EntryConstants.MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.String(EntryConstants.MAX_DESCRIPTION_LENGTH), nullable=True)
    image_filename = db.Column(db.String(EntryConstants.MAX_IMAGE_FILENAME_LENGTH), nullable=True)
    url = db.Column(db.String(EntryConstants.MAX_URL_LENGTH), nullable=True)
    cancelled = db.Column(db.Boolean, nullable=False, default=False)
    last_updated_by = db.Column(db.String(MAX_LAST_UPDATED_BY_LENGTH), nullable=True)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(QuoteConstants.MAX_TEXT_LENGTH), nullable=False)
    author = db.Column(db.String(QuoteConstants.MAX_AUTHOR_LENGTH), nullable=False)
    category = db.Column(db.String(QuoteConstants.MAX_CATEGORY_LENGTH), nullable=True)
    url = db.Column(db.String(QuoteConstants.MAX_URL_LENGTH), nullable=True)
    last_updated_by = db.Column(db.String(MAX_LAST_UPDATED_BY_LENGTH), nullable=True)
    last_shown = db.Column(db.Date, nullable=True, index=True)
