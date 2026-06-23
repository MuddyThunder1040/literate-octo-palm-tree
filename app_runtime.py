from contextlib import asynccontextmanager

from fastapi import FastAPI

from app_middleware import RequestTimingMiddleware
from app_services.crypto_market import start_market_services, stop_market_services


@asynccontextmanager
async def lifespan(app):
    start_market_services()
    yield
    stop_market_services()


def create_app():
    app = FastAPI(title="Crypto Trading Monitor", lifespan=lifespan)
    app.add_middleware(RequestTimingMiddleware)
    return app
