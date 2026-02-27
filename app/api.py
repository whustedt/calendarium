from flask_restx import Api
from .api_models import (
    entries_ns, categories_ns, quotes_ns, 
    grafana_ns, maintenance_ns, giphy_ns
)

def init_api(app):
    """Initialize Flask-RESTX API with documentation"""
    
    api = Api(
        app,
        version='1.0',
        title='Calendarium API',
        description='A comprehensive calendar and event management system with timeline visualization, category management, quote system, and Grafana integration.',
        doc='/api/docs/',  # Swagger UI will be available at /api/docs/
        prefix='/api/v1',  # All API routes will be prefixed with /api/v1
        validate=True,
        ordered=True,
        authorizations={
            'apikey': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'X-API-Key'
            }
        }
    )
    
    # Add namespaces to API
    api.add_namespace(entries_ns, path='/entries')
    api.add_namespace(categories_ns, path='/categories')
    api.add_namespace(quotes_ns, path='/quotes')
    api.add_namespace(grafana_ns, path='/grafana')
    api.add_namespace(giphy_ns, path='/giphy')
    api.add_namespace(maintenance_ns, path='/maintenance')
    
    return api
