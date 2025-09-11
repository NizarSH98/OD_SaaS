#!/usr/bin/env python3
"""
WSGI entry point for production deployment.
This file is used by WSGI servers like Gunicorn to serve the Flask application.
"""

from app import create_app

# Create the Flask application instance
application = create_app()

if __name__ == "__main__":
    # This allows running the WSGI file directly for testing
    application.run(host='0.0.0.0', port=5000, debug=False)
