``` mermaid
flowchart TD
    %% API Layer
    API[FastAPI API\nPOST /sync\nGET /adapters] -->|trigger task| CeleryTask[Celery Worker\nsync_adapter_task]
    API -->|direct call| CLI[CLI Runner\nrun_adapter_sync]

    %% Sync Engine
    CeleryTask --> SyncEngine[Sync Engine\nrun_adapter_sync]
    CLI --> SyncEngine

    %% Adapters
    SyncEngine --> Adapters[Adapters / Ports\nGitHub, AWS, Mock\nRaises domain errors]

    %% Storage
    Adapters --> AssetStore[AssetStore\nMongoDB storage\nBulkWrite, Indexes]

    %% Observability / Metrics
    SyncEngine --> Metrics[Monitoring\nSYNC_SUCCESS, SYNC_ERRORS, SYNC_DURATION, ASSET_COUNT]
    AssetStore --> Metrics
    CeleryTask --> Metrics
    API --> Metrics

    %% Metrics exposure
    Metrics --> Prometheus[/metrics endpoint for Prometheus/]

    %% Notes
    style API fill:#f9f,stroke:#333,stroke-width:2px
    style CLI fill:#ccf,stroke:#333,stroke-width:2px
    style CeleryTask fill:#fc9,stroke:#333,stroke-width:2px
    style SyncEngine fill:#9fc,stroke:#333,stroke-width:2px
    style Adapters fill:#cff,stroke:#333,stroke-width:2px
    style AssetStore fill:#ffc,stroke:#333,stroke-width:2px
    style Metrics fill:#f96,stroke:#333,stroke-width:2px
    style Prometheus fill:#eee,stroke:#333,stroke-width:2px


