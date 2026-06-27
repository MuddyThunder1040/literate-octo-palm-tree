import pytest
import respx
import httpx
from unittest.mock import patch, MagicMock, AsyncMock

from app_services.market_repository import market_repository


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
    raw = [{
        "symbol": "BTCUSDT",
        "lastPrice": "50000.00",
        "priceChange": "1000.00",
        "priceChangePercent": "2.04",
        "weightedAvgPrice": "49500.00",
        "highPrice": "51000.00",
        "lowPrice": "48000.00",
        "volume": "100.5",
        "quoteVolume": "5000000.00",
        "openTime": 1700000000000,
        "closeTime": 1700086400000,
        "count": 50000,
    }]
    with respx.mock(base_url="https://data-api.binance.vision") as mock:
        mock.get("/api/v3/ticker/24hr").mock(
            return_value=httpx.Response(200, json=raw)
        )
        r = client.get("/api/crypto/markets?symbols=BTCUSDT")
    assert r.status_code == 200
    assert r.json()[0]["symbol"] == "BTCUSDT"


def test_crypto_markets_upstream_error(client):
    with respx.mock(base_url="https://data-api.binance.vision") as mock:
        mock.get("/api/v3/ticker/24hr").mock(
            return_value=httpx.Response(503)
        )
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
    raw = [{
        "symbol": "BTCUSDT",
        "lastPrice": "50000.00",
        "priceChange": "0.00",
        "priceChangePercent": "0.00",
        "weightedAvgPrice": "50000.00",
        "highPrice": "51000.00",
        "lowPrice": "49000.00",
        "volume": "100.0",
        "quoteVolume": "5000000.00",
        "openTime": 1700000000000,
        "closeTime": 1700086400000,
        "count": 1000,
    }]
    with respx.mock(base_url="https://data-api.binance.vision") as mock:
        mock.get("/api/v3/ticker/24hr").mock(
            return_value=httpx.Response(200, json=raw)
        )
        r = client.post("/api/crypto/ingest?symbols=BTCUSDT")
    assert r.status_code == 200
    body = r.json()
    assert body["storage_ready"] is False
    assert body["count"] == 1
