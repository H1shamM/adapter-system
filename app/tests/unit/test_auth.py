from datetime import timedelta

import pytest
from jose import jwt, JWTError

from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)


def test_password_hash_and_verify():
    password = "secret123"
    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password)


def test_password_verify_fails_for_wrong_password():
    password = "secret123"
    hashed_password = hash_password(password)

    assert not verify_password("wrongpassword", hashed_password)


def test_create_access_token_contains_subject():
    token = create_access_token({"sub": "admin"})

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )

    assert payload["sub"] == "admin"


def test_expired_access_token_rejected():
    token = create_access_token({"sub": "admin"}, expires_delta=timedelta(seconds=-1))

    with pytest.raises(JWTError):
        jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
