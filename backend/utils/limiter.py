"""
Shared rate limiter instance — استخدام مركزي لـ slowapi
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Global limiter — key by IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
