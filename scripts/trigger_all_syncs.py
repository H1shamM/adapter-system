"""
Trigger all configured adapters to sync immediately.
"""
import requests
import time

API_BASE = "http://localhost:8000/api/v1"


session = requests.Session()

def login(username: str = "admin", password:str = "admin123"):

    try:
        response = session.post(
            f"{API_BASE}/auth/login",
            data={"username": username, "password": password},
        )

        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            session.headers.update({"Authorization": f"Bearer {token}"})
            print(f"✓ Logged in as {username}")
            return True

        else:
            print(f"✗ Login failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Login error: {e}")
        return False

def get_all_instances():
    response = session.get(f"{API_BASE}/adapters")
    if response.status_code == 200:
        data = response.json()
        return data.get("instances", [])
    return []

def trigger_sync(adapter_id: str):
    try:
        response = session.post(f"{API_BASE}/adapters/{adapter_id}/sync")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Queued {adapter_id}: task_id={data.get('task_id')}")
            return True
        else:
            print(f"✗ Failed to queue {adapter_id}: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error queuing {adapter_id}: {e}")
        return False


def trigger_all_syncs():
    print("=" * 80)
    print("TRIGGER ALL SYNCS")
    print("=" * 80)

    if not login():
        print("Login failed")
        return

    print("\nFetching configured adapter instances ...")
    instances = get_all_instances()

    if not instances:
        print("No adapter instances configured!")
        return

    print(f"Found {len(instances)} instances")

    # Trigger all
    print(f"\nTriggering {len(instances)} syncs...")
    print("-" * 80)


    success_count = 0
    failed_count = 0

    for instance in instances:
        adapter_id = instance.get("adapter_id")
        if trigger_sync(adapter_id):
            success_count += 1
        else:
            failed_count += 1

        time.sleep(0.1)

    print("-" * 80)
    print(f"\nResults:")
    print(f"  Queued:  {success_count} ✅")
    print(f"  Failed:  {failed_count} ❌")
    print(f"  Total:   {len(instances)}")
    print("\nAll syncs queued! Check monitor_scaling.py to watch progress.")


if __name__ == "__main__":
    trigger_all_syncs()