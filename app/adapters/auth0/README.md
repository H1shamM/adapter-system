# Auth0 Adapter

## Overview

Ingests users (and their role assignments) from the Auth0 Management API into `NormalizedAsset`.

## Setup

1. In the Auth0 dashboard: **Applications -> Create Application -> Machine to Machine**, authorize it
   for the **Auth0 Management API**, and grant `read:users` + `read:roles` scopes.
2. Note the tenant **Domain**, **Client ID**, and **Client Secret** from the application's Settings tab.
3. Set env vars (never commit real values): `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`.
4. See `configs/auth0_sample.json` for the config shape — secrets are referenced via `VAR:` indirection
   (resolved from the env vars above at runtime, see `AssetHttpClient._resolve_secret`).

## Auth

OAuth2 client-credentials grant (`oauth2_client_credentials` auth type, added to the shared
`AssetHttpClient` rather than special-cased here — see `app/http/client.py`). The token is fetched by
`ensure_token()`, called at the start of `connect()`.

## The interesting design decision

A user's role assignments come from a **separate** endpoint (`/api/v2/roles/{id}/users`), not the user
object itself. `fetch_raw()` fetches all roles once, fetches each role's users once, and inverts the
result into a `{user_id: [role_names]}` map — instead of calling a per-user roles endpoint once per user
(N+1, expensive at scale).

## Known operational gotchas (learned the hard way)

- **M2M grant propagation delay**: a newly authorized Machine-to-Machine application's token requests
  can 401 for up to a minute or two after creation before the grant is fully active. Not a bug — retry
  after a short wait.
- **List/search endpoint is eventually consistent**: `GET /api/v2/users` uses a search index that can
  lag behind writes; a newly created user may not appear in the list for a short time even though it's
  immediately fetchable by direct ID (`GET /api/v2/users/{id}`).
- **Hard pagination limit**: Auth0 refuses to paginate past the first 1000 records
  (`invalid_paging` error). The shared `page_number` pagination strategy in `AssetHttpClient` now stops
  once a page returns fewer than a full page of results, instead of blindly walking to `max_pages`.

## Testing

```bash
pytest app/tests/adapters/test_auth0_adapter.py
pytest app/tests/contract/test_adapter_contract.py -k auth0
```
