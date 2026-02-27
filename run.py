#!/usr/bin/env python3
"""
Flask application entry point for the Calendarium project.
"""
import os
from app import create_app

# Create Flask application instance
app = create_app()

if __name__ == '__main__':
    # Run the application in debug mode for development
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
