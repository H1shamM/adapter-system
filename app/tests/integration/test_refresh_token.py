from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_refresh_token_flow():
    response = client.post(
        '/api/v1/auth/login',
        data={"username": "admin", "password": "admin123"}
    )

    tokens = response.json()
    refresh_token = tokens['refresh_token']

    refresh_res = client.post(
        '/api/v1/auth/refresh',
        data={"token": refresh_token}
    )

    assert refresh_res.status_code == 200

    body = refresh_res.json()
    print(body)
    assert "access_token" in body
    assert body["token_type"] == "bearer"

def test_refresh_token_invalid():
    response = client.post(
        '/api/v1/auth/refresh',
        data={"token": "invalid-token"}
    )

    assert response.status_code == 401