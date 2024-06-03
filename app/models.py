from . import db

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(1000), nullable=True)
    image_filename = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    last_updated_by = db.Column(db.String(130), nullable=True)

    # Define category choices
    CATEGORIES = ['cake', 'birthday', 'release', 'custom']
