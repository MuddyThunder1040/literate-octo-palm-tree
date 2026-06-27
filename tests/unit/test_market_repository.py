from datetime import datetime, timezone
from decimal import Decimal

from app_services.market_repository import MarketRepository, serialize_snapshot


def _sample_row():
    return {
        "symbol": "BTCUSDT",
        "observed_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
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


def test_serialize_snapshot_converts_decimals():
    result = serialize_snapshot(_sample_row())
    assert result["symbol"] == "BTCUSDT"
    assert isinstance(result["price"], float)
    assert result["price"] == 50000.0
    assert result["observed_at"] == "2024-01-01T00:00:00+00:00"


def test_serialize_snapshot_handles_none():
    row = _sample_row()
    row["price_change"] = None
    result = serialize_snapshot(row)
    assert result["price_change"] is None


def test_repository_not_ready_by_default():
    repo = MarketRepository()
    assert repo.ready is False
    assert repo.session is None


def test_repository_health_when_not_ready():
    repo = MarketRepository()
    health = repo.health()
    assert health["ready"] is False
    assert "hosts" in health
    assert "port" in health


def test_repository_returns_empty_when_not_ready():
    repo = MarketRepository()
    assert repo.latest() == []
    assert repo.history("BTCUSDT") == []
    assert repo.save_snapshots([]) == []
