# Calendarium API Documentation

## Overview

The Calendarium application now includes a comprehensive REST API with OpenAPI/Swagger documentation. The API is built using Flask-RESTX and provides access to all major functionality.

## API Access

- **Base URL**: `/api/v1`
- **Swagger Documentation**: `/api/docs/`
- **API Spec**: `/api/docs/swagger.json`

## API Namespaces

### 1. Entries (`/api/v1/entries`)
- **GET** `/api/v1/entries/` - Get all entries and categories
- **POST** `/api/v1/entries/` - Create a new entry
- **GET** `/api/v1/entries/{id}` - Get specific entry
- **PUT** `/api/v1/entries/{id}` - Update entry
- **DELETE** `/api/v1/entries/{id}` - Delete entry
- **POST** `/api/v1/entries/{id}/toggle-cancelled` - Toggle entry cancelled state
- **POST** `/api/v1/entries/update-serial` - Update all serial entries
- **POST** `/api/v1/entries/purge-old` - Purge old entries

### 2. Categories (`/api/v1/categories`)
- **GET** `/api/v1/categories/` - List all categories
- **POST** `/api/v1/categories/` - Create category
- **GET** `/api/v1/categories/{id}` - Get specific category
- **PUT** `/api/v1/categories/{id}` - Update category
- **DELETE** `/api/v1/categories/{id}` - Delete category
- **GET** `/api/v1/categories/names` - Get category names for dropdowns

### 3. Quotes (`/api/v1/quotes`)
- **GET** `/api/v1/quotes/` - List all quotes
- **POST** `/api/v1/quotes/` - Create quote
- **GET** `/api/v1/quotes/{id}` - Get specific quote
- **PUT** `/api/v1/quotes/{id}` - Update quote
- **DELETE** `/api/v1/quotes/{id}` - Delete quote
- **GET** `/api/v1/quotes/daily` - Get daily quote
- **GET** `/api/v1/quotes/random` - Get random quote
- **GET** `/api/v1/quotes/categories` - Get quote categories

### 4. Grafana Integration (`/api/v1/grafana`)
- **GET** `/api/v1/grafana/test` - Test connection
- **POST** `/api/v1/grafana/search` - Search targets
- **POST** `/api/v1/grafana/query` - Query data
- **POST** `/api/v1/grafana/annotations` - Get annotations
- **POST** `/api/v1/grafana/tag-keys` - Get tag keys
- **POST** `/api/v1/grafana/tag-values` - Get tag values

### 5. Giphy Integration (`/api/v1/giphy`)
- **GET** `/api/v1/giphy/search` - Search GIFs
- **GET** `/api/v1/giphy/url` - Get Giphy URL
- **GET** `/api/v1/giphy/enabled` - Check if Giphy is enabled

### 6. Maintenance (`/api/v1/maintenance`)
- **GET** `/api/v1/maintenance/export` - Export data as ZIP
- **POST** `/api/v1/maintenance/import` - Import batch data
- **GET** `/api/v1/maintenance/health` - Health check
- **GET** `/api/v1/maintenance/stats` - Get statistics

## Example Usage

### Creating an Entry
```bash
curl -X POST http://localhost:5000/api/v1/entries/ \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-06-01",
    "title": "Team Meeting", 
    "description": "Weekly team sync",
    "category": "Work"
  }'
```

### Creating a Quote
```bash
curl -X POST http://localhost:5000/api/v1/quotes/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Innovation distinguishes between a leader and a follower.",
    "author": "Steve Jobs",
    "category": "innovation"
  }'
```

### Getting Daily Quote
```bash
curl http://localhost:5000/api/v1/quotes/daily?color=true
```

### Creating a Category
```bash
curl -X POST http://localhost:5000/api/v1/categories/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Work",
    "symbol": "💼",
    "color_hex": "#007bff",
    "repeat_annually": false
  }'
```

## Features

### ✅ Implemented Features

1. **Complete API Coverage**: All existing functionality is available via REST API
2. **OpenAPI/Swagger Documentation**: Interactive documentation at `/api/docs/`
3. **Proper HTTP Status Codes**: RESTful response codes (200, 201, 400, 404, 500)
4. **Request/Response Validation**: Input validation with proper error messages
5. **Consistent Error Handling**: Standardized error response format
6. **Namespace Organization**: Logical grouping of related endpoints
7. **Model Definitions**: Clear request/response schemas
8. **CORS Support**: Cross-origin requests enabled
9. **Minimal Boilerplate**: Clean implementation without pollution

### 🔧 Technical Implementation

- **Framework**: Flask-RESTX for API and documentation
- **Documentation**: Auto-generated Swagger UI
- **Validation**: Marshmallow-style model validation
- **Error Handling**: Consistent JSON error responses
- **Logging**: Proper error logging for debugging
- **Database**: SQLAlchemy ORM integration
- **Security**: Input validation and sanitization

### 🚀 Benefits

1. **Developer Experience**: Interactive API documentation
2. **Integration Ready**: Standard REST API for frontend/mobile apps
3. **Backward Compatible**: Existing HTML routes still work
4. **Maintainable**: Clear separation of concerns
5. **Testable**: Easy to write API tests
6. **Discoverable**: Self-documenting API

## Testing the API

You can test the API using:

1. **Swagger UI**: Visit `/api/docs/` for interactive testing
2. **curl**: Command line HTTP requests (see examples above)
3. **Postman**: Import the OpenAPI spec from `/api/docs/swagger.json`
4. **JavaScript**: Use fetch() or axios for frontend integration

## Next Steps

The API is now fully functional and ready for:

1. Frontend JavaScript integration
2. Mobile app development
3. Third-party integrations
4. Automated testing
5. CI/CD pipeline integration

All endpoints are documented, tested, and working correctly!
