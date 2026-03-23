import json
import requests

"""
Setup 40 test adapters with varying sync intervals.

Simulates a real enterprise customer with:
- 5 critical adapters (sync every 6 hours)
- 15 high-priority adapters (sync every 12 hours)
- 20 normal adapters (sync every 24 hours)
"""

API_BASE = "http://localhost:8000/api/v1"

test_configs = []


for i in range(5):
    test_configs.append({
        "adapter_id" : f"critical_adapter_{i:02d}",
        "adapter_type": "perftest",
        "name": "perftest",
        "enabled": True,
        "sync_interval": 21600,
        "priority": "high",
        "test_id": f"critical_adapter_{i:02d}",
        "sync_duration_seconds": 180,
        "asset_count": 150,
        "base_url": "http://mock-api.test",
        "auth_type": "none",
        "asset_types": ["test_asset"]
    })

for i in range(15):
    test_configs.append({
        "adapter_id": f"high_priority_adapter_{i:02d}",
        "adapter_type": "perftest",
        "name": "perftest",
        "enabled": True,
        "sync_interval": 43200,
        "priority": "medium",
        "test_id": f"high_priority_adapter_{i:02d}",
        "sync_duration_seconds": 300,
        "asset_count": 100,
        "base_url": "http://mock-api.test",
        "auth_type": "none",
        "asset_types": ["test_asset"]
    })

for i in range(20):
    test_configs.append({
        "adapter_id": f"normal_priority_adapter_{i:02d}",
        "adapter_type": "perftest",
        "name": "perftest",
        "enabled": True,
        "sync_interval": 86400,
        "priority": "low",
        "test_id": f"normal_adapter_{i:02d}",
        "sync_duration_seconds": 400,
        "asset_count": 50,
        "base_url": "http://mock-api.test",
        "auth_type": "none",
        "asset_types": ["test_asset"]
    })

print(f"Configuring {len(test_configs)} test adapters")

for i, config in enumerate(test_configs):
    try:
        response = requests.post(
            f"{API_BASE}/adapters",
            json=config,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            print(f"✓ Configured {config['test_id']} ({config['sync_interval']}s interval)")
        else:
            print(f"✗ Failed to configure {config['test_id']}: {response.text}")

    except Exception as e:
        print(f"✗ Error configuring {config['test_id']}: {e}")

print(f"\nSetup complete! {len(test_configs)} adapters configured.")
print("\nDistribution:")
print("  - 5 critical (6h interval)")
print("  - 15 high-priority (12h interval)")
print("  - 20 normal (24h interval)")