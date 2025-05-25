import os
import time

from app.adapters.github_adapter import GitHubAdapter
from app.models import NormalizedAsset


def test_github_adapter():
    # 1. Initialize with mock config
    config = {
        "api_token": os.getenv("GITHUB_TOKEN", "test-token"),
        "repo": "axios/axios"  # Example repo
    }
    adapter = GitHubAdapter(config)

    # 2. Test fetching
    try:
        raw_issues = adapter.fetch_assets()
        print("✅ Raw data sample:", raw_issues[:1])
    except Exception as e:
        print("❌ Fetch failed:", e)
        return

    # 3. Test normalization
    try:
        normalized = adapter.normalize(raw_issues)
        print("✅ Normalized sample:", normalized[:1])

        # Validate schema
        for asset in normalized:
            NormalizedAsset(**asset)  # Will throw error if invalid
        print("✅ All assets validate against schema")

    except Exception as e:
        print("❌ Normalization failed:", e)
        return

    # 4. Test full processing
    from app.tasks import process_adapter
    task = process_adapter.delay("github", config)

    # Wait with status checks
    for _ in range(10):  # 10 attempts
        if task.ready():
            result = task.result
            print("✅ Processing result:", result)
            return
        time.sleep(3)  # Wait 3 seconds between checks

    raise AssertionError("Task did not complete within 30 seconds")


if __name__ == "__main__":
    test_github_adapter()