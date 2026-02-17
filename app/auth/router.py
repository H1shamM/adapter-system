from fastapi import HTTPException, APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.security import create_access_token,verify_password, hash_password

router = APIRouter(prefix="/auth",tags=["Auth"])

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

    return {"access_token": access_token, "token_type": "bearer"}