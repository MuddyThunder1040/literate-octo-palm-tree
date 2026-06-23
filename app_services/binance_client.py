from decimal import Decimal
import json
import httpx

from app_config import settings


def _to_decimal(value):
    return Decimal(str(value))


def _normalize_symbol(symbol):
    return symbol.strip().upper()


class BinanceClient:
    def __init__(self, base_url=None, timeout=None):
        self.base_url = (base_url or settings.binance_base_url).rstrip("/")
        self.timeout = timeout or settings.request_timeout_seconds

    async def get_24hr_tickers(self, symbols):
        normalized_symbols = [_normalize_symbol(symbol) for symbol in symbols if symbol.strip()]
        params = {}
        if len(normalized_symbols) == 1:
            params["symbol"] = normalized_symbols[0]
        elif normalized_symbols:
            params["symbols"] = json.dumps(normalized_symbols)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get("/api/v3/ticker/24hr", params=params)
            response.raise_for_status()
            payload = response.json()

        rows = payload if isinstance(payload, list) else [payload]
        return [self._map_ticker(row) for row in rows]

    def _map_ticker(self, row):
        return {
            "symbol": row["symbol"],
            "price": _to_decimal(row["lastPrice"]),
            "price_change": _to_decimal(row["priceChange"]),
            "price_change_percent": _to_decimal(row["priceChangePercent"]),
            "weighted_avg_price": _to_decimal(row["weightedAvgPrice"]),
            "high_price": _to_decimal(row["highPrice"]),
            "low_price": _to_decimal(row["lowPrice"]),
            "volume": _to_decimal(row["volume"]),
            "quote_volume": _to_decimal(row["quoteVolume"]),
            "open_time": int(row["openTime"]),
            "close_time": int(row["closeTime"]),
            "trade_count": int(row["count"]),
        }
