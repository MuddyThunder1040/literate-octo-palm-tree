"""
Integration tests — run against live dev deployment.
Set APP_URL env var (default: http://localhost:8001).
"""
import os
import httpx
import pytest

BASE = os.getenv("APP_URL", "http://localhost:8001")


def test_health():
    r = httpx.get(f"{BASE}/api/cluster/health", timeout=10)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_crypto_status():
    r = httpx.get(f"{BASE}/api/crypto/status", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "cassandra" in body
    assert body["cassandra"]["ready"] is True


def test_ingest_and_latest():
    r = httpx.post(f"{BASE}/api/crypto/ingest?symbols=BTCUSDT", timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["storage_ready"] is True
    assert body["count"] >= 1

    r = httpx.get(f"{BASE}/api/crypto/latest?symbols=BTCUSDT", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert data[0]["symbol"] == "BTCUSDT"


def test_price_history():
    r = httpx.get(f"{BASE}/api/crypto/history/BTCUSDT", timeout=10)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)


def test_live_market_data():
    r = httpx.get(f"{BASE}/api/crypto/markets?symbols=ETHUSDT", timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert float(data[0]["price"]) > 0
