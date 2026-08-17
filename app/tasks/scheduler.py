import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.integrations.github import GitHubIssueClient
from app.storage.adapters import AdapterConfigStore
from app.storage.sync_history import SyncHistoryStore
from app.tasks.core import app, sync_adapter_task
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Consecutive FAILED syncs (last_n_statuses, newest first) that trigger a drift issue -- a plain
# constant enforced in code, not a "usually 3 is enough" convention (see docs/AGENTIC_ADAPTER_
# DESIGN.md's Trigger model / the quest4-agents lesson this mirrors: guardrails belong in code).
FAILURE_STREAK_THRESHOLD = 3


@app.task(name="check_due_adapters")
def check_and_queue_due_adapters():
    logger.info("scheduler_checking_due_adapters")
    store = AdapterConfigStore()
    due_adapters = store.get_due_adapters()

    if not due_adapters:
        logger.info("scheduler_no_due_adapters")
        return {"queued": 0, "total_due": 0}

    history = SyncHistoryStore()
    queued = 0

    for adapter in due_adapters:
        adapter_id = adapter["adapter_id"]
        adapter_type = adapter["adapter_type"]
        sync_id = str(uuid4())

        try:

            task = sync_adapter_task.delay(adapter_id, adapter_type, adapter, sync_id)

            history.start_sync(
                sync_id=sync_id,
                adapter=adapter_id,
                estimated_duration=adapter.get("sync_duration_seconds"),
            )

            queued += 1

            logger.info(
                "scheduler_queued_sync",
                adapter_id=adapter_id,
                adapter_type=adapter_type,
                sync_interval=adapter.get("sync_interval"),
                priority=adapter.get("priority"),
                task_id=task.id,
                sync_id=sync_id,
            )
        except Exception as e:
            logger.error(
                "scheduler_queue_failed",
                adapter_id=adapter_id,
                adapter_type=adapter_type,
                error=str(e),
                exc_info=True,
            )

    logger.info("scheduler_completed", total_due=len(due_adapters), queued=queued)

    return {
        "queued": queued,
        "total_due": len(due_adapters),
        "timestamp": datetime.now().isoformat(),
    }


@app.task(name="check_repeatedly_failing_adapters")
def check_repeatedly_failing_adapters():
    """Drift-detection watcher -- the automated half of Sprint 5's Trigger model
    (docs/AGENTIC_ADAPTER_DESIGN.md). Flags an adapter instance whose last FAILURE_STREAK_THRESHOLD
    finished syncs were all FAILED by opening a labeled GitHub issue with the failing sync_ids and
    error messages attached, so a human (or, once wired up, an automated routine reacting to that
    issue) can run diagnose-adapter-drift against it. Never opens a duplicate while one is already
    open for that adapter."""
    logger.info("drift_watcher_checking_adapters")
    adapter_store = AdapterConfigStore()
    history_store = SyncHistoryStore()
    github = GitHubIssueClient()

    flagged = 0
    checked = 0

    for adapter in adapter_store.list_all():
        if not adapter.get("enabled"):
            continue
        checked += 1
        adapter_id = adapter["adapter_id"]
        adapter_type = adapter["adapter_type"]

        try:
            statuses = history_store.last_n_statuses(adapter=adapter_id, n=FAILURE_STREAK_THRESHOLD)
            if len(statuses) < FAILURE_STREAK_THRESHOLD:
                continue
            if not all(status == "FAILED" for status in statuses):
                continue

            if asyncio.run(github.find_open_drift_issue(adapter_id)):
                logger.info("drift_watcher_already_flagged", adapter_id=adapter_id)
                continue

            evidence = history_store.list(adapter=adapter_id, limit=FAILURE_STREAK_THRESHOLD)
            issue_number = asyncio.run(
                github.create_drift_issue(
                    adapter_id=adapter_id, adapter_type=adapter_type, evidence=evidence
                )
            )
            flagged += 1
            logger.info(
                "drift_issue_opened",
                adapter_id=adapter_id,
                adapter_type=adapter_type,
                issue_number=issue_number,
            )
        except Exception as e:
            logger.error(
                "drift_watcher_check_failed",
                adapter_id=adapter_id,
                adapter_type=adapter_type,
                error=str(e),
                exc_info=True,
            )

    logger.info("drift_watcher_completed", checked=checked, flagged=flagged)

    return {"checked": checked, "flagged": flagged, "timestamp": datetime.now().isoformat()}


app.conf.beat_schedule = {
    "check-due-adapters-every-5-min": {
        "task": "check_due_adapters",
        "schedule": timedelta(minutes=5),
        "options": {"expires": 300},
    },
    "check-repeatedly-failing-adapters-every-15-min": {
        "task": "check_repeatedly_failing_adapters",
        "schedule": timedelta(minutes=15),
        "options": {"expires": 900},
    },
}

app.conf.timezone = "UTC"
