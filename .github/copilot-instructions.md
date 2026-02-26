# Copilot Instructions for Calendarium

## Project Overview

Calendarium is a Flask-based web application for managing events and visualizing them on a dynamic timeline. It includes:
- Event management with categories
- Quote management system
- Grafana integration for data visualization
- Giphy API integration
- Timeline visualization with Flickity library

## Technology Stack

- **Backend**: Python 3.13, Flask
- **Database**: SQLAlchemy with Flask-Migrate (Alembic) for migrations
- **Testing**: pytest
- **Frontend**: HTML templates (Jinja2), vanilla JavaScript, CSS
- **Deployment**: Docker, Gunicorn WSGI server
- **External APIs**: Grafana Simple JSON Datasource, Giphy API

## Development Practices

### Code Style
- Follow existing code patterns and conventions in the repository
- Use consistent naming: snake_case for Python functions and variables
- Keep model validation constants in dedicated classes (e.g., `QuoteConstants`, `CategoryConstants`, `EntryConstants`)
- Maintain separation of concerns: routes are split into logical modules (`routes.py`, `routes_grafana.py`, `routes_quotes.py`, `routes_categories.py`, `routes_maintenance.py`)

### Testing
- All changes should maintain or improve test coverage
- Run tests with: `pytest` or `pytest -v` for verbose output
- Tests are located in the `tests/` directory
- Use test fixtures defined in `conftest.py`
- Ensure all 67 existing tests pass before submitting changes
- Test structure follows: `test_<feature>.py` naming convention

### Database Migrations
- Use Flask-Migrate for all database schema changes
- Generate migrations with: `flask db migrate -m "Description of changes"`
- Apply migrations with: `flask db upgrade`
- Never modify existing migration files; create new ones instead
- Review auto-generated migrations before applying them

### Running the Application

**Development:**
```bash
flask run --debug
```

**Production:**
```bash
gunicorn -w 4 -b "127.0.0.1:5000" "app:create_app()"
```

**Docker:**
```bash
docker-compose up --build
```

### Environment Variables
- Use `.env` file for local development (excluded from git)
- Required: `GIPHY_API_TOKEN` for Giphy integration
- Database path: `/app/data/data.db` (configurable via `SQLALCHEMY_DATABASE_URI`)

## Important Constraints

### Licensing
- This project uses GPLv3 license
- Includes Flickity library (GPLv3)
- Any modifications must comply with GPLv3
- Maintain attribution for third-party assets (e.g., Noun Project icons)

### Security
- Never commit secrets or API tokens to the repository
- Use environment variables for sensitive configuration
- Track last_updated_by field using `request.remote_addr` for audit trails

### API Endpoints
- Grafana endpoints under `/grafana/*` must maintain Simple JSON Datasource compatibility
- Quote endpoints support both JSON and HTML responses
- Category management includes protection for system categories (`is_protected` flag)
- Entry management tracks cancellation status and supports annual repetition

## File Organization

```
app/
├── __init__.py          # App factory, initialization
├── config.py            # Configuration classes (Config, TestConfig)
├── models.py            # Database models (Entry, Category, Quote)
├── helpers.py           # Utility functions
├── routes*.py           # Route handlers (modularized by feature)
├── static/              # CSS, JavaScript, assets
└── templates/           # Jinja2 HTML templates

tests/                   # Test suite
migrations/              # Alembic database migrations
```

## Common Tasks

### Adding a New Route
1. Determine the appropriate routes file based on feature area
2. Add route handler following existing patterns
3. Update relevant tests in `tests/`
4. Ensure proper error handling and validation

### Adding a New Model Field
1. Update model class in `models.py`
2. Add validation constants if applicable
3. Generate migration: `flask db migrate -m "Add field description"`
4. Update affected routes and helpers
5. Add or update tests

### Adding Dependencies
1. Add to `requirements.txt`
2. Update Dockerfile if needed
3. Test in Docker build

## Testing Guidelines
- Use `test_client` fixture for HTTP request testing
- Use `init_database` fixture for tests requiring database state
- Mock external API calls (Giphy, etc.)
- Test both success and error cases
- Include edge cases and validation scenarios
