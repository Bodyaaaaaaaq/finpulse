"""Реєстрація, вхід, вихід, поточний користувач (ТЗ 5.2, задача BE-2)."""
import os

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.middleware.auth import TOKEN_COOKIE, get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut
from app.services import login_limiter
from app.services.security import TOKEN_LIFETIME, create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# На сервері з HTTPS у .env ставимо COOKIE_SECURE=true, локально - false
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


def _set_token_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        key=TOKEN_COOKIE,
        value=create_token(user.id),
        max_age=int(TOKEN_LIFETIME.total_seconds()),
        httponly=True,  # JavaScript на сторінці не може прочитати токен
        samesite="lax",
        secure=COOKIE_SECURE,
    )


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == data.email)):
        raise HTTPException(status_code=409, detail="Користувач з таким email уже існує")

    user = User(email=data.email, name=data.name.strip(), password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Два одночасні запити з однаковим email
        db.rollback()
        raise HTTPException(status_code=409, detail="Користувач з таким email уже існує")
    db.refresh(user)  # підтягує created_at і points, які заповнює база

    _set_token_cookie(response, user)
    return user


@router.post("/login", response_model=UserOut)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    if login_limiter.is_blocked(data.email):
        minutes = login_limiter.minutes_left(data.email)
        raise HTTPException(status_code=429, detail=f"Забагато спроб входу. Спробуйте через {minutes} хв")

    user = db.scalar(select(User).where(User.email == data.email))
    if user is None or not verify_password(data.password, user.password_hash):
        login_limiter.register_failure(data.email)
        # Однакове повідомлення, щоб не підказувати, чи існує такий email
        raise HTTPException(status_code=401, detail="Неправильний email або пароль")

    login_limiter.reset(data.email)
    _set_token_cookie(response, user)
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(TOKEN_COOKIE)
    return {"message": "Ви вийшли з акаунта"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
