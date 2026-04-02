# Demo Script (5 minutes)

A walkthrough demonstrating the adapter system's multi-instance scaling, real-time monitoring, and dashboard UI.

## Prerequisites

- Docker + Docker Compose installed
- Node.js 18+ installed
- Python 3.11+ installed

## Setup (one-time, ~2 minutes)

```bash
# Start all backend services
docker compose up --build -d

# Wait for services to be healthy
docker compose ps   # All should show "healthy"

# Install frontend dependencies
cd ui && npm install && cd ..

# Create 40 adapter instances (5 critical, 15 high, 20 normal)
python scripts/setup_scaling_test.py
```

## Demo Flow

### Step 1: Start the Dashboard

```bash
cd ui && npm run dev
```

Open http://localhost:5173

**Login:** `admin` / `admin123`

**What you see:** The Overview tab with 4 stats cards (Total Adapters: 40, Active Syncs: 0, Queue Depth: 0, Capacity: 0/40), Worker Visualization showing 4 empty workers, and the Adapter Instances Grid listing all 40 instances.

### Step 2: Explore the Tabs

- **Overview** -- Stats cards, worker slot visualization, live sync monitor
- **Adapters** -- Instance cards grouped by type (github, aws, coingecko, etc.) with health badges and per-instance sync buttons
- **Assets** -- Paginated table of ingested assets with expandable metadata rows
- **Sync History** -- Aggregated success rates, durations, and failure counts per adapter

### Step 3: Trigger a Single Sync

On the **Overview** tab, find any adapter in the instances grid and click the Play button. Watch:

1. The "Active Syncs" stat card increments
2. The Live Sync Monitor shows a progress card with elapsed time
3. Worker Visualization lights up a slot in one worker

### Step 4: Trigger All 40 Adapters

Click the **"Sync All Adapters"** button in the header. Confirm the dialog.

**What happens:**
- All 40 adapters are queued as Celery tasks
- RabbitMQ distributes tasks across 4 workers (10 each)
- Worker Visualization shows all 40 slots filling up
- Live Sync Monitor shows 40 active progress cards
- Stats update every 5 seconds

### Step 5: Monitor Completion

Watch the syncs complete over the next few minutes. As each finishes:

- Active Syncs count decreases
- Worker slots turn from green back to grey
- Completed syncs appear in the "Recent Completed" table
- Switch to the **Sync History** tab to see success rates

### Step 6: View Ingested Assets

Switch to the **Assets** tab. Click any row to expand and see type-specific metadata:

- **Crypto assets** -- Symbol, price, market cap rank
- **User assets** -- Email, phone, country
- **Issue assets** -- Clickable GitHub issue URL

### Step 7: Show the Architecture (API Docs)

Open http://localhost:8000/docs to show the auto-generated Swagger UI with all endpoints.

## Key Talking Points During Demo

1. **Horizontal scaling** -- "Each worker handles 10 concurrent syncs. I can scale to N workers just by adding containers."

2. **Adapter pattern** -- "Adding a new integration is just 3 methods: connect, fetch_raw, normalize. No changes to existing code."

3. **Multi-instance** -- "The same adapter type can have multiple instances with different configs -- like 5 GitHub repos monitored independently."

4. **Observability** -- "Every sync is tracked in MongoDB with duration, status, and results. Prometheus metrics are exposed at /metrics."

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Failed to connect to backend" | Check `docker compose ps` -- all services should be healthy |
| Login fails | Default credentials: `admin` / `admin123` |
| No adapters shown | Run `python scripts/setup_scaling_test.py` |
| CORS errors | Backend CORS allows `localhost:5173` by default |
| Syncs stay in STARTED | Check worker logs: `docker compose logs worker` |

## Scaling Test (Full Load)

To demo with 4 workers (40 concurrent capacity):

```bash
docker compose -f docker-compose.yml -f docker-compose.scaling-test.yml up --build -d

python scripts/setup_scaling_test.py
python scripts/trigger_all_syncs.py
python scripts/monitor_scaling.py   # Terminal-based real-time stats
```
