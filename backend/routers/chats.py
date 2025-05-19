from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import Annotated
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from models import User as UserModel, Chat as ChatModel, Message as MessageModel, UserWork as UserWorkModel
from core.security import oauth2_scheme, decode_access_token
from model_utils import generate_once


router = APIRouter()

class Message(BaseModel):
    text: str


# Получить или создать чат для работы
@router.get("/work/{work_id}/chat", summary="Получить или создать чат для работы", tags=["Чаты"])
async def get_or_create_chat(work_id: int, token: Annotated[str, Depends(oauth2_scheme)], mode: str = Query("help"), session: Session = Depends(get_session)):
    """
    Получает чат, включая все сообщения, или создаёт новый чат для работы, если его ещё нет.
    Доступен только студенту, назначенному на работу.
    Требуется авторизация с использованием токена доступа.

    Параметр пути:
    - **work_id**: ID работы, для которой создаётся или получается чат
    - **mode**: режим работы (по умолчанию "help")
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем доступ
    uw = session.exec(select(UserWorkModel).where(UserWorkModel.work_id == work_id, UserWorkModel.student_id == user.id)).first()
    if not uw:
        raise HTTPException(403, "Нет доступа")

    chat = session.exec(select(ChatModel).where(ChatModel.user_id == user.id, ChatModel.mode == mode, ChatModel.document_data == None, ChatModel.work_id == work_id)).first()

    if not chat:
        chat = ChatModel(user_id=user.id, work_id=work_id, mode=mode)
        session.add(chat)
        session.commit()
        session.refresh(chat)

    messages = session.exec(select(MessageModel).where(MessageModel.chat_id == chat.id).order_by(MessageModel.created_at)).all()

    return {"chat_id": chat.id,
            "messages": [{
                "id": message.id,
                "sender": message.sender,
                "context": message.text,
                "created_at": message.created_at.isoformat()
            } for message in messages]}


# Добавить сообщение от пользователя и получить сообщение от LLM
@router.post("/chat/{chat_id}/messages/add", summary="Добавить сообщение от пользователя и получить сообщение от LLM", tags=["Чаты"])
async def add_message(chat_id: int, message_data: Message, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Сохраняем сообщение пользователя и вызываем LLM.
    Возвращаем ответ LLM и сообщение пользователя.
    Требуется авторизация с использованием токена доступа.

    Поля для добавления сообщения:
    - **text**: текст сообщения пользователя

    Параметр пути:
    - **chat_id**: ID чата, в который добавляется сообщение
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # проверяем, что чат принадлежит пользователю
    chat = session.get(ChatModel, chat_id)
    if not chat or chat.user_id != user.id:
        raise HTTPException(404, "Чат не найден")

    # Сохраняем сообщение пользователя
    user_message = MessageModel(chat_id=chat_id, sender="user", text=message_data.text)
    session.add(user_message); 
    session.commit(); 
    session.refresh(user_message)

    # Генерируем ответ 
    ai_text: str = await run_in_threadpool(generate_once, message_data.text)

    ai_message = MessageModel(chat_id=chat_id, sender="ai", text=ai_text)
    session.add(ai_message)
    session.commit()
    session.refresh(ai_message)

    return JSONResponse({
        "user_message": {
            "id": user_message.id,
            "sender": "user",
            "context": user_message.text,
            "created_at": user_message.created_at.isoformat()
        },
        "ai_message": {
            "id": ai_message.id,
            "sender": "ai",
            "context": ai_message.text,
            "created_at": ai_message.created_at.isoformat()
        }
    }, status_code=201)
