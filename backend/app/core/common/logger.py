import logging
import sys
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

def setup_logger(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        stream=sys.stdout,
    )
    logger = logging.getLogger("astro")
    return logger

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger=None):
        super().__init__(app)
        self.logger = logger or logging.getLogger("astro")

    async def dispatch(self, request: Request, call_next):
        self.logger.info(f"➡️  {request.method} {request.url.path}")
        response = await call_next(request)
        self.logger.info(f"⬅️  {response.status_code} {request.url.path}")
        return response