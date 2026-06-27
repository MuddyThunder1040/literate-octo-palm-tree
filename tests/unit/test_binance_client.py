from decimal import Decimal
import pytest
import respx
import httpx

from app_services.binance_client import BinanceClient, _to_decimal, _normalize_symbol


def test_normalize_symbol():
    assert _normalize_symbol("  btcusdt  ") == "BTCUSDT"
    assert _normalize_symbol("ethusdt") == "ETHUSDT"


def test_to_decimal():
    assert _to_decimal("50000.12") == Decimal("50000.12")
    assert _to_decimal(42) == Decimal("42")


def _raw_ticker(symbol="BTCUSDT"):
    return {
        "symbol": symbol,
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
    }


def test_map_ticker():
    client = BinanceClient()
    result = client._map_ticker(_raw_ticker())
    assert result["symbol"] == "BTCUSDT"
    assert result["price"] == Decimal("50000.00")
    assert result["high_price"] == Decimal("51000.00")
    assert result["trade_count"] == 50000
    assert result["open_time"] == 1700000000000


@pytest.mark.asyncio
async def test_get_24hr_tickers_single():
    with respx.mock(base_url="https://data-api.binance.vision") as mock:
        mock.get("/api/v3/ticker/24hr").mock(
            return_value=httpx.Response(200, json=_raw_ticker())
        )
        client = BinanceClient()
        result = await client.get_24hr_tickers(["BTCUSDT"])

    assert len(result) == 1
    assert result[0]["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_get_24hr_tickers_multiple():
    raw = [_raw_ticker("BTCUSDT"), _raw_ticker("ETHUSDT")]
    with respx.mock(base_url="https://data-api.binance.vision") as mock:
        mock.get("/api/v3/ticker/24hr").mock(
            return_value=httpx.Response(200, json=raw)
        )
        client = BinanceClient()
        result = await client.get_24hr_tickers(["BTCUSDT", "ETHUSDT"])

    assert len(result) == 2
