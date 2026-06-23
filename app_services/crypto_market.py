import asyncio
from datetime import datetime, timezone

from app_config import settings
from app_services.binance_client import BinanceClient
from app_services.market_repository import market_repository, serialize_snapshot

binance_client = BinanceClient()
_last_ingest = None
_last_error = None
_poller_task = None


def _serialize_ticker(ticker, observed_at=None):
    row = {
        key: float(value) if hasattr(value, "as_tuple") else value
        for key, value in ticker.items()
    }
    if observed_at:
        row["observed_at"] = observed_at.isoformat()
    return row


def normalize_symbols(symbols=None):
    if not symbols:
        return settings.default_symbols
    if isinstance(symbols, str):
        symbols = symbols.split(",")
    return [symbol.strip().upper() for symbol in symbols if symbol.strip()]


async def fetch_market_data(symbols=None):
    tickers = await binance_client.get_24hr_tickers(normalize_symbols(symbols))
    return [_serialize_ticker(ticker) for ticker in tickers]


async def ingest_market_data(symbols=None):
    global _last_error, _last_ingest
    tickers = await binance_client.get_24hr_tickers(normalize_symbols(symbols))
    saved_rows = market_repository.save_snapshots(tickers)
    _last_ingest = datetime.now(timezone.utc)
    _last_error = None

    if saved_rows:
        rows = [serialize_snapshot(row) for row in saved_rows]
        return {
            "storage_ready": True,
            "count": len(rows),
            "data": rows,
        }

    rows = [_serialize_ticker(ticker, _last_ingest) for ticker in tickers]
    return {
        "storage_ready": market_repository.ready,
        "count": len(rows),
        "data": rows,
    }


def get_latest_prices(symbols=None):
    return market_repository.latest(normalize_symbols(symbols) if symbols else None)


def get_price_history(symbol, limit=100):
    safe_limit = max(1, min(limit, 500))
    return market_repository.history(symbol, safe_limit)


def get_market_status():
    return {
        "binance_base_url": settings.binance_base_url,
        "default_symbols": settings.default_symbols,
        "last_ingest_at": _last_ingest.isoformat() if _last_ingest else None,
        "last_error": _last_error,
        "auto_ingest_seconds": settings.auto_ingest_seconds,
        "cassandra": market_repository.health(),
    }


def start_market_services():
    market_repository.connect()
    if settings.auto_ingest_seconds > 0:
        start_auto_ingest()


def stop_market_services():
    global _poller_task
    if _poller_task:
        _poller_task.cancel()
        _poller_task = None
    market_repository.close()


def start_auto_ingest():
    global _poller_task
    if _poller_task and not _poller_task.done():
        return
    _poller_task = asyncio.create_task(_auto_ingest_loop())


async def _auto_ingest_loop():
    global _last_error
    while True:
        try:
            await ingest_market_data(settings.default_symbols)
        except Exception as exc:
            _last_error = str(exc)
        await asyncio.sleep(settings.auto_ingest_seconds)
