from datetime import date, datetime, timezone
from decimal import Decimal

from app_config import settings


def _decimal_to_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def serialize_snapshot(row):
    return {
        "symbol": row["symbol"],
        "observed_at": row["observed_at"].isoformat(),
        "price": _decimal_to_float(row["price"]),
        "price_change": _decimal_to_float(row["price_change"]),
        "price_change_percent": _decimal_to_float(row["price_change_percent"]),
        "weighted_avg_price": _decimal_to_float(row["weighted_avg_price"]),
        "high_price": _decimal_to_float(row["high_price"]),
        "low_price": _decimal_to_float(row["low_price"]),
        "volume": _decimal_to_float(row["volume"]),
        "quote_volume": _decimal_to_float(row["quote_volume"]),
        "open_time": row["open_time"],
        "close_time": row["close_time"],
        "trade_count": row["trade_count"],
    }


class MarketRepository:
    def __init__(self):
        self.cluster = None
        self.session = None
        self.ready = False
        self.error = None

    def connect(self):
        try:
            from cassandra.auth import PlainTextAuthProvider
            from cassandra.cluster import Cluster
        except ImportError as exc:
            self.ready = False
            self.error = f"cassandra-driver is not installed: {exc}"
            return

        auth_provider = None
        if settings.cassandra_username and settings.cassandra_password:
            auth_provider = PlainTextAuthProvider(
                username=settings.cassandra_username,
                password=settings.cassandra_password,
            )

        try:
            self.cluster = Cluster(
                contact_points=settings.cassandra_hosts,
                port=settings.cassandra_port,
                auth_provider=auth_provider,
            )
            self.session = self.cluster.connect()
            self._ensure_schema()
            self.ready = True
            self.error = None
        except Exception as exc:
            self.ready = False
            self.error = str(exc)

    def close(self):
        if self.cluster:
            self.cluster.shutdown()
        self.cluster = None
        self.session = None
        self.ready = False

    def health(self):
        return {
            "ready": self.ready,
            "hosts": settings.cassandra_hosts,
            "port": settings.cassandra_port,
            "keyspace": settings.cassandra_keyspace,
            "error": self.error,
        }

    def _ensure_schema(self):
        replication = "{'class': 'SimpleStrategy', 'replication_factor': 3}"
        self.session.execute(
            f"""
            CREATE KEYSPACE IF NOT EXISTS {settings.cassandra_keyspace}
            WITH replication = {replication}
            """
        )
        self.session.set_keyspace(settings.cassandra_keyspace)
        self.session.execute(
            """
            CREATE TABLE IF NOT EXISTS price_ticks_by_symbol (
                symbol text,
                bucket_date date,
                observed_at timestamp,
                price decimal,
                price_change decimal,
                price_change_percent decimal,
                weighted_avg_price decimal,
                high_price decimal,
                low_price decimal,
                volume decimal,
                quote_volume decimal,
                open_time bigint,
                close_time bigint,
                trade_count int,
                PRIMARY KEY ((symbol, bucket_date), observed_at)
            ) WITH CLUSTERING ORDER BY (observed_at DESC)
            """
        )
        self.session.execute(
            """
            CREATE TABLE IF NOT EXISTS latest_prices (
                symbol text PRIMARY KEY,
                observed_at timestamp,
                price decimal,
                price_change decimal,
                price_change_percent decimal,
                weighted_avg_price decimal,
                high_price decimal,
                low_price decimal,
                volume decimal,
                quote_volume decimal,
                open_time bigint,
                close_time bigint,
                trade_count int
            )
            """
        )

    def save_snapshots(self, snapshots):
        if not self.ready:
            return []

        observed_at = datetime.now(timezone.utc)
        bucket_date = date.today()
        saved = []

        insert_tick = self.session.prepare(
            """
            INSERT INTO price_ticks_by_symbol (
                symbol, bucket_date, observed_at, price, price_change,
                price_change_percent, weighted_avg_price, high_price, low_price,
                volume, quote_volume, open_time, close_time, trade_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        )
        upsert_latest = self.session.prepare(
            """
            INSERT INTO latest_prices (
                symbol, observed_at, price, price_change, price_change_percent,
                weighted_avg_price, high_price, low_price, volume, quote_volume,
                open_time, close_time, trade_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        )

        for snapshot in snapshots:
            values = (
                snapshot["symbol"],
                bucket_date,
                observed_at,
                snapshot["price"],
                snapshot["price_change"],
                snapshot["price_change_percent"],
                snapshot["weighted_avg_price"],
                snapshot["high_price"],
                snapshot["low_price"],
                snapshot["volume"],
                snapshot["quote_volume"],
                snapshot["open_time"],
                snapshot["close_time"],
                snapshot["trade_count"],
            )
            self.session.execute(insert_tick, values)
            self.session.execute(upsert_latest, values[:1] + values[2:])
            saved.append({"observed_at": observed_at, **snapshot})

        return saved

    def latest(self, symbols=None):
        if not self.ready:
            return []

        if symbols:
            rows = []
            statement = self.session.prepare("SELECT * FROM latest_prices WHERE symbol = ?")
            for symbol in symbols:
                result = self.session.execute(statement, (symbol.upper(),)).one()
                if result:
                    rows.append(result._asdict())
            return [serialize_snapshot(row) for row in rows]

        result = self.session.execute("SELECT * FROM latest_prices")
        return [serialize_snapshot(row._asdict()) for row in result]

    def history(self, symbol, limit=100):
        if not self.ready:
            return []

        statement = self.session.prepare(
            """
            SELECT * FROM price_ticks_by_symbol
            WHERE symbol = ? AND bucket_date = ?
            LIMIT ?
            """
        )
        rows = self.session.execute(statement, (symbol.upper(), date.today(), limit))
        return [serialize_snapshot(row._asdict()) for row in rows]


market_repository = MarketRepository()
