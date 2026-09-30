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

from a2wsgi import ASGIMiddleware
from server import app

application = ASGIMiddleware(app)
