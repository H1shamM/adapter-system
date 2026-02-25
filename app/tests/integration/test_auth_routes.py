from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

def test_login_success():

    response = client.post(
        'api/v1/auth/login',
        data={'username': 'admin', 'password': 'admin123'}
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"

def test_login_failure():
    response = client.post(
        'api/v1/auth/login',
        data={'username': 'admin', 'password': 'wrong'}
    )

    assert response.status_code == 401


