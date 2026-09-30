"""Passenger WSGI entrypoint for the FastAPI CRM backend on cPanel.

Passenger exposes a WSGI interface, while FastAPI is ASGI. a2wsgi provides
an ASGI-to-WSGI adapter so the same production FastAPI application can run
behind cPanel Passenger without changing the API routes.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# cPanel does not automatically load a project .env file into Passenger's
# process environment. Load the preserved production .env before importing
# the FastAPI application so MongoDB/CORS/security settings are available.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)
except Exception:
    # Keep startup compatible if python-dotenv is unavailable; dependency
    # installation is handled by the cPanel deployment configuration.
    pass

from a2wsgi import ASGIMiddleware
from server import app

application = ASGIMiddleware(app)
