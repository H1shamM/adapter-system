# Asset Management System

## Features
- Adapter framework for data ingestion
- GitHub/AWS/Mock integrations
- MongoDB storage with versioning
- Prometheus metrics

## Quick Start
```bash
docker-compose up -d
celery -A app.tasks worker --loglevel=info
uvicorn app.main:app --reload
```

## API Documentation
`GET /assets` - List assets with filters  
`POST /adapters/{type}/sync` - Trigger sync

## Architecture
![System Diagram](docs/architecture.png)