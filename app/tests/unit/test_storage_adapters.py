"""Unit tests for AdapterConfigStore (app/storage/adapters.py)."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_mongo(mocker):
    fake_collection = MagicMock(name="adapters_collection")
    fake_db = MagicMock(name="db")
    fake_db.adapters = fake_collection
    fake_db.__getitem__.return_value = fake_collection

    fake_client = MagicMock(name="mongo_client")
    fake_client.__getitem__.return_value = fake_db

    mocker.patch("app.storage.adapters.get_mongo_client", return_value=fake_client)
    return {"client": fake_client, "db": fake_db, "collection": fake_collection}


@pytest.fixture
def store(mock_mongo):
    from app.storage.adapters import AdapterConfigStore

    return AdapterConfigStore()


def test_create_indexes_creates_three_indexes(store, mock_mongo):
    store.create_indexes()
    assert mock_mongo["collection"].create_index.call_count == 3


def test_upsert_writes_full_doc_with_meta(store, mock_mongo):
    store.upsert(adapter_id="gh-1", adapter_type="github", config={"repo": "x/y"})

    mock_mongo["collection"].update_one.assert_called_once()
    args, kwargs = mock_mongo["collection"].update_one.call_args
    filter_doc = args[0]
    update_doc = args[1]
    assert filter_doc == {"adapter_id": "gh-1"}
    set_payload = update_doc["$set"]
    assert set_payload["adapter_id"] == "gh-1"
    assert set_payload["adapter_type"] == "github"
    assert set_payload["repo"] == "x/y"
    assert isinstance(set_payload["updated_at"], datetime)
    assert kwargs.get("upsert") is True


def test_get_returns_sanitized_doc(store, mock_mongo):
    raw_doc = {"_id": "ignored", "adapter_id": "gh-1", "adapter_type": "github"}
    mock_mongo["collection"].find_one.return_value = raw_doc

    result = store.get("gh-1")

    assert result["adapter_id"] == "gh-1"
    mock_mongo["collection"].find_one.assert_called_once_with({"adapter_id": "gh-1"})


def test_get_returns_none_when_doc_missing(store, mock_mongo):
    mock_mongo["collection"].find_one.return_value = None
    assert store.get("absent") is None


def test_get_by_type_returns_list(store, mock_mongo):
    mock_mongo["collection"].find.return_value = iter(
        [
            {"adapter_id": "gh-1", "adapter_type": "github"},
            {"adapter_id": "gh-2", "adapter_type": "github"},
        ]
    )

    result = store.get_by_type("github")

    assert len(result) == 2
    mock_mongo["collection"].find.assert_called_once_with({"adapter_type": "github"})


def test_list_all_returns_list(store, mock_mongo):
    mock_mongo["collection"].find.return_value = iter([{"adapter_id": "x"}])

    result = store.list_all()

    assert len(result) == 1
    mock_mongo["collection"].find.assert_called_once_with()


def test_delete_calls_delete_one(store, mock_mongo):
    store.delete("gh-1")
    mock_mongo["collection"].delete_one.assert_called_once_with({"adapter_id": "gh-1"})


def test_set_next_sync_uses_set_and_setoninsert(store, mock_mongo):
    before = datetime.utcnow()
    store.set_next_sync("gh-1", sync_interval=600)
    after = datetime.utcnow()

    args, kwargs = mock_mongo["collection"].update_one.call_args
    filter_doc, update_doc = args[0], args[1]
    assert filter_doc == {"adapter_id": "gh-1"}
    next_sync = update_doc["$set"]["next_sync"]
    assert before + timedelta(seconds=600) - timedelta(seconds=2) <= next_sync
    assert next_sync <= after + timedelta(seconds=600) + timedelta(seconds=2)
    assert update_doc["$setOnInsert"]["last_sync"] is None
    assert kwargs.get("upsert") is True


def test_get_due_adapters_filters_enabled_and_due(store, mock_mongo):
    mock_mongo["collection"].find.return_value = iter([{"adapter_id": "gh-1", "next_sync": None}])

    result = store.get_due_adapters()

    assert len(result) == 1
    query = mock_mongo["collection"].find.call_args.args[0]
    assert query["enabled"] is True
    assert "$or" in query


def test_update_after_sync_when_adapter_exists(store, mock_mongo):
    mock_mongo["collection"].find_one.return_value = {
        "adapter_id": "gh-1",
        "sync_interval": 1800,
    }
    store.update_after_sync("gh-1")

    mock_mongo["collection"].update_one.assert_called_once()
    args, _ = mock_mongo["collection"].update_one.call_args
    filter_doc, update_doc = args[0], args[1]
    assert filter_doc == {"adapter_id": "gh-1"}
    assert "last_sync" in update_doc["$set"]
    assert "next_sync" in update_doc["$set"]


def test_update_after_sync_does_nothing_when_adapter_missing(store, mock_mongo):
    mock_mongo["collection"].find_one.return_value = None
    store.update_after_sync("absent")
    mock_mongo["collection"].update_one.assert_not_called()


def test_update_after_sync_uses_default_interval_when_missing(store, mock_mongo):
    """If sync_interval isn't on the doc, defaults to 3600s."""
    mock_mongo["collection"].find_one.return_value = {"adapter_id": "gh-1"}
    before = datetime.utcnow()
    store.update_after_sync("gh-1")
    after = datetime.utcnow()

    args, _ = mock_mongo["collection"].update_one.call_args
    next_sync = args[1]["$set"]["next_sync"]
    assert before + timedelta(seconds=3600) - timedelta(seconds=2) <= next_sync
    assert next_sync <= after + timedelta(seconds=3600) + timedelta(seconds=2)
