# Adapter System – Pluggable Ingestion Service (Python)

## Overview

This project implements a **pluggable backend ingestion system** using the **Adapter (Ports & Adapters) architecture pattern**.

It simulates a real-world backend service that integrates with multiple third-party APIs (e.g. GitHub, AWS), **normalizes heterogeneous data into a unified schema**, and exposes a clean internal interface for downstream systems.

The project is inspired by production ingestion systems used in SaaS platforms and asset-management products.

---

## Problem This Solves

In real systems, backend services often need to integrate with:
- many external APIs
- different authentication methods
- different response formats
- changing vendor schemas

This project demonstrates how to:
- isolate external dependencies
- keep core logic stable
- add new integrations without modifying existing code
- normalize external data into a consistent internal model

---

## Architecture
````
            ┌──────────────┐
            │  Core Logic  │
            │ (Runner /    │
            │  Orchestration)
            └──────┬───────┘
                   │
        ┌──────────┴──────────┐
        │      Adapter API     │
        │ (Abstract Base Class)
        └──────────┬──────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
┌───────────────┐        ┌────────────────┐
│ GitHub Adapter│        │ AWS Adapter    │
│ (HTTP API)    │        │ (HTTP API)     │
└───────────────┘        └────────────────┘
                   │
            ┌──────┴───────┐
            │ Normalization│
            │ (Unified Model)
            └──────────────┘
````
## Key Concepts

### Adapter Pattern
- Each external integration implements a common adapter interface
- Core logic depends only on the interface, not concrete implementations
- New adapters can be added without modifying existing code

### Factory Pattern
- Adapters are created dynamically via a factory
- The system selects the adapter based on configuration
- Prevents hard-coded dependencies

### Normalization Layer
- External vendor data is converted into a `NormalizedAsset`
- Downstream systems never depend on vendor-specific schemas

---
## Tech Stack
- Python
- Pydantic
- pytest
- Docker & Docker Compose

## Project Structure
```
app/
├── adapters/
│   ├── base.py              # Abstract adapter contract
│   ├── factory.py           # Adapter factory
│   ├── github_adapter.py    # GitHub integration
│   └── aws_adapter.py       # AWS integration
│
├── models/
│   ├── asset.py             # NormalizedAsset schema
│   └── config.py            # Adapter & HTTP configs
│
├── http/
│   └── client.py            # Reusable HTTP client abstraction
│
├── tests/
│   ├── test_adapters.py
│   └── test_github_adapter.py
│
└── main.py                  # Entry point (example usage)
```

## Key Concepts

### Adapter Pattern
- Each external integration implements a common adapter interface
- Core logic depends only on the interface, not concrete implementations
- New adapters can be added without modifying existing code

### Factory Pattern
- Adapters are created dynamically via a factory
- The system selects the adapter based on configuration
- Prevents hard-coded dependencies

### Normalization Layer
- External vendor data is converted into a `NormalizedAsset`
- Downstream systems never depend on vendor-specific schemas

---

## Run Locally
```bash
pip install -r requirements.txt
python app/main.py
```

Or with Docker:
```bash
docker compose up --build
```

## Why This Matters
- Easy to add or replace integrations
- Resistant to third‑party API changes
- Mirrors real-world ingestion systems
- High testability and maintainability
