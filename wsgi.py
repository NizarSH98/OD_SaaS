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
    import os
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=False)
