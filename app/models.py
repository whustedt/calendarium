from . import db

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(1000), nullable=True)

    # Define category choices
    CATEGORIES = ['cake', 'birthday', 'release', 'custom']
