from . import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    color_hex = db.Column(db.String(10), nullable=False)
    repeat_annually = db.Column(db.Boolean, default=False, nullable=False)
    display_celebration = db.Column(db.Boolean, default=False, nullable=False)
    is_protected = db.Column(db.Boolean, default=False, nullable=False)
    last_updated_by = db.Column(db.String(130), nullable=True)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('entries', lazy=True))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    image_filename = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    cancelled = db.Column(db.Boolean, nullable=False, default=False)
    last_updated_by = db.Column(db.String(130), nullable=True)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    last_updated_by = db.Column(db.String(130), nullable=True)
