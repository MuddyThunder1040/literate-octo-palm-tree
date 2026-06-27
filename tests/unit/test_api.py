from decimal import Decimal
from unittest.mock import patch, AsyncMock

from app_services.market_repository import market_repository


def _ticker(symbol="BTCUSDT"):
    return {
        "symbol": symbol,
        "price": Decimal("50000.00"),
        "price_change": Decimal("1000.00"),
        "price_change_percent": Decimal("2.04"),
        "weighted_avg_price": Decimal("49500.00"),
        "high_price": Decimal("51000.00"),
        "low_price": Decimal("48000.00"),
        "volume": Decimal("100.5"),
        "quote_volume": Decimal("5000000.00"),
        "open_time": 1700000000000,
        "close_time": 1700086400000,
        "trade_count": 50000,
    }


def test_health_check(client):
    r = client.get("/api/cluster/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "metrics" in body


def test_crypto_status(client):
    r = client.get("/api/crypto/status")
    assert r.status_code == 200
    body = r.json()
    assert "cassandra" in body
    assert "default_symbols" in body


def test_home_returns_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_crypto_markets_success(client):
    tickers = [_ticker()]
    with patch("app_services.crypto_market.binance_client.get_24hr_tickers",
               new_callable=AsyncMock, return_value=tickers):
        r = client.get("/api/crypto/markets?symbols=BTCUSDT")
    assert r.status_code == 200
    assert r.json()[0]["symbol"] == "BTCUSDT"


def test_crypto_markets_upstream_error(client):
    import httpx
    with patch("app_services.crypto_market.binance_client.get_24hr_tickers",
               new_callable=AsyncMock, side_effect=httpx.HTTPError("upstream down")):
        r = client.get("/api/crypto/markets?symbols=BTCUSDT")
    assert r.status_code == 502


def test_crypto_latest_no_data(client):
    with patch.object(market_repository, "latest", return_value=[]):
        r = client.get("/api/crypto/latest")
    assert r.status_code == 200
    assert r.json() == []


def test_crypto_history(client):
    with patch.object(market_repository, "history", return_value=[]):
        r = client.get("/api/crypto/history/BTCUSDT")
    assert r.status_code == 200


def test_ingest_when_cassandra_not_ready(client):
    tickers = [_ticker()]
    with patch("app_services.crypto_market.binance_client.get_24hr_tickers",
               new_callable=AsyncMock, return_value=tickers):
        r = client.post("/api/crypto/ingest?symbols=BTCUSDT")
    assert r.status_code == 200
    body = r.json()
    assert body["storage_ready"] is False
    assert body["count"] == 1
