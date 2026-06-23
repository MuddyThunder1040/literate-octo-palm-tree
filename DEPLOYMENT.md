# Ubuntu Deployment

The application is container-ready and expects an existing Cassandra cluster.

## Required environment

```text
CASSANDRA_HOSTS=10.0.0.10,10.0.0.11,10.0.0.12
CASSANDRA_PORT=9042
CASSANDRA_KEYSPACE=crypto_market
```

If Cassandra requires authentication:

```text
CASSANDRA_USERNAME=your_username
CASSANDRA_PASSWORD=your_password
```

For Binance regional access, configure the base URL:

```text
BINANCE_BASE_URL=https://data-api.binance.vision
```

If your server should use the regional Binance US endpoint, use:

```text
BINANCE_BASE_URL=https://api.binance.us
```

Optional market settings:

```text
CRYPTO_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,XRPUSDT
CRYPTO_AUTO_INGEST_SECONDS=30
BINANCE_TIMEOUT_SECONDS=10
```

`CRYPTO_AUTO_INGEST_SECONDS=0` disables background ingestion. You can still trigger ingestion from the UI or `POST /api/crypto/ingest`.

## Docker run

```bash
docker build -t crypto-trading-monitor:latest .

docker run -d \
  --name crypto-trading-monitor \
  -p 8000:8000 \
  -e CASSANDRA_HOSTS=10.0.0.10,10.0.0.11,10.0.0.12 \
  -e CASSANDRA_PORT=9042 \
  -e CASSANDRA_KEYSPACE=crypto_market \
  -e BINANCE_BASE_URL=https://api.binance.com \
  -e CRYPTO_AUTO_INGEST_SECONDS=30 \
  crypto-trading-monitor:latest
```

Open:

```text
http://server-ip:8000/
```

## API

```text
GET  /api/crypto/status
GET  /api/crypto/markets?symbols=BTCUSDT,ETHUSDT
POST /api/crypto/ingest?symbols=BTCUSDT,ETHUSDT
GET  /api/crypto/latest?symbols=BTCUSDT,ETHUSDT
GET  /api/crypto/history/BTCUSDT?limit=100
GET  /api/cluster/health
```
