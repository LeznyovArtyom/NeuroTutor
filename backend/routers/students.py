from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from pydantic import BaseModel
from sqlmodel import Session, select
from database import get_session
from models import User as UserModel, TeacherStudent as TeacherStudentModel
from core.security import oauth2_scheme, decode_access_token


router = APIRouter()


class AddStudentsToList(BaseModel):
    ids: list[int]


# Поиск студентов по совпадению фамилии или логина
@router.get("/users/search", summary="Поиск пользователей по фамилии или логину", tags=["Студенты"])
async def search_users(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session), query: str = Query(..., min_length=2, description="Фрагмент фамилии или логина")):
    """
    Возвращает всех пользователей, у login или lastName которых есть `query`,
    исключая текущего пользователя.
    """
    user_login = decode_access_token(token)
    current_user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()
    if not current_user:
        raise HTTPException(404, "Пользователь не найден")

    stmt = (select(UserModel).where(UserModel.id != current_user.id,(UserModel.last_name.ilike(f"%{query}%")) |(UserModel.login.ilike(f"%{query}%"))).limit(20))
    users = session.exec(stmt).all()

    users_data = [
        {
            "id": user.id,
            "last_name": user.last_name,
            "first_name": user.first_name,
            "login": user.login
        } for user in users
    ]

    return JSONResponse({"Users": users_data}, status_code=200)


# Получить всех студентов преподавателя
@router.get("/users/me/students", summary="Получить всех студентов преподавателя", tags=["Студенты"])
async def get_students_from_list(token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Возвращает список студентов, с которыми текущий преподаватель работает.
    Требуется авторизация с использованием токена доступа.
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="Только преподаватель может просматривать своих студентов")
    
    students = session.exec(select(UserModel).join(TeacherStudentModel, TeacherStudentModel.student_id == UserModel.id).where(TeacherStudentModel.teacher_id == user.id)).all()

    students_data = [
        {
            "id": student.id,
            "last_name": student.last_name,
            "first_name": student.first_name,
            "login": student.login
        } for student in students
    ]

    return JSONResponse({"Students": students_data}, status_code=200)


# Добавить студентов в список преподавателя
@router.post("/users/me/students/add", summary="Добавить студентов в список преподавателя", tags=["Студенты"])
async def add_students_to_list(studentsIds: AddStudentsToList, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Добавляет связь преподаватель–студент для каждого `id` из studentsIds.ids.
    """
    user_login = decode_access_token(token)

    current_user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not current_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Только преподаватель может добавлять студентов")
    
    for studentId in studentsIds.ids:
        if studentId == current_user.id:
            continue
        exists = session.exec(select(TeacherStudentModel).where(TeacherStudentModel.teacher_id == current_user.id, TeacherStudentModel.student_id == studentId)).first()
        if not exists:
            rel = TeacherStudentModel(
                teacher_id=current_user.id, student_id=studentId
            )
            session.add(rel)

    session.commit()
    return JSONResponse({"message": "Студенты добавлены в список преподавателя"}, status_code=201)


# Удалить студента из списка преподавателя
@router.delete("/users/me/student/{student_id}/remove", summary="Удалить студента из списка преподавателя", tags=["Студенты"])
async def delete_student_from_list(student_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Удаляет студента из списка преподавателя.
    Требуется авторизация с использованием токена доступа.

    Параметр пути: **student_id**
    """
    user_login = decode_access_token(token)

    current_user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not current_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Только преподаватель может удалять студентов")

    # Проверяем, существует ли связь преподаватель-студент
    teacher_student_relation = session.exec(select(TeacherStudentModel).where(TeacherStudentModel.teacher_id == current_user.id,TeacherStudentModel.student_id == student_id)).first()

    if not teacher_student_relation:
        raise HTTPException(status_code=404, detail="Студент не найден в списке преподавателя")

    # Удаляем связь преподаватель-студент
    session.delete(teacher_student_relation)
    session.commit()

    return JSONResponse({"message": "Студент успенщно удален из списка преподавателя"}, status_code=200)