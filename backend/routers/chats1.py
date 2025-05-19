from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import Annotated
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from models import User as UserModel, Chat as ChatModel, Message as MessageModel
from core.security import oauth2_scheme, decode_access_token


router = APIRouter()


class ChatUpdate(BaseModel):
    title: str | None = None
    mode: str | None = None


class Message(BaseModel):
    context: str
    sender: str
    

# Получить все сессии чата текущего пользователя
@router.get("/users/me/chat_sessions", summary="Получить все сессии чата текущего пользователя", tags=["Сессии чата"])
async def get_user_chat_sessions(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Возвращает список всех сессий чата текущего пользователя.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_sessions = session.exec(select(ChatModel).where(ChatModel.user_id == user.id)).all()

    chat_sessions_data = [
        {
            "id": chat_session.id,
            "title": chat_session.title,
            "mode": chat_session.mode,
            "created_at": chat_session.created_at.isoformat()
        } for chat_session in chat_sessions
    ]

    return JSONResponse({"Chats": chat_sessions_data}, status_code=200)


# Добавить новую сессию чата текущему пользователю
@router.post("/users/me/chat_sessions/add", summary="Добавить новую сессию чата текущему пользователю", tags=["Сессии чата"])
async def add_new_chat_session(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Добавляет новую сессию чата текущему пользователю.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    new_chat_session = ChatModel(
        title="Новый чат",
        mode="base",
        user_id=user.id
    )

    session.add(new_chat_session)
    session.commit()
    session.refresh(new_chat_session)

    return JSONResponse({"message": "Сессия чата успешно добавлена", "newChatId": new_chat_session.id}, status_code=201)


# Удалить сессию чата
@router.delete("/users/me/chat_sessions/{session_id}/delete", summary="Удалить сессию чата", tags=["Сессии чата"])
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

    chat_session = session.exec(select(ChatModel).where(ChatModel.id == session_id, ChatModel.user_id == user.id)).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    session.delete(chat_session)
    session.commit()

    return JSONResponse({"message": "Сессия чата успешно удалена"}, status_code=200)


# Обновить информацию о сессии чата
@router.put("/users/me/chat_sessions/{session_id}/update", summary="Обновить информацию о сессии чата", tags=["Сессии чата"])
async def update_chat_session(session_id: int, chat_session_data: ChatUpdate, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
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

    chat_session = session.exec(select(ChatModel).where(ChatModel.id == session_id, ChatModel.user_id == user.id)).first()

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
@router.get("/users/me/chat_sessions/{session_id}/messages", summary="Получить все сообщения текущей сессии чата", tags=["Сообщения"])
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

    chat_session = session.exec(select(ChatModel).where(ChatModel.id == session_id, ChatModel.user_id == user.id)).first()

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
@router.post("/users/me/chat_sessions/{session_id}/messages/add", summary="Добавить новое сообщение к текущей сессии чата", tags=["Сообщения"])
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

    chat_session = session.exec(select(ChatModel).where(ChatModel.id == session_id, ChatModel.user_id == user.id)).first()

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


@router.post("/chat/answer")
async def chat_answer(request: ChatRequest, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Генерирует ответ на основе текста и ID сессии чата.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)
    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat_sess = session.exec(select(ChatModel).where(ChatModel.id == request.chat_id, ChatModel.user_id == user.id)).first()
    if not chat_sess:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    # ─── 3. генерируем ответ целиком ───
    answer_text: str = await run_in_threadpool(generate_once, request.text)

    return JSONResponse({"answer": answer_text})