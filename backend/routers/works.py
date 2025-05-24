from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Annotated
from pydantic import BaseModel
from sqlmodel import Session, select, update
from database import get_session
from models import User as UserModel, Discipline as DisciplineModel, Work as WorkModel, UserWork as UserWorkModel, StudentDiscipline as StudentDisciplineModel
from core.security import oauth2_scheme, decode_access_token


router = APIRouter()


class Work(BaseModel):
    name: str
    task: str
    number: int
    document_id: int
    document_section: str


class WorkUpdate(BaseModel):
    name: str | None = None
    task: str | None = None
    number: int | None = None
    document_id: int | None = None
    document_section: str | None = None


class AddStudentsToWork(BaseModel):
    ids: list[int]


# Добавить новую работу к дисциплине
@router.post("/disciplines/{discipline_id}/work/add", summary="Добавить новую работу в дисциплину", tags=["Работы"])
async def add_new_work_to_discipline(discipline_id: int, work_data: Work, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Добавляет новую работу в дисциплину.
    Требуется авторизация с использованием токена доступа.

    Поля для добавления работы:
    - **name**: Название работы
    - **task**: Задание
    - **number**: Номер работы (для сортировки в списке)
    - **document_id**: ID документа
    - **document_section**: Раздел документа

    Параметр пути: **discipline_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # проверяем, что дисциплина существует и принадлежит текущему преподавателю
    discipline = session.exec(select(DisciplineModel).where(DisciplineModel.id == discipline_id,DisciplineModel.teacher_id == user.id,)).first()
    
    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    # Сдвинуть все существующие работы с number >= запрошенного на +1
    stmt = (update(WorkModel).where(WorkModel.discipline_id == discipline_id, WorkModel.number >= work_data.number,)
        # использовать SQL-выражение, сдвигающее поле number на +1
        .values(number=WorkModel.number + 1)
        .execution_options(synchronize_session="fetch")
    )
    session.exec(stmt)

    new_work = WorkModel(
        name=work_data.name,
        task=work_data.task,
        number=work_data.number,
        document_id=work_data.document_id,
        document_section=work_data.document_section,
        discipline_id=discipline_id
    )

    session.add(new_work)
    session.commit()

    return JSONResponse({"message": "Работа успешно добавлена в дисциплину"}, status_code=201)


# Удалить работу из дисциплины
@router.delete("/disciplines/{discipline_id}/work/{work_id}/delete", summary="Удалить работу из дисциплины", tags=["Работы"])
async def delete_work_from_discipline(discipline_id: int, work_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Удаляет работу из дисциплины.
    Требуется авторизация с использованием токена доступа.

    Параметр пути: **discipline_id**, **work_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    work = session.exec(select(WorkModel).where(DisciplineModel.id == discipline_id, WorkModel.id == work_id)).first()

    if not work:
        raise HTTPException(status_code=404, detail="Работа не найдена")

    session.delete(work)
    session.commit()

    return JSONResponse({"message": "Работа успешно удалена из дисциплины"}, status_code=200)


# Получить информацию о работе
@router.get("/disciplines/{discipline_id}/work/{work_id}", summary="Получить информацию о работе", tags=["Работы"])
async def get_work_info(discipline_id: int, work_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Получает информацию о работе.
    Требуется авторизация с использованием токена доступа.

    Параметры пути: **discipline_id**, **work_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    work = session.exec(select(WorkModel).where(DisciplineModel.id == discipline_id, WorkModel.id == work_id)).first()

    if not work:
        raise HTTPException(status_code=404, detail="Работа не найдена")

    # Получаем студентов и их статус через таблицу user_work
    students = session.exec(
        select(UserModel, UserWorkModel.status)
        .join(UserWorkModel, UserWorkModel.student_id == UserModel.id)
        .where(UserWorkModel.work_id == work_id)
    ).all()

    work_data = {
        "id": work.id,
        "name": work.name,
        "task": work.task,
        "number": work.number,
        "document_id": work.document_id,
        "document_name": work.document.name,
        "document_section": work.document_section,
        "students": [
            {
                "id": student.id,
                "last_name": student.last_name,
                "first_name": student.first_name,
                "status": status
            } for student, status in students
        ]
    }

    # Подгружаем статус, если студент
    if user.role == 'student':
        student_status = session.exec(select(UserWorkModel.status).where(UserWorkModel.work_id == work_id, UserWorkModel.student_id == user.id)).first()
        work_data["status"] = student_status or "Не начата"

    return JSONResponse({"Work": work_data}, status_code=200)


# Обновить информацию о работе
@router.put("/disciplines/{discipline_id}/work/{work_id}/update", summary="Обновить информацию о работе", tags=["Работы"])
async def update_discipline(discipline_id: int, work_id: int, work_data: WorkUpdate, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Обновляет информацию о работе.
    Требуется авторизация с использованием токена доступа.

    Поля для обновления работы:
    - **name**: Название дисциплины (опционально)
    - **task**: Задание (опционально)
    - **number**: Порядковый номер (опционально)
    - **document_id**: ID документа (опционально)
    - **document_section**: Раздел документа (опционально)

    Параметры пути: **discipline_id**, **work_id**
    """
    user_login = decode_access_token(token)

    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Проверяем, что дисциплина принадлежит этому преподавателю
    discipline = session.exec(select(DisciplineModel).where(DisciplineModel.id == discipline_id, DisciplineModel.teacher_id == user.id,)).first()
    if not discipline:
        raise HTTPException(404, "Дисциплина не найдена")

    work = session.exec(select(WorkModel).where(DisciplineModel.id == discipline_id, WorkModel.id == work_id)).first()

    if not work:
        raise HTTPException(status_code=404, detail="Работа не найдена")

    if work_data.name is not None:
        work.name = work_data.name
    if work_data.task is not None:
        work.task = work_data.task
    if work_data.number is not None:
        old_num = work.number
        new_num = work_data.number

        if new_num < old_num:
            # Сдвигаем все работы [new_num, old_num) вверх на +1
            stmt = (
                update(WorkModel)
                .where(
                    WorkModel.discipline_id == discipline_id,
                    WorkModel.id != work_id,
                    WorkModel.number >= new_num,
                    WorkModel.number < old_num,
                )
                .values(number=WorkModel.number + 1)
                .execution_options(synchronize_session="fetch")
            )
            session.exec(stmt)

        elif new_num > old_num:
            # Сдвигаем все работы (old_num, new_num] вниз на –1
            stmt = (
                update(WorkModel)
                .where(
                    WorkModel.discipline_id == discipline_id,
                    WorkModel.id != work_id,
                    WorkModel.number <= new_num,
                    WorkModel.number > old_num,
                )
                .values(number=WorkModel.number - 1)
                .execution_options(synchronize_session="fetch")
            )
            session.exec(stmt)

        # Ставим новый номер текущей работы
        work.number = new_num
    if work_data.document_id is not None:
        work.document_id = work_data.document_id
    if work_data.document_section is not None:
        work.document_section = work_data.document_section

    session.add(work)
    session.commit()

    return JSONResponse({"message": "Работа успешно обновлена"}, status_code=200)


# Добавить студентов в работу
@router.post("/disciplines/{discipline_id}/work/{work_id}/students/add", summary="Добавить студентов в работу", tags=["Работы"])
async def add_students_to_work(discipline_id: int, work_id: int, studentsIds: AddStudentsToWork, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Добавляет студентов в работу.
    Требуется авторизация с использованием токена доступа.

    Поля для обновления работы:
    - **studentsIds**: Список ID студентов

    Параметры пути:
    - **discipline_id**: ID дисциплины
    - **work_id**: ID работы
    """
    user_login = decode_access_token(token)

    # Проверяем, что пользователь существует
    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, что дисциплина принадлежит текущему преподавателю
    discipline = session.exec(select(DisciplineModel).where(DisciplineModel.id == discipline_id, DisciplineModel.teacher_id == user.id)).first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    # Проверяем, что работа существует и принадлежит дисциплине
    work = session.exec(select(WorkModel).where(WorkModel.id == work_id, WorkModel.discipline_id == discipline_id)).first()
    if not work:
        raise HTTPException(status_code=404, detail="Работа не найдена")
    
    # Загружаем всех студентов, записанных на дисциплину
    allowed_student_ids = { student_discipline.student_id for student_discipline in session.exec(select(StudentDisciplineModel).where(StudentDisciplineModel.discipline_id == discipline_id)) }

    # Добавляем студентов в работу
    for student_id in studentsIds.ids:
        # Проверяем, что студент записан на дисциплину
        if student_id not in allowed_student_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Нельзя добавить пользователя {student_id} — он не записан на эту дисциплину"
            )
        
        # Проверяем, что студент существует
        student = session.exec(select(UserModel).where(UserModel.id == student_id)).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Студент с ID {student_id} не найден")

        # Проверяем, что связь студент-работа еще не создана
        existing_relation = session.exec(select(UserWorkModel).where(UserWorkModel.student_id == student_id, UserWorkModel.work_id == work_id)).first()
        if not existing_relation:
            new_user_work = UserWorkModel(student_id=student_id, work_id=work_id)
            session.add(new_user_work)

    session.commit()

    return JSONResponse({"message": "Студенты успешно добавлены в работу"}, status_code=201)


# Удалить студента из работы
@router.delete("/disciplines/{discipline_id}/work/{work_id}/students/{student_id}/remove", summary="Удалить студента из работы", tags=["Работы"])
async def remove_student_from_work(discipline_id: int, work_id: int, student_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
    """
    Удаляет студента из работы.
    Требуется авторизация с использованием токена доступа.

    Параметры пути:
    - **discipline_id**: ID дисциплины
    - **work_id**: ID работы
    - **student_id**: ID студента
    """
    user_login = decode_access_token(token)

    # Проверяем, что пользователь существует
    user = session.exec(select(UserModel).where(UserModel.login == user_login)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Проверяем, что дисциплина принадлежит текущему преподавателю
    discipline = session.exec(select(DisciplineModel).where(DisciplineModel.id == discipline_id, DisciplineModel.teacher_id == user.id)).first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Дисциплина не найдена")

    # Проверяем, что работа существует и принадлежит дисциплине
    work = session.exec(select(WorkModel).where(WorkModel.id == work_id, WorkModel.discipline_id == discipline_id)).first()
    if not work:
        raise HTTPException(status_code=404, detail="Работа не найдена")

    # Проверяем, что связь студент-работа существует
    user_work = session.exec(select(UserWorkModel).where(UserWorkModel.student_id == student_id, UserWorkModel.work_id == work_id)).first()
    if not user_work:
        raise HTTPException(status_code=404, detail="Студент не найден в этой работе")

    # Удаляем связь студент-работа
    session.delete(user_work)
    session.commit()

    return JSONResponse({"message": "Студент успешно удален из работы"}, status_code=200)
