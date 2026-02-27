from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
from flask_apscheduler import APScheduler
from .config import Config
import logging

db = SQLAlchemy()
migrate = Migrate()
scheduler = APScheduler()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    scheduler.init_app(app)

    # Initialize traditional routes
    from .routes import init_app as init_routes
    init_routes(app, scheduler)
        
    from .routes_grafana import init_grafana_routes
    init_grafana_routes(app)

    from .routes_categories import init_categories_routes
    init_categories_routes(app)

    from .routes_quotes import init_quote_routes
    init_quote_routes(app)

    from .routes_maintenance import init_maintenance_routes
    init_maintenance_routes(app)
    
    # Initialize API with Swagger documentation
    from .api import init_api
    api = init_api(app)
    
    # Import API route modules to register them with namespaces
    from . import (
        api_routes_entries, api_routes_categories, api_routes_quotes,
        api_routes_grafana, api_routes_giphy, api_routes_maintenance
    )

    with app.app_context():

        if not app.config['TESTING']:
            from .helpers import create_upload_folder
            create_upload_folder(app.config['UPLOAD_FOLDER'])
            scheduler.start()
        
        upgrade() # Apply any pending migrations
    
    return app
