from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from .config import Config
import os.path


db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import init_app as init_routes
    init_routes(app)
        
    from .routes_grafana import init_grafana_routes
    init_grafana_routes(app)

    from .helpers import create_upload_folder
    create_upload_folder(app.config['UPLOAD_FOLDER'])

    with app.app_context():
        if not os.path.exists(app.config['SQLALCHEMY_DATABASE_URI'].split('///')[-1]):
            db.create_all()  # Create the database file and tables if not exists
        upgrade() # Apply any pending migrations
 
    return app
