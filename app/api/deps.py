from app.storage.adapters import AdapterConfigStore
from app.storage.assets import AssetStore
from app.storage.sync_history import SyncHistoryStore


def get_asset_store():
    return AssetStore()


def get_adapter_config_store():
    return AdapterConfigStore()

def get_sync_history_store():
    return SyncHistoryStore()