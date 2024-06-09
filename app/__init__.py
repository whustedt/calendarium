from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from .config import Config

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

    from .routes_categories import init_categories_routes
    init_categories_routes(app)

    with app.app_context():

        if not app.config['TESTING']:
            from .helpers import create_upload_folder
            create_upload_folder(app.config['UPLOAD_FOLDER'])

        upgrade() # Apply any pending migrations
 
    return app
