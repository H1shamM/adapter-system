import json

import pandas as pd
import plotly.express as px


from app.adapters.JSONPlaceholder.adapter import JSONPlaceholderAdapter
from app.adapters.base import AdapterConfig

with open("configs/jsonplaceholder_config.json") as f:
    config_data = json.load(f)

config = AdapterConfig(**config_data)
assets = JSONPlaceholderAdapter(config=config).execute()

from app.adapters.coingecko.adapter import CoinGeckoAdapter

with open("configs/coingecko_config.json") as f:
    coingecko_config = json.load(f)

coingecko_config_data = AdapterConfig(**coingecko_config)

coin_assets = CoinGeckoAdapter(config=coingecko_config_data).execute()


assets.extend(coin_assets)

if not assets:
    print("No assets found")
    exit(1)

df = pd.DataFrame([{
    "asset_id": asset.asset_id,
    "name": asset.name,
    "type": asset.asset_type,
    "vendor": asset.vendor,
    "last_seen": asset.last_seen,
} for asset in assets])

df['last_seen'] = pd.to_datetime(df['last_seen'])

fig_type = px.pie(df, names='type', title='Assets By Type')
fig_type.show()

vendor_counts = df.groupby('vendor').size().reset_index(name='count')
fig_vendor = px.bar(vendor_counts, x='vendor', y='count',title = 'Number of Assets By vendor',
                    labels={'count': 'Count of Assets '})
fig_vendor.show()

time_series = df.groupby(df['last_seen'].dt.date).size().reset_index(name='count')
fig_time = px.line(time_series, x='last_seen', y='count',title='Assets Synced over Time')
fig_time.show()