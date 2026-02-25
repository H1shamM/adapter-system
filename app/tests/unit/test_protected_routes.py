from fastapi.testclient import TestClient
from app.api.main import app
from app.auth.security import create_access_token

client = TestClient(app)


def test_protected_route_requires_token():
    response = client.get('/api/v1/syncs/history')

    assert response.status_code == 401


def test_protected_route_with_token():
    token = create_access_token({'sub': 'admin'})
    response = client.get(
        '/api/v1/syncs/history',
        headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code in (200, 404)
