from fastapi import HTTPException, APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError

from app.auth.security import create_access_token, verify_password, hash_password, create_refresh_token, decode_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# simple admin
fake_user = {
    "username": "admin",
    "hashed_password": hash_password('admin123'),

}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != fake_user["username"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username")
    if not verify_password(form_data.password, fake_user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

    access_token = create_access_token(data={"sub": fake_user["username"]})
    refresh_token = create_refresh_token(data={"sub": fake_user["username"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_token(token: str):
    try:
        payload = decode_token(token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect token type")

        user_name = payload.get("sub")
        access_token = create_access_token(data={"username": user_name})

        return {"access_token": access_token}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
