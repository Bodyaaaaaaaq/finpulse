"""Профіль: зміна імені/email, зміна пароля, видалення акаунта (ТЗ 5.2, задача BE-3).

Усі адреси вимагають входу (CurrentUser), інакше 401.
"""
from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies import DbSession
from app.middleware.auth import TOKEN_COOKIE, CurrentUser
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.profile import AccountDelete, PasswordChange, ProfileUpdate
from app.services.security import hash_password, verify_password

router = APIRouter(prefix="/profile", tags=["profile"])

EMAIL_TAKEN = "Користувач з таким email уже існує"


@router.patch("", response_model=UserOut)
def update_profile(data: ProfileUpdate, user: CurrentUser, db: DbSession):
    if data.email is not None and data.email != user.email:
        taken = db.scalar(select(User.id).where(User.email == data.email))
        if taken:
            raise HTTPException(status_code=409, detail=EMAIL_TAKEN)
        user.email = data.email

    if data.name is not None:
        user.name = data.name

    try:
        db.commit()
    except IntegrityError:
        # Хтось зайняв цей email між перевіркою і збереженням
        db.rollback()
        raise HTTPException(status_code=409, detail=EMAIL_TAKEN) from None
    db.refresh(user)
    return user


@router.patch("/password")
def change_password(data: PasswordChange, user: CurrentUser, db: DbSession):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неправильний поточний пароль")

    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Пароль змінено"}


@router.delete("")
def delete_account(data: AccountDelete, response: Response, user: CurrentUser, db: DbSession):
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неправильний пароль")

    # Решту зробить база (зовнішні ключі з DB-8, DB-10, DB-7):
    # conversion_history і user_rewards видаляються (CASCADE),
    # у game_items зібрані предмети залишаються, collected_by_user_id стає NULL (SET NULL).
    db.delete(user)
    db.commit()
    response.delete_cookie(TOKEN_COOKIE)
    return {"message": "Акаунт видалено"}
