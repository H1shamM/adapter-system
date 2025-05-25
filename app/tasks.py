from celery import Celery
from requests import RequestException
from tenacity import retry, stop_after_attempt, wait_fixed
from app.adapters.github_adapter import GitHubAdapter
from app.storage import store_assets

app = Celery(
    'tasks',
    broker='amqp://localhost:5672',
    backend='redis://localhost:6379/0'  # Switch to Redis for better results tracking
)

# Adapter registry
ADAPTER_MAP = {
    "github": GitHubAdapter
}


@app.task(bind=True)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def process_adapter(self, adapter_type: str, config: dict):
    """Main processing task"""
    try:
        # Get adapter class
        adapter_class = ADAPTER_MAP.get(adapter_type)
        if not adapter_class:
            raise ValueError(f"Unknown adapter type: {adapter_type}")

        # Instantiate and process
        adapter = adapter_class(config)
        raw_data = adapter.fetch_assets()
        normalized = adapter.normalize(raw_data)

        # Store results
        inserted_ids = store_assets(normalized)
        return {
            "adapter": adapter_type,
            "processed": len(inserted_ids),
            "success": True
        }

    except RequestException as e:
        self.retry(exc=e)
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }
