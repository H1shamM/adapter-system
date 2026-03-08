from prometheus_client import Counter , Gauge

SYNC_SUCCESS = Counter(
    'asset_sync_success_total',
    'Successful asset synchronizations',
    ['adapter_type', 'customer_id']
)
SYNC_FAILURES = Counter(
    'adapter_sync_failure_total',
    'Failures during the sync process',
    ['adapter_type', 'customer_id']
)

SYNC_DURATION = Gauge(
    'asset_sync_duration_seconds',
    'Sync execution time',
    ['adapter_type', 'customer_id']
)

SYNC_ERRORS = Counter(
    'asset_sync_error_total',
    'Errors during the sync process',
    ['adapter_type', 'customer_id']
)
ASSET_COUNT = Gauge(
    'stored_assets_total',
    'Total assets per type',
    ['asset_type', 'customer_id']
)