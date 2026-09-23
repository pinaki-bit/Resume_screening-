"""
backend/app/rate_limiter.py

Shared rate limiter instance.

Extracted to its own module to avoid circular imports between
app.main and the API routers that need to use the limiter decorator.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter instance — imported by both app.main and API routers.
limiter = Limiter(key_func=get_remote_address)
