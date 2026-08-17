"""Unit tests for AssetStore (app/storage/assets.py).

All MongoDB calls are mocked via pytest-mock. The integration suite
exercises the real-DB path; these tests verify call shapes and code paths.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pymongo.errors import BulkWriteError, PyMongoError

from app.models.assets import NormalizedAsset


@pytest.fixture
def mock_mongo(mocker):
    """Patch get_mongo_client + return the fake collection for assertions."""
    fake_collection = MagicMock(name="assets_collection")
    fake_db = MagicMock(name="db")
    fake_db.assets = fake_collection
    fake_db.__getitem__.return_value = fake_collection

    fake_client = MagicMock(name="mongo_client")
    fake_client.__getitem__.return_value = fake_db

    mocker.patch("app.storage.assets.get_mongo_client", return_value=fake_client)
    return {"client": fake_client, "db": fake_db, "collection": fake_collection}


@pytest.fixture
def store(mock_mongo):
    from app.storage.assets import AssetStore

    # _indexes_created is a process-level guard (real createIndexes should only run once per
    # process, not once per AssetStore() instantiation) -- reset it so each test deterministically
    # observes index creation regardless of what ran earlier in the same pytest session.
    AssetStore._indexes_created = False
    return AssetStore()


@pytest.fixture
def sample_asset():
    return NormalizedAsset(
        asset_id="aws_ec2_i-1234",
        customer_id="acme",
        name="web-1",
        asset_type="ec2",
        status="RUNNING",
        last_seen=datetime(2024, 1, 1),
        vendor="AWS",
        metadata={"instance_type": "t3.micro"},
    )


def test_construction_creates_three_indexes(mock_mongo):
    from app.storage.assets import AssetStore

    AssetStore._indexes_created = False
    AssetStore()
    assert mock_mongo["db"].assets.create_index.call_count == 3


def test_store_assets_happy_path(store, mock_mongo, sample_asset):
    fake_result = MagicMock()
    fake_result.bulk_api_result = {"nInserted": 1, "nModified": 0}
    mock_mongo["db"].assets.bulk_write.return_value = fake_result

    result = store.store_assets([sample_asset])

    assert result == {"nInserted": 1, "nModified": 0}
    mock_mongo["db"].assets.bulk_write.assert_called_once()
    args, kwargs = mock_mongo["db"].assets.bulk_write.call_args
    assert len(args[0]) == 1
    # independent upserts (unique-indexed by asset_id+customer_id) -- out-of-order execution is
    # safe and faster at scale, no correctness downside.
    assert kwargs["ordered"] is False


def test_store_assets_propagates_bulk_write_error(store, mock_mongo, sample_asset):
    mock_mongo["db"].assets.bulk_write.side_effect = BulkWriteError({"writeErrors": []})
    with pytest.raises(BulkWriteError):
        store.store_assets([sample_asset])


def test_store_assets_propagates_pymongo_error(store, mock_mongo, sample_asset):
    mock_mongo["db"].assets.bulk_write.side_effect = PyMongoError("boom")
    with pytest.raises(PyMongoError):
        store.store_assets([sample_asset])


def test_find_assets_enriches_query_with_customer_id(store, mock_mongo):
    cursor = MagicMock()
    cursor.sort.return_value.skip.return_value.limit.return_value.max_time_ms.return_value = iter(
        []
    )
    mock_mongo["db"].assets.find.return_value = cursor

    store.find_assets({"asset_type": "ec2"}, skip=10, limit=5)

    called_query = mock_mongo["db"].assets.find.call_args.args[0]
    assert called_query["asset_type"] == "ec2"
    assert "customer_id" in called_query


def test_get_asset_passes_filter_and_max_time(store, mock_mongo):
    mock_mongo["db"].assets.find_one.return_value = {"asset_id": "x"}

    result = store.get_asset("x")

    assert result == {"asset_id": "x"}
    args, kwargs = mock_mongo["db"].assets.find_one.call_args
    assert args[0]["asset_id"] == "x"
    assert "customer_id" in args[0]
    assert kwargs.get("maxTimeMS") == 200


def test_get_asset_history_returns_list_with_projection(store, mock_mongo):
    mock_mongo["db"].assets.find.return_value = iter(
        [{"version": 1, "_last_modified": datetime(2024, 1, 1)}]
    )

    history = store.get_asset_history("x")

    assert isinstance(history, list)
    assert history[0]["version"] == 1
    args, kwargs = mock_mongo["db"].assets.find.call_args
    assert args[0]["asset_id"] == "x"
    assert kwargs["projection"]["version"] == 1


def test_normalize_asset_reshapes_doc(store):
    doc = {
        "asset_id": "x1",
        "asset_type": "ec2",
        "status": "RUNNING",
        "name": "web-1",
        "vendor": "AWS",
        "last_seen": datetime(2024, 1, 1),
        "metadata": {"k": "v"},
    }
    out = store._normalize_asset(doc)
    assert out["id"] == "x1"
    assert out["type"] == "ec2"
    assert out["data"]["vendor"] == "AWS"
    assert out["data"]["metadata"] == {"k": "v"}


def test_normalize_asset_handles_missing_metadata(store):
    doc = {
        "asset_id": "x2",
        "asset_type": "ec2",
        "status": "RUNNING",
        "name": "web-2",
        "vendor": "AWS",
        "last_seen": datetime(2024, 1, 1),
    }
    out = store._normalize_asset(doc)
    assert out["data"]["metadata"] == {}


def test_count_assets_enriches_query_with_customer_id(store, mock_mongo):
    mock_mongo["db"].assets.count_documents.return_value = 42

    result = store.count_assets({"asset_type": "user"})

    assert result == 42
    args, kwargs = mock_mongo["db"].assets.count_documents.call_args
    assert "customer_id" in args[0]
    assert kwargs["maxTimeMS"] == 500
