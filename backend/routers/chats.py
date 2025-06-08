from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Annotated
from pydantic import BaseModel
from sqlmodel import Session, select
from database.database import get_session
from database.sql_models import User as UserModel, Chat as ChatModel, Message as MessageModel, UserWork as UserWorkModel, ChatStage, WorkStatus
from core.security import oauth2_scheme, decode_access_token
from llm.assistant_core import handle_checking_the_work_stage, handle_checking_the_corrected_work_stage, dialogue, set_user_work_status


router = APIRouter()

class Message(BaseModel):
    text: str


# Получить или создать чат для работы
@router.get("/work/{work_id}/chat", summary="Получить или создать чат для работы", tags=["Чаты"])
async def get_or_create_chat(work_id: int, token: Annotated[str, Depends(oauth2_scheme)], mode: str = Query("acceptance of work"), session: Session = Depends(get_session)):
    """
    Получает чат, включая все сообщения, или создаёт новый чат для работы, если его ещё нет.
    Доступен только студенту, назначенному на работу.
    Требуется авторизация с использованием токена доступа.

    Параметр пути:
    - **work_id**: ID работы, для которой создаётся или получается чат
    - **mode**: режим работы (по умолчанию "acceptance of work")
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем доступ
    uw = session.exec(select(UserWorkModel).where(UserWorkModel.work_id == work_id, UserWorkModel.student_id == user.id)).first()
    if not uw:
        raise HTTPException(403, "Нет доступа")

    chat = session.exec(select(ChatModel).where(ChatModel.user_id == user.id, ChatModel.mode == mode, ChatModel.work_id == work_id)).first()

    if not chat:
        chat = ChatModel(user_id=user.id, work_id=work_id, mode=mode)
        session.add(chat)
        session.commit()
        session.refresh(chat)

    messages = session.exec(select(MessageModel).where(MessageModel.chat_id == chat.id).order_by(MessageModel.created_at)).all()

    return {"chat_id": chat.id,
            "stage": chat.stage,
            "document_name": chat.document_name,
            "messages": [{
                "id": message.id,
                "sender": message.sender,
                "context": message.text,
                "created_at": message.created_at.isoformat()
            } for message in messages]}


# Добавить сообщение от пользователя и получить сообщение от LLM
@router.post("/chat/{chat_id}/messages/add", summary="Добавить сообщение от пользователя и получить сообщение от LLM", tags=["Чаты"])
async def add_message_and_generate_answer(chat_id: int, message_data: Message, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
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
    if message_data.text:
        user_message = MessageModel(chat_id=chat_id, sender="user", text=message_data.text)
        session.add(user_message); 
        session.commit(); 
        session.refresh(user_message)
    else:
        user_message = None

    # Проверяем ответ студента и составляем статистику
    ai_text = await dialogue(chat, message_data.text, session)

    # Сохраняем ответ модели
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
        },
        "chat": {
            "stage": chat.stage
        }
    }, status_code=200)


# Загрузка файла работы и запуск проверки
@router.post("/chat/{chat_id}/upload", summary="Загрузить файл работы и запустить проверку", tags=["Чаты"])
async def upload_work(chat_id: int, token: Annotated[str, Depends(oauth2_scheme)], file: UploadFile = File(...), session: Session = Depends(get_session)):
    """
    Принимает файл (PDF / DOCX / TXT), сохраняет в chat.document_data и запускает этап проверки (next_turn). 
    Возвращает первое сообщение ассистента с вопросом №1.
    """
    user_login = decode_access_token(token)
    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    chat = session.get(ChatModel, chat_id)
    if not chat or chat.user_id != user.id:
        raise HTTPException(404, "Чат не найден")

    if chat.stage not in (ChatStage.NEW, ChatStage.RETURNED_FOR_REVISION):
        raise HTTPException(400, "Файл уже загружен")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Загруженный файл пуст или испорчен")
    
    # Определяем, в какой этап будем переводить
    next_stage = ChatStage.CHECKING_THE_WORK if chat.meta is None else ChatStage.CHECKING_CORRECTED_WORK
    
    # Начинаем ручную транзакцию
    try:
        # Помечаем чат, но не делаем session.commit()
        chat.document_data = data
        chat.document_name = file.filename
        chat.stage = next_stage
        session.add(chat)
        session.flush()   # отправляем в БД, но не коммитим

        set_user_work_status(chat, session, WorkStatus.IN_PROGRESS)

        # вызываем LLM-проверку
        if next_stage == ChatStage.CHECKING_THE_WORK:
            # запускаем проверку работы
            assistant_reply = await handle_checking_the_work_stage(chat, session)
        else:
            # запускаем проверку исправленной работы
            assistant_reply = await handle_checking_the_corrected_work_stage(chat, session)

    except Exception as e:
        # Если что-то упало (включая любые ошибки LLM) — откатываем все изменения
        session.rollback()
        # Добавляем в чат сообщение об ошибке
        assistant_reply = (
            "⚠️ Произошла ошибка при обращении к модели. "
            "Пожалуйста, попробуйте загрузить файл ещё раз чуть позже."
        )
        ai_message = MessageModel(chat_id=chat_id, sender="ai", text=assistant_reply)
        session.add(ai_message)
        session.commit()
        session.refresh(ai_message)

        return {
            "ai_message": {
                "id": ai_message.id,
                "sender": ai_message.sender,
                "context": ai_message.text,
                "created_at": ai_message.created_at.isoformat()
            },
            "chat": {
                "stage": chat.stage,
                "document_name": chat.document_name
            }
        }

    # Если LLM всё отработал без исключений — коммитим изменения
    session.commit()
    session.refresh(chat)

    # Сохраняем ответ ассистента
    ai_message = MessageModel(chat_id=chat_id, sender="ai", text=assistant_reply)
    session.add(ai_message); 
    session.commit(); 
    session.refresh(ai_message)

    return {"ai_message": {
            "id": ai_message.id,
            "sender": "ai",
            "context": ai_message.text,
            "created_at": ai_message.created_at.isoformat()
        },
        "chat": {
            "stage": chat.stage,
            "document_name": chat.document_name
        }
    }