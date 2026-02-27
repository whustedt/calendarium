from flask import request, jsonify, current_app
from flask_restx import Resource
import requests
import os
from .api_models import (
    giphy_ns, giphy_search_response_model, 
    giphy_url_response_model, giphy_enabled_response_model, 
    error_model
)

@giphy_ns.route('/search')
class GiphySearchAPI(Resource):
    @giphy_ns.doc('search_gifs')
    @giphy_ns.param('q', 'Search query for GIFs', type=str, required=True)
    @giphy_ns.param('limit', 'Number of results to return (default: 15)', type=int, required=False)
    @giphy_ns.marshal_with(giphy_search_response_model)
    @giphy_ns.response(400, 'Query parameter required', error_model)
    @giphy_ns.response(500, 'External API error', error_model)
    def get(self):
        """Search GIFs using Giphy API (server-side)"""
        query = request.args.get('q')
        if not query:
            return {'error': 'Query parameter "q" is required'}, 400
        
        limit = request.args.get('limit', 15, type=int)
        
        try:
            response = requests.get(
                'https://api.giphy.com/v1/gifs/search',
                params={
                    'api_key': os.getenv('GIPHY_API_TOKEN'),
                    'q': query,
                    'limit': limit
                }
            )
            response.raise_for_status()
            return {'data': response.json()['data']}
        except requests.RequestException as e:
            current_app.logger.error(f"Giphy API request failed: {e}")
            return {'error': 'Failed to fetch GIFs from Giphy'}, 500

@giphy_ns.route('/url')
class GiphyUrlAPI(Resource):
    @giphy_ns.doc('get_giphy_url')
    @giphy_ns.param('q', 'Search query for GIFs', type=str, required=True)
    @giphy_ns.param('limit', 'Number of results to return (default: 15)', type=int, required=False)
    @giphy_ns.marshal_with(giphy_url_response_model)
    @giphy_ns.response(400, 'Query parameter required', error_model)
    def get(self):
        """Get Giphy API URL with embedded API key (for client-side requests)"""
        query = request.args.get('q')
        if not query:
            return {'error': 'Query parameter "q" is required'}, 400
        
        limit = request.args.get('limit', 15, type=int)
        
        url = f"https://api.giphy.com/v1/gifs/search?api_key={os.getenv('GIPHY_API_TOKEN')}&q={query}&limit={limit}"
        return {'url': url}

@giphy_ns.route('/enabled')
class GiphyEnabledAPI(Resource):
    @giphy_ns.doc('check_giphy_enabled')
    @giphy_ns.marshal_with(giphy_enabled_response_model)
    def get(self):
        """Check if Giphy integration is enabled"""
        api_token = os.getenv('GIPHY_API_TOKEN')
        enabled = bool(api_token and api_token.strip())
        return {'enabled': enabled}
