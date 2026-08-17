"""Unit tests for SyncHistoryStore (app/storage/sync_history.py)."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_mongo(mocker):
    fake_collection = MagicMock(name="sync_history_collection")
    fake_db = MagicMock(name="db")
    fake_db.sync_history = fake_collection
    fake_db.__getitem__.return_value = fake_collection

    fake_client = MagicMock(name="mongo_client")
    fake_client.__getitem__.return_value = fake_db

    mocker.patch("app.storage.sync_history.get_mongo_client", return_value=fake_client)
    return {"client": fake_client, "db": fake_db, "collection": fake_collection}


@pytest.fixture
def store(mock_mongo):
    from app.storage.sync_history import SyncHistoryStore

    # _indexes_created is a process-level guard (real createIndexes should only run once per
    # process, not once per SyncHistoryStore() instantiation) -- reset it so each test
    # deterministically observes index creation regardless of pytest session ordering.
    SyncHistoryStore._indexes_created = False
    return SyncHistoryStore()


def test_construction_creates_four_indexes(store, mock_mongo):
    assert mock_mongo["collection"].create_index.call_count == 4


def test_start_sync_inserts_full_doc(store, mock_mongo):
    store.start_sync(sync_id="s1", adapter="gh-1", estimated_duration=120)

    mock_mongo["collection"].insert_one.assert_called_once()
    doc = mock_mongo["collection"].insert_one.call_args.args[0]
    assert doc["sync_id"] == "s1"
    assert doc["adapter"] == "gh-1"
    assert doc["status"] == "STARTED"
    assert doc["estimated_duration"] == 120
    assert doc["finished_at"] is None
    assert doc["duration_ms"] is None
    assert doc["result"] is None
    assert doc["error"] is None
    assert doc["processed_count"] == 0
    assert isinstance(doc["started_at"], datetime)


def test_start_sync_estimated_duration_optional(store, mock_mongo):
    store.start_sync(sync_id="s1", adapter="gh-1")
    doc = mock_mongo["collection"].insert_one.call_args.args[0]
    assert doc["estimated_duration"] is None


def test_finish_sync_computes_duration_ms(store, mock_mongo):
    started_at = datetime.utcnow() - timedelta(seconds=5)
    mock_mongo["collection"].find_one.return_value = {"started_at": started_at}

    store.finish_sync(sync_id="s1", status="SUCCESS", result={"inserted": 3})

    args, _ = mock_mongo["collection"].update_one.call_args
    filter_doc, update_doc = args[0], args[1]
    assert filter_doc == {"sync_id": "s1"}
    set_payload = update_doc["$set"]
    assert set_payload["status"] == "SUCCESS"
    assert set_payload["result"] == {"inserted": 3}
    assert set_payload["error"] is None
    assert isinstance(set_payload["finished_at"], datetime)
    assert set_payload["duration_ms"] >= 4000
    assert set_payload["duration_ms"] <= 7000


def test_finish_sync_handles_missing_doc(store, mock_mongo):
    mock_mongo["collection"].find_one.return_value = None

    store.finish_sync(sync_id="absent", status="FAILED", error="boom")

    args, _ = mock_mongo["collection"].update_one.call_args
    set_payload = args[1]["$set"]
    assert set_payload["status"] == "FAILED"
    assert set_payload["error"] == "boom"
    assert set_payload["duration_ms"] is None


def test_finish_sync_handles_doc_without_started_at(store, mock_mongo):
    mock_mongo["collection"].find_one.return_value = {"sync_id": "s1"}
    store.finish_sync(sync_id="s1", status="FAILED")
    set_payload = mock_mongo["collection"].update_one.call_args.args[1]["$set"]
    assert set_payload["duration_ms"] is None


def test_update_progress_sets_processed_count(store, mock_mongo):
    store.update_progress(sync_id="s1", processed_count=250)

    mock_mongo["collection"].update_one.assert_called_once_with(
        {"sync_id": "s1"}, {"$set": {"processed_count": 250}}
    )


def test_list_returns_all_when_no_adapter_filter(store, mock_mongo):
    cursor = MagicMock()
    cursor.sort.return_value.limit.return_value = iter([{"sync_id": "s1"}, {"sync_id": "s2"}])
    mock_mongo["collection"].find.return_value = cursor

    result = store.list()

    assert len(result) == 2
    mock_mongo["collection"].find.assert_called_once_with({})


def test_list_filters_by_adapter(store, mock_mongo):
    cursor = MagicMock()
    cursor.sort.return_value.limit.return_value = iter([])
    mock_mongo["collection"].find.return_value = cursor

    store.list(adapter="gh-1", limit=50)

    mock_mongo["collection"].find.assert_called_once_with({"adapter": "gh-1"})
    cursor.sort.return_value.limit.assert_called_once_with(50)


def test_get_returns_sanitized_doc(store, mock_mongo):
    mock_mongo["collection"].find_one.return_value = {"sync_id": "s1", "_id": "skip"}

    result = store.get("s1")

    assert result["sync_id"] == "s1"
    mock_mongo["collection"].find_one.assert_called_once_with({"sync_id": "s1"})


def test_get_returns_none_for_missing_sync(store, mock_mongo):
    mock_mongo["collection"].find_one.return_value = None
    assert store.get("absent") is None
