from fastapi import HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from httpx import HTTPError

from app_runtime import create_app
from app_services.cluster_health import get_cluster_health
from app_services.crypto_market import (
    fetch_market_data,
    get_latest_prices,
    get_market_status,
    get_price_history,
    ingest_market_data,
)
from app_views import render_crypto_dashboard

app = create_app()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_crypto_dashboard(request)


@app.get("/api/cluster/health")
def cluster_health():
    return get_cluster_health()


@app.get("/api/crypto/status")
def crypto_status():
    return get_market_status()


@app.get("/api/crypto/markets")
async def crypto_markets(symbols: str | None = Query(default=None)):
    try:
        return await fetch_market_data(symbols)
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Binance request failed: {exc}") from exc


@app.post("/api/crypto/ingest")
async def crypto_ingest(symbols: str | None = Query(default=None)):
    try:
        return await ingest_market_data(symbols)
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Binance request failed: {exc}") from exc


@app.get("/api/crypto/latest")
def crypto_latest(symbols: str | None = Query(default=None)):
    symbol_list = symbols.split(",") if symbols else None
    return get_latest_prices(symbol_list)


@app.get("/api/crypto/history/{symbol}")
def crypto_history(symbol: str, limit: int = Query(default=100, ge=1, le=500)):
    return get_price_history(symbol, limit)


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
