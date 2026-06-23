import os


def _csv_env(name, default):
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


class Settings:
    app_name = os.getenv("APP_NAME", "Crypto Trading Monitor")
    binance_base_url = os.getenv("BINANCE_BASE_URL", "https://data-api.binance.vision")
    default_symbols = _csv_env("CRYPTO_SYMBOLS", "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT")
    cassandra_hosts = _csv_env("CASSANDRA_HOSTS", "127.0.0.1")
    cassandra_port = int(os.getenv("CASSANDRA_PORT", "9042"))
    cassandra_keyspace = os.getenv("CASSANDRA_KEYSPACE", "crypto_market")
    cassandra_username = os.getenv("CASSANDRA_USERNAME")
    cassandra_password = os.getenv("CASSANDRA_PASSWORD")
    auto_ingest_seconds = int(os.getenv("CRYPTO_AUTO_INGEST_SECONDS", "0"))
    request_timeout_seconds = float(os.getenv("BINANCE_TIMEOUT_SECONDS", "10"))


settings = Settings()
