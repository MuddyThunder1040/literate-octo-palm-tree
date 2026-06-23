import time

from starlette.middleware.base import BaseHTTPMiddleware


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started_at) * 1000
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
        return response
