## Adapter Development Guide

### Creating New Adapters
1. Create new directory under `app/adapters`
2. Implement:
   - `<adapter_name>/adapter.py` with `[Name]Adapter` class
   - `<adapter_name>/schemas.py` with config model
3. Add to registry in `app/adapters/factory.py`

### Required Methods
1. Inherit from `BaseAdapter`
2. Implement required methods:
   - `connect()` - Test connection
   - `fetch_raw()` - Get raw data
   - `normalize()` - Convert to schema

## Example Config
```python
class GitHubConfig(AdapterConfig):
    token: SecretStr
    org: str
    repo: str