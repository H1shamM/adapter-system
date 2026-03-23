import time
from collections import Counter
from datetime import datetime

import requests

"""
Monitor scaling test in real-time.

Shows:
- Active syncs
- Queue depth
- Worker status
- Completion rate
"""

API_BASE = "http://localhost:8000/api/v1"

session = requests.Session()


def login(username: str = "admin", password: str = "admin123"):
    try:
        response = session.post(
            f"{API_BASE}/auth/login",
            data={"username": username, "password": password}
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


def get_sync_history():
    try:
        response = session.get(f"{API_BASE}/syncs/history?limit=500")

        if response.status_code == 401:
            print("Authentication required. Please login first.")
            return []

        if response.status_code != 200:
            print(f"API Error {response.status_code}: {response.text}")
            return []
        data = response.json()
        if not isinstance(data, list):
            print(f"Warning: Expected list, got {type(data)}")
            return []

        return data

    except Exception as e:
        print(f"Error fetching history: {e}")
        return []


def get_sync_summary():
    response = session.get(f"{API_BASE}/syncs/summary")
    return response.json()


def monitor():
    print("=" * 80)
    print("SCALING TEST MONITOR")
    print("=" * 80)

    if not login():
        print("Login failed")
        return

    start_time = datetime.now()

    while True:
        try:
            history = get_sync_history()
            total_syncs = len(history)
            statuses = Counter(sync["status"] for sync in history)

            in_progress = statuses.get("STARTED", 0)
            completed = statuses.get("SUCCESS", 0)
            failed = statuses.get("FAILED", 0)

            completed_syncs = [s for s in history if s["status"] == "SUCCESS" and s['duration_ms']]
            avg_duration = sum(s["duration_ms"] for s in completed_syncs) / len(
                completed_syncs) if completed_syncs else 0

            elapsed = (datetime.now() - start_time).total_seconds()

            print(f"\n[{datetime.utcnow().strftime('%H:%M:%S')}] Elapsed: {elapsed:.0f}s")
            print("-" * 80)
            print(f"Total Syncs:    {total_syncs}")
            print(f"In Progress:    {in_progress} 🔄")
            print(f"Completed:      {completed} ✅")
            print(f"Failed:         {failed} ❌")

            if avg_duration > 0:
                print(f"Avg Duration:   {avg_duration / 1000:.1f}s")
            else:
                print(f"Avg Duration:   N/A (no completed syncs yet)")

            if total_syncs > 0:
                completion_rate = (completed / total_syncs) * 100
                print(f"Completion:     {completion_rate:.1f}%")

            if in_progress > 0:
                print("\nActive Syncs:")
                active = [s for s in history if s["status"] == "STARTED"]
                for sync in active:
                    adapter = sync.get("adapter", "unknown")
                    started = sync.get("started_at", "")
                    print(f"  - {adapter} (started: {started})")

            time.sleep(10)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            print("\nFinal Statistics:")
            print("-" * 80)
            try:
                summary = get_sync_summary()
                if summary:
                    for adapter, stats in summary.items():
                        print(f"\n{adapter}:")
                        print(f"  Total Runs:    {stats.get('total_runs', 0)}")
                        print(f"  Success Rate:  {stats.get('success_rate', 0):.1f}%")
                        print(f"  Last Duration: {stats.get('last_duration_ms', 0) / 1000:.1f}s")
            except:
                pass
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(10)


if __name__ == "__main__":
    monitor()
