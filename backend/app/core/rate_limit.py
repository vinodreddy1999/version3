from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# In-memory storage: fine for a single backend instance (the default
# docker-compose/local setup). A multi-replica deployment needs a shared
# backend (e.g. Redis) via storage_uri, since each process would otherwise
# track its own independent counters.
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)
