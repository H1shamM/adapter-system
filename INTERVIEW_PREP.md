# Interview Preparation Guide

## 30-Second Elevator Pitch

"I built a pluggable data ingestion platform that integrates with external APIs like GitHub, AWS, and CoinGecko. It uses hexagonal architecture so adding a new integration is just implementing three methods -- connect, fetch, normalize -- with zero changes to existing code. The system scales horizontally with Celery workers and can run 40+ adapter instances simultaneously. It has a React dashboard for real-time monitoring of sync progress across all workers."

## Architecture Walkthrough

### "Walk me through the architecture"

"The system has three main layers:

**1. API Layer** -- FastAPI serves REST endpoints behind JWT auth. When a user triggers a sync, the API queues a Celery task and returns immediately with a sync ID.

**2. Task Layer** -- Celery workers pick up sync tasks from RabbitMQ. Each worker runs 10 concurrent tasks. The task calls the Sync Engine, which is the core orchestration.

**3. Adapter Layer** -- The Sync Engine uses a Factory to build the right adapter from a registry. Every adapter implements the same three-method contract: `connect()` validates credentials, `fetch_raw()` pulls vendor data, `normalize()` converts it to our unified `NormalizedAsset` schema. Results go to MongoDB.

The key architectural insight is **inversion of control** -- the core engine never imports a specific adapter. The factory resolves the type string at runtime. This means I can add a new adapter without touching any existing code."

### "How does the data flow?"

```
User clicks "Sync" in UI
  --> POST /api/v1/adapters/{id}/sync
  --> API looks up adapter config in MongoDB
  --> Queues Celery task with (adapter_id, type, config, sync_id)
  --> Worker picks up task
  --> sync_engine.run_adapter_sync(type, config)
  --> factory.build_adapter(type, config) returns adapter instance
  --> adapter.execute() chains: connect -> fetch_raw -> normalize
  --> AssetStore.store_assets() upserts into MongoDB
  --> SyncHistory records duration, status, result counts
  --> Prometheus metrics updated
```

## Scaling Story

### "How does scaling work?"

"I started with a single Celery worker processing one sync at a time. With 40 adapters at 30-minute sync intervals, they'd pile up in the queue.

I scaled horizontally by adding workers. Each worker runs 10 concurrent tasks using Celery's prefork pool. The Docker Compose scaling config launches 4 workers, giving 40 concurrent slots -- enough to sync all 40 adapters simultaneously.

RabbitMQ handles the distribution automatically. Tasks are acked late (`task_acks_late=True`) so if a worker crashes mid-sync, the task returns to the queue and another worker picks it up."

### "How would you handle 1000+ adapters?"

"Three changes:

1. **Auto-scaling workers** -- Use Kubernetes HPA to scale workers based on queue depth. The RabbitMQ management API exposes queue length.

2. **Priority queues** -- Critical adapters (SLA-bound) get a high-priority queue. Non-critical adapters go to a default queue. Celery supports multiple queues natively.

3. **Smarter scheduling** -- The beat scheduler currently checks all adapters on a fixed interval. At scale, I'd batch check in pages and spread the triggers to avoid thundering herd."

## Technical Decisions

### "Why FastAPI?"

"Async-native, auto-generates OpenAPI docs, Pydantic validation on every endpoint. For this project, having interactive Swagger docs at `/docs` is great for demos and debugging."

### "Why MongoDB?"

"The adapter configs and asset metadata are schema-flexible -- each adapter type has different fields. MongoDB's document model handles this naturally. Relational would require JSON columns or an EAV pattern."

### "Why Celery + RabbitMQ?"

"Syncs are long-running (seconds to minutes). They can't block the API. Celery gives me distributed task execution, retries with backoff, and time limits. RabbitMQ is the most battle-tested broker for Celery and gives me durable queues."

### "Why not use async tasks directly in FastAPI?"

"FastAPI's BackgroundTasks run in the same process. If the API restarts, tasks are lost. Celery tasks are durable -- they survive API restarts, can be distributed across machines, and support retries, time limits, and result tracking."

## Challenges Overcome

### Multi-Instance Refactor

"The original system used adapter type as the primary key -- one GitHub adapter, one AWS adapter. A customer asked for monitoring 5 different GitHub repos. I refactored the entire storage layer to use `adapter_id` as the primary key, with `adapter_type` as a secondary index. This touched every layer: storage, API, task queue, scheduler, and frontend."

### Worker Reliability

"Initial testing showed tasks being lost on worker restart. I added `task_acks_late=True` and `task_reject_on_worker_lost=True` so tasks aren't acknowledged until they complete. Combined with soft/hard time limits (30/35 minutes), this prevents both lost tasks and zombie workers."

### JWT Token Refresh

"The frontend's axios interceptor catches 401s, refreshes the access token using the refresh token, and retries the original request transparently. The tricky part was preventing refresh storms when multiple requests fail simultaneously -- the interceptor uses a flag to ensure only one refresh happens."

## Trade-offs

### "What would you change for production?"

| Current | Production |
|---------|------------|
| Hardcoded demo user | OAuth2 / SAML integration |
| `.env` file secrets | AWS Secrets Manager / Vault |
| Single MongoDB instance | Replica set with auth + TLS |
| No CI/CD | GitHub Actions with staged deploy |
| Basic error handling | Dead letter queue + alerting |
| Sync-all triggers every instance | Staggered scheduling to avoid thundering herd |

### "What are the limitations?"

"1. **No idempotency** -- If a worker crashes after storing assets but before recording history, a retry would re-insert. I'd add a sync_id check in the store layer.

2. **No backpressure** -- Triggering 1000 syncs fills the queue without throttling. I'd add a max-in-flight check.

3. **Polling-based UI** -- The dashboard polls every 3-5 seconds. WebSockets would give true real-time updates without the overhead."

## Common Questions

### "How do you prevent duplicate syncs?"

"Currently, the system doesn't -- triggering sync twice queues two tasks. In production, I'd add a distributed lock (Redis) per adapter_id. Before queuing, check if a sync is already in-flight for that adapter."

### "How do you handle adapter failures?"

"Three levels: (1) Celery retries with exponential backoff for transient errors like connection timeouts. (2) The `connect()` method validates credentials before fetching -- fails fast on auth issues. (3) Sync history records every failure with the error message, and the dashboard shows per-adapter success rates."

### "How do you test this?"

"Unit tests mock the HTTP client and test each adapter's normalize method with fixture data. Integration tests hit a real MongoDB and test the full API --> storage flow. The PerfTestAdapter simulates 30-minute syncs for load testing without needing real external APIs."

### "Walk me through adding a new adapter"

"Three steps: (1) Create `app/adapters/my_adapter/adapter.py` implementing `BaseAdapter` -- three methods: connect, fetch_raw, normalize. (2) Register it in `ADAPTER_REGISTRY` in factory.py. (3) Add to `SUPPORTED_ADAPTERS` list. No other code changes needed. The API, scheduler, and dashboard all pick it up automatically."
