from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Annotated
from passlib.context import CryptContext
import jwt
from database import get_session
from models import User as UserModel, Chat as ChatModel, Message as MessageModel, Discipline as DisciplineModel, Document as DocumentModel, Work as WorkModel
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone


app = FastAPI(title="API NeuroTutor", description="API для цифрового помощника", version="3.1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:5173", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Token(BaseModel):
    access_token: str
    token_type: str | None = None


class User(BaseModel):
    last_name: str
    first_name: str
    login: str
    role: str
    password: str


class UserUpdate(BaseModel):
    last_name: str | None = None
    first_name: str | None = None
    login: str | None = None
    password: str | None = None


class ChatSessionUpdate(BaseModel):
    title: str | None = None
    mode: str | None = None


class Message(BaseModel):
    context: str
    sender: str


SECRET_KEY = "diplom"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен истек",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Зарегистрировать пользователя
@app.post("/users/register", summary="Регистрация пользователя", tags=["Пользователи"])
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
@app.post("/users/login", summary="Авторизация пользователя", tags=["Пользователи"])
async def login_user(user_data: User, session: Session = Depends(get_session)):
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
@app.get("/users/me", summary="Получить инфорацию о текущем пользователе", tags=["Пользователи"])
async def get_info_about_me(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
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
@app.delete("/users/me/delete", summary="Удалить текущего пользователя", tags=["Пользователи"])
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


# Обновить инфорацию о пользователе
@app.put("/users/me/update", summary="Обновить информацию о текущем пользователе", tags=["Пользователи"])
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

    if not user_data.login and not user_data.password:
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

    session.add(user)
    session.commit()
    session.refresh(user)

    if user_data.login and user_data.login != old_login:
        new_token = create_access_token(data={"sub": user_data.login})
        return JSONResponse({"message": "Пользователь успешно обновлен", "new_token": new_token}, status_code=200)

    return JSONResponse({"message": "Пользователь успешно обновлен"}, status_code=200)


# Получить все сессии чата текущего пользователя
@app.get("/users/me/chat_sessions", summary="Получить все сессии чата текущего пользователя", tags=["Сессии чата"])
async def get_user_chat_sessions(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Возвращает список всех сессий чата текущего пользователя.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_sessions = session.exec(select(ChatSessionModel).where(ChatSessionModel.user_id == user.id)).all()

    chat_sessions_data = [
        {
            "id": chat_session.id,
            "title": chat_session.title,
            "mode": chat_session.mode,
            "created_at": chat_session.created_at.isoformat()
        } for chat_session in chat_sessions
    ]

    return JSONResponse({"ChatSessions": chat_sessions_data}, status_code=200)


# Добавить новую сессию чата текущему пользователю
@app.post("/users/me/chat_sessions/add", summary="Добавить новую сессию чата текущему пользователю", tags=["Сессии чата"])
async def add_new_chat_session(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Добавляет новую сессию чата текущему пользователю.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    new_chat_session = ChatSessionModel(
        title="Новый чат",
        mode="base",
        user_id=user.id
    )

    session.add(new_chat_session)
    session.commit()
    session.refresh(new_chat_session)

    return JSONResponse({"message": "Сессия чата успешно добавлена", "newChatSessionId": new_chat_session.id}, status_code=201)


# Удалить сессию чата
@app.delete("/users/me/chat_sessions/{session_id}/delete", summary="Удалить сессию чата", tags=["Сессии чата"])
async def delete_chat_session(session_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Удаляет сессию чата по её ID.
    Требуется авторизация с использованием токена доступа.

    Параметр пути: **session_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_session = session.exec(select(ChatSessionModel).where(ChatSessionModel.id == session_id, ChatSessionModel.user_id == user.id)).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    session.delete(chat_session)
    session.commit()

    return JSONResponse({"message": "Сессия чата успешно удалена"}, status_code=200)


# Обновить информацию о сессии чата
@app.put("/users/me/chat_sessions/{session_id}/update", summary="Обновить информацию о сессии чата", tags=["Сессии чата"])
async def update_chat_session(session_id: int, chat_session_data: ChatSessionUpdate, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Обновляет информацию о сессии чата по её ID.
    Требуется авторизация с использованием токена доступа.

    Поля для обновления:
    - **title**: Название сессии
    - **mode**: Режим работы модели
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_session = session.exec(select(ChatSessionModel).where(ChatSessionModel.id == session_id, ChatSessionModel.user_id == user.id)).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    if chat_session_data.title:
        chat_session.title = chat_session_data.title
    if chat_session_data.mode:
        chat_session.mode = chat_session_data.mode

    session.add(chat_session)
    session.commit()

    return JSONResponse({"message": "Сессия чата успешно обновлена"}, status_code=200)


# Получить все сообщения текущей сессии
@app.get("/users/me/chat_sessions/{session_id}/messages", summary="Получить все сообщения текущей сессии чата", tags=["Сообщения"])
async def get_chat_session_messages(session_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Возвращает список всех сообщений текущей сессии чата.
    Требуется авторизация с использованием токена доступа.

    Параметр пути: **session_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_session = session.exec(select(ChatSessionModel).where(ChatSessionModel.id == session_id, ChatSessionModel.user_id == user.id)).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    messages = session.exec(select(MessageModel).where(MessageModel.chat_session_id == chat_session.id)).all()

    messages_data = [
        {
            "id": message.id,
            "context": message.context,
            "sender": message.sender,
            "created_at": message.created_at.isoformat()
        } for message in messages
    ]

    return JSONResponse({"Messages": messages_data}, status_code=200)


# Добавить новое сообщение к текущей сессии чата
@app.post("/users/me/chat_sessions/{session_id}/messages/add", summary="Добавить новое сообщение к текущей сессии чата", tags=["Сообщения"])
async def add_new_message(session_id: int, message_data: Message, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Добавляет новое сообщение к текущей сессии чата.
    Требуется авторизация с использованием токена доступа.

    Поля для добавления сообщения:
    - **context**: Текст сообщения
    - **sender**: Отправитель сообщения (ai или user)
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_session = session.exec(select(ChatSessionModel).where(ChatSessionModel.id == session_id, ChatSessionModel.user_id == user.id)).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    new_message = MessageModel(
        context=message_data.context,
        sender=message_data.sender,
        chat_session_id=chat_session.id
    )

    session.add(new_message)
    session.commit()
    session.refresh(new_message)

    return JSONResponse({"message": "Сообщение успешно добавлено"}, status_code=201)


from pydantic import BaseModel
from model_utils import generate_once


class ChatRequest(BaseModel):
    chat_id: int
    text: str
    mode: str | None = "base"


@app.post("/chat/answer")
async def chat_answer(request: ChatRequest, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Генерирует ответ на основе текста и ID сессии чата.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)
    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_sess = session.exec(select(ChatSessionModel).where(ChatSessionModel.id == request.chat_id, ChatSessionModel.user_id == user.id)).first()
    if not chat_sess:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    # ─── 3. генерируем ответ целиком ───
    answer_text: str = await run_in_threadpool(generate_once, request.text)

    return JSONResponse({"answer": answer_text})