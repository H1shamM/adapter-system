from typing import Dict, List, Optional

import httpx

from app.config import settings

DRIFT_LABEL = "adapter-drift"

# Deployment prerequisite, not created automatically here: the `adapter-drift` label must already
# exist on the target repo (e.g. `gh label create adapter-drift --color b60205` once), or issue
# creation will fail with a 422 from GitHub's API.


class GitHubIssueClient:
    """Thin wrapper around the GitHub REST API for opening/finding drift-detection issues. Used
    by the drift watcher (app/tasks/scheduler.py) to bridge a detected failure streak into
    something a human -- or eventually an automated routine, see docs/AGENTIC_ADAPTER_DESIGN.md --
    can pick up and run diagnose-adapter-drift against."""

    def __init__(self):
        self._base_url = f"https://api.github.com/repos/{settings.github.repo}"
        self._headers = {
            "Authorization": f"Bearer {settings.github.token.get_secret_value()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def find_open_drift_issue(self, adapter_id: str) -> Optional[int]:
        """Returns the issue number of an already-open drift issue for this adapter instance, or
        None. Dedupe check -- no new Mongo state needed, and self-heals once the issue is closed
        (the next failing tick can open a fresh one)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/issues",
                headers=self._headers,
                params={"labels": DRIFT_LABEL, "state": "open", "per_page": 100},
            )
            response.raise_for_status()
            for issue in response.json():
                if "pull_request" in issue:
                    continue  # the issues endpoint also returns PRs; drift issues never are one
                if adapter_id in issue.get("title", ""):
                    return issue["number"]
            return None

    async def create_drift_issue(
        self, *, adapter_id: str, adapter_type: str, evidence: List[Dict]
    ) -> int:
        """Opens a labeled issue summarizing the failure streak, with enough evidence (sync_ids,
        timestamps, error messages) that a human -- or diagnose-adapter-drift, given this as its
        `evidence` argument -- can start investigating without digging through sync_history
        themselves."""
        body_lines = [
            f"Adapter instance `{adapter_id}` (type `{adapter_type}`) has failed its last "
            f"{len(evidence)} syncs in a row.",
            "",
            "| sync_id | finished_at | error |",
            "|---|---|---|",
        ]
        for sync in evidence:
            body_lines.append(
                f"| `{sync.get('sync_id')}` | {sync.get('finished_at')} | "
                f"{sync.get('error') or '(none recorded)'} |"
            )
        body_lines += [
            "",
            "Investigate with:",
            f'```\n/diagnose-adapter-drift {adapter_type} "{evidence[0].get("error", "")}"\n```',
        ]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/issues",
                headers=self._headers,
                json={
                    "title": f"[adapter-drift] {adapter_id} ({adapter_type}) failing repeatedly",
                    "body": "\n".join(body_lines),
                    "labels": [DRIFT_LABEL],
                },
            )
            response.raise_for_status()
            return response.json()["number"]
