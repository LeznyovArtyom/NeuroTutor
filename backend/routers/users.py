from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Annotated
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from models import User as UserModel
from datetime import timedelta
from core.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme, decode_access_token


router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str | None = None


class User(BaseModel):
    last_name: str
    first_name: str
    role: str
    login: str
    password: str


class UserLogin(BaseModel):
    login: str
    password: str


class UserUpdate(BaseModel):
    last_name: str | None = None
    first_name: str | None = None
    login: str | None = None
    password: str | None = None


# Зарегистрировать пользователя
@router.post("/users/register", summary="Регистрация пользователя", tags=["Пользователи"])
async def register_new_user(user_data: User, session: Session = Depends(get_session)):
    """
    Регистрирует нового пользователя в системе.
    
    - **last_name**: фамилия пользователя
    - **first_name**: имя пользователя
    - **role**: роль пользователя
    - **login**: уникальный логин
    - **password**: пароль пользователя
    """
    
    existing_user = session.exec(select(UserModel).where(UserModel.login == user_data.login)).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Пользователь с таким логином уже существует")
    
    hashed_password = get_password_hash(user_data.password)

    new_user = UserModel(
        last_name=user_data.last_name,
        first_name=user_data.first_name,
        role=user_data.role,
        login=user_data.login,
        password=hashed_password
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return JSONResponse({"message": "Пользователь успешно зарегистрирован"}, status_code=201)


# Авторизовать пользователя
@router.post("/users/login", summary="Авторизация пользователя", tags=["Пользователи"])
async def login_user(user_data: UserLogin, session: Session = Depends(get_session)):
    """
    Авторизует пользователя и возвращает токен доступа.

    - **login**: логин пользователя
    - **password**: пароль пользователя
    """
    user = session.exec(select(UserModel).where(UserModel.login == user_data.login)).first()

    if user and verify_password(user_data.password, user.password):
        access_token = create_access_token(data={"sub": user_data.login}, expires_delta=timedelta(ACCESS_TOKEN_EXPIRE_MINUTES))
        return JSONResponse({"access_token": access_token, "token_type": "bearer"})
    else:
        raise HTTPException(status_code=401, detail="Неправильные данные для входа")


# Получить информацию о пользователе
@router.get("/users/me", summary="Получить инфорацию о текущем пользователе", tags=["Пользователи"])
async def get_user_info(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Возвращает информацию о пользователе.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if user:
        return JSONResponse({"User": {
            "id": user.id,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "role": user.role,
            "login": user.login
        }})
    return JSONResponse({"error": "Пользователь не найден"}, status_code=404)


# Удалить пользователя
@router.delete("/users/me/delete", summary="Удалить текущего пользователя", tags=["Пользователи"])
async def delete_user(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Удаляет текущего пользователя из системы.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    session.delete(user)
    session.commit()

    return JSONResponse({"message": "Пользователь удален"}, status_code=200)


# Обновить информацию о пользователе
@router.put("/users/me/update", summary="Обновить информацию о текущем пользователе", tags=["Пользователи"])
async def update_user(user_data: UserUpdate, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Обновляет информацию о текущем пользователе
    Требуется авторизация с использованием токена доступа.

    Поля для обновления:
    - **last_name**: Фамилия пользователя
    - **first_name**: Имя пользователя
    - **login**: Логин пользователя
    - **password**: Пароль
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if not user_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    
    old_login = user.login

    # Проверка на уникальность логина, если он меняется
    if user_data.login and user_data.login != old_login:
        existing_user = session.exec(select(UserModel).where(UserModel.login == user_data.login)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Логин уже используется")
        user.login = user_data.login
    if user_data.password:
        user.password = get_password_hash(user_data.password)
    if user_data.last_name:
        user.last_name = user_data.last_name
    if user_data.first_name:
        user.first_name = user_data.first_name

    session.add(user)
    session.commit()
    session.refresh(user)

    if user_data.login and user_data.login != old_login:
        new_token = create_access_token(data={"sub": user_data.login})
        return JSONResponse({"message": "Пользователь успешно обновлен", "new_token": new_token}, status_code=200)

    return JSONResponse({"message": "Пользователь успешно обновлен"}, status_code=200)
