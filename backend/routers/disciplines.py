from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Annotated, Optional, List
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from models import User as UserModel, Discipline as DisciplineModel, Document as DocumentModel
import base64
from core.security import oauth2_scheme, decode_access_token


router = APIRouter()


class Document(BaseModel):
    name: str
    data: bytes


class Discipline(BaseModel):
    name: str
    documents: Optional[List[Document]] = None


class DisciplineUpdate(BaseModel):
    name: Optional[str] = None
    documents: Optional[List[Document]] = None
    

# Получить все дисциплины текущего преподавателя
@router.get("/users/me/disciplines", summary="Получить все дисциплины текущего преподавателя", tags=["Дисциплины"])
async def get_user_disciplines(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Возвращает список всех дисциплин текущего преподавателя.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    disciplines = session.exec(select(DisciplineModel).where(DisciplineModel.teacher_id == user.id)).all()

    disciplines_data = [
        {
            "id": discipline.id,
            "name": discipline.name,
        } for discipline in disciplines
    ]

    return JSONResponse({"Disciplines": disciplines_data}, status_code=200)


# Добавить новую дисциплину текущему преподавателю
@router.post("/users/me/disciplines/add", summary="Добавить новую дисциплину текущему преподавателю", tags=["Дисциплины"])
async def add_new_discipline(discipline_data: Discipline, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Добавляет новую дисциплину текущему преподавателю.
    Требуется авторизация с использованием токена доступа.

    Поля для добавления дисциплины:
    - **name**: Название дисциплины
    - **documents**: Список документов (опционально)
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    new_discipline = DisciplineModel(
        name=discipline_data.name,
        teacher_id=user.id
    )

    session.add(new_discipline)
    session.commit()
    session.refresh(new_discipline)

    if discipline_data.documents:
        for document in discipline_data.documents:
            new_document = DocumentModel(
                name=document.name,
                data=document.data,
                discipline_id=new_discipline.id
            )
            session.add(new_document)
        session.commit()
        session.refresh(new_document)

    return JSONResponse({"id": new_discipline.id, "message": "Дисциплина успешно добавлена"}, status_code=201)


# Получить информацию о дисциплине текущего преподавателя
@router.get("/users/me/disciplines/{discipline_id}", summary="Получить информацию о дисциплине текущего преподавателя", tags=["Дисциплины"])
async def get_discipline_info(discipline_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Возвращает информацию о дисциплине текущего преподавателя.
    Требуется авторизация с использованием токена доступа.

    Параметр пути: **discipline_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    discipline = session.exec(select(DisciplineModel).where(DisciplineModel.id == discipline_id, DisciplineModel.teacher_id == user.id)).first()

    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    return JSONResponse({"Discipline": {
        "id": discipline.id,
        "name": discipline.name,
        "documents": [
            {
                "id": document.id,
                "name": document.name,
                "data": base64.b64encode(document.data).decode()
            } for document in discipline.documents
        ],
        "works": [
            {
                "id": work.id,
                "name": work.name,
                "number": work.number,
            } for work in discipline.works
        ]
    }}, status_code=200)


# Обновить информацию о дисциплине текущего преподавателя
@router.put("/users/me/disciplines/{discipline_id}/update", summary="Обновить информацию о дисциплине текущего преподавателя", tags=["Дисциплины"])
async def update_discipline(discipline_id: int, discipline_data: DisciplineUpdate, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Обновляет информацию о дисциплине текущего преподавателя.
    Требуется авторизация с использованием токена доступа.

    Поля для обновления дисциплины:
    - **name**: Название дисциплины (опционально)
    - **documents**: Список документов (опционально)
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    discipline = session.exec(select(DisciplineModel).where(DisciplineModel.id == discipline_id, DisciplineModel.teacher_id == user.id)).first()

    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    if discipline_data.name:
        discipline.name = discipline_data.name

    if discipline_data.documents:
        for document in discipline_data.documents:
            new_document = DocumentModel(
                name=document.name,
                data=document.data,
                discipline_id=discipline.id
            )
            session.add(new_document)

    session.add(discipline)
    session.commit()

    return JSONResponse({"message": "Дисциплина успешно обновлена"}, status_code=200)


# Удалить дисциплину текущего преподавателя
@router.delete("/users/me/disciplines/{discipline_id}/delete", summary="Удалить дисциплину текущего преподавателя", tags=["Дисциплины"])
async def delete_discipline(discipline_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Удаляет дисциплину текущего преподавателя.
    Требуется авторизация с использованием токена доступа.

    Параметр пути: **discipline_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    discipline = session.exec(select(DisciplineModel).where(DisciplineModel.id == discipline_id, DisciplineModel.teacher_id == user.id)).first()

    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    session.delete(discipline)
    session.commit()

    return JSONResponse({"message": "Дисциплина успешно удалена"}, status_code=200)


# Удалить документ
@router.delete("/disciplines/{discipline_id}/documents/{document_id}/delete", summary="Удалить документ из дисциплины", tags=["Дисциплины"])
async def delete_document_from_discipline(discipline_id: int, document_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Удаляет документ из дисциплины.
    Требуется авторизация с использованием токена доступа.

    Параметры пути: **discipline_id**, **document_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    document = session.exec(select(DocumentModel).where(DisciplineModel.id == discipline_id, DocumentModel.id == document_id)).first()

    if not document:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")
    
    session.delete(document)
    session.commit()

    return JSONResponse({"message": "Документ успещно удален из дисциплины"}, status_code=200)
