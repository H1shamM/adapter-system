# Adapter System

A production-grade **pluggable data ingestion platform** built with hexagonal (Ports & Adapters) architecture. Integrates with multiple external APIs, normalizes heterogeneous data into a unified schema, and scales horizontally with distributed task processing.

## Architecture

```
                    React Dashboard (Vite + TypeScript)
                              |
                         Axios / REST
                              |
                    FastAPI  (/api/v1/*)
                    JWT Auth + Rate Limiting
                              |
              +---------------+---------------+
              |                               |
        Celery Task Queue              CLI Runner
        (RabbitMQ broker)            (runner.py)
              |                               |
              +---------------+---------------+
                              |
                     Sync Engine
                   run_adapter_sync()
                              |
                     Adapter Factory
                    build_adapter(type, config)
                              |
            +---------+-------+--------+---------+
            |         |       |        |         |
         GitHub     AWS   CoinGecko  JSON    PerfTest
         Adapter  Adapter  Adapter  Placeholder Adapter
            |         |       |        |         |
            +----+----+-------+--------+---------+
                 |
          NormalizedAsset (Pydantic)
                 |
            MongoDB Storage
     (assets, adapter_configs, sync_history)
```

**Data flow:** API request --> Celery task --> Sync Engine --> Factory builds adapter --> `connect()` --> `fetch_raw()` --> `normalize()` --> MongoDB storage --> Prometheus metrics

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI 0.110+ | REST endpoints, OpenAPI docs |
| Auth | python-jose + bcrypt | JWT access/refresh tokens |
| Task Queue | Celery 5.3 + RabbitMQ | Async distributed task execution |
| Database | MongoDB (pymongo) | Assets, configs, sync history |
| HTTP Client | httpx (async) | Adapter API calls with retry/pagination |
| Monitoring | Prometheus client | Sync metrics (success, duration, errors) |
| Rate Limiting | slowapi | API request throttling |
| Frontend | React 19 + TypeScript 5.9 | Dashboard UI |
| Build | Vite 7 | Frontend bundling |
| Container | Docker + Docker Compose | Multi-service orchestration |

## Features

- **Multi-instance adapters** -- Multiple instances of the same adapter type with independent configs and schedules
- **Horizontal scaling** -- 4 workers x 10 concurrency = 40 simultaneous syncs
- **Beat scheduler** -- Automatic periodic syncing based on per-instance `sync_interval`
- **Unified schema** -- All vendor data normalized into `NormalizedAsset` model
- **Factory pattern** -- `ADAPTER_REGISTRY` maps type strings to (AdapterClass, ConfigClass) tuples
- **JWT authentication** -- Access + refresh token flow with auto-refresh on the frontend
- **Real-time dashboard** -- Live sync monitoring, worker visualization, adapter management
- **Health checks** -- Kubernetes-ready liveness/readiness/startup probes

## Quick Start

```bash
# 1. Start all services (API, worker, beat, MongoDB, RabbitMQ)
docker compose up --build -d

# 2. Set up 40 test adapter instances
python scripts/setup_scaling_test.py

# 3. Start the frontend
cd ui && npm install && npm run dev

# 4. Open dashboard
# http://localhost:5173  (login: admin / admin123)

# 5. Trigger all 40 adapters from the UI or CLI
python scripts/trigger_all_syncs.py
```

## API Endpoints

All endpoints are prefixed with `/api/v1` and require JWT auth (except `/auth/login`).

### Authentication
```
POST /api/v1/auth/login          # Get access + refresh tokens
POST /api/v1/auth/refresh         # Refresh access token
```

### Adapters
```
GET    /api/v1/adapters                    # List all instances (optional ?adapter_type= filter)
POST   /api/v1/adapters                    # Create/update an adapter instance
GET    /api/v1/adapters/{adapter_id}       # Get instance details
POST   /api/v1/adapters/{adapter_id}/sync  # Trigger sync for an instance
POST   /api/v1/adapters/{adapter_id}/health # Check adapter health
```

### Syncs
```
GET  /api/v1/syncs/history                # Sync history (optional ?adapter=&limit=)
GET  /api/v1/syncs/summary                # Aggregated stats per adapter
GET  /api/v1/syncs/{sync_id}              # Single sync details
GET  /api/v1/syncs/{task_id}/status       # Celery task status (polling)
```

### Assets
```
GET  /api/v1/assets                       # Paginated asset list (?page=&limit=&asset_type=)
```

### Health
```
GET  /api/v1/health/live                  # Liveness probe
GET  /api/v1/health/ready                 # Readiness probe (checks MongoDB + RabbitMQ)
GET  /api/v1/health/info                  # Instance metadata
```

## Scaling Demo

Run 40 adapter instances simultaneously across 4 Celery workers:

```bash
# Start with scaling config (4 workers x 10 concurrency)
docker compose -f docker-compose.yml -f docker-compose.scaling-test.yml up --build -d

# Create 40 test instances (5 critical, 15 high, 20 normal priority)
python scripts/setup_scaling_test.py

# Trigger all 40 simultaneously
python scripts/trigger_all_syncs.py

# Monitor in real-time
python scripts/monitor_scaling.py
```

The dashboard shows live worker utilization with slot-level visualization.

## Adding a New Adapter

1. Create `app/adapters/your_adapter/adapter.py`:

```python
class YourAdapter(BaseAdapter):
    async def connect(self):
        """Validate credentials / test connectivity."""

    async def fetch_raw(self) -> List[Dict]:
        """Fetch raw data from external API."""

    def normalize(self, raw_data: List[Dict]) -> List[NormalizedAsset]:
        """Convert vendor data to unified schema."""
```

2. Register in `app/adapters/factory.py`:

```python
ADAPTER_REGISTRY = {
    ...
    "your_adapter": (YourAdapter, YourConfig),
}
```

3. Add to `app/adapters/registry.py` SUPPORTED_ADAPTERS list.

## Project Structure

```
app/
  adapters/          # Adapter implementations (GitHub, AWS, CoinGecko, etc.)
    base.py          # BaseAdapter ABC + AdapterConfig
    factory.py       # ADAPTER_REGISTRY + build_adapter()
  api/               # FastAPI routes (/adapters, /syncs, /assets, /health, /auth)
  auth/              # JWT creation, verification, password hashing
  config/            # Pydantic BaseSettings (env-driven configuration)
  db/                # MongoDB client initialization
  models/            # NormalizedAsset -- unified data schema
  monitoring/        # Prometheus metrics
  services/          # Sync engine -- core orchestration
  storage/           # MongoDB data access (adapters, assets, sync_history)
  tasks/             # Celery app, sync task, beat scheduler
  tests/             # Unit + integration tests
scripts/             # Scaling test setup, trigger, and monitor scripts
ui/                  # React + TypeScript dashboard
configs/             # JSON adapter config files
```

## Running Tests

```bash
pytest                          # All tests
pytest app/tests/unit/          # Unit tests only
pytest app/tests/integration/   # Integration tests (requires MongoDB + RabbitMQ)
```

## Environment Variables

All configuration is driven by environment variables via Pydantic BaseSettings. See `.env` for the full list. Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MONGO_URL` | `mongodb://mongo:27017` | MongoDB connection |
| `CELERY_BROKER_URL` | `amqp://guest:guest@localhost:5672//` | RabbitMQ broker |
| `API_JWT_SECRET_KEY` | -- | JWT signing secret |
| `CUSTOMER_ID` | `default_customer_id` | Multi-tenant customer identifier |

## Production Considerations

This is a demo/portfolio project. For production deployment, you would add:

- **Secret management** -- AWS Secrets Manager / HashiCorp Vault instead of `.env`
- **CI/CD pipeline** -- Automated testing, Docker image builds, staged deployments
- **Comprehensive test coverage** -- Target 80%+ with integration and contract tests
- **Monitoring stack** -- Prometheus + Grafana dashboards, PagerDuty alerts
- **Database auth** -- MongoDB authentication, TLS, replica sets
- **Rate limiting per tenant** -- Per-customer API quotas
- **Idempotent syncs** -- Prevent duplicate processing on worker restart
- **Dead letter queue** -- Handle permanently failing tasks
- **Graceful shutdown** -- Drain workers before container stop
