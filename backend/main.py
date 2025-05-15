from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Annotated
from passlib.context import CryptContext
import jwt
from database import get_session
from models import User as UserModel, Chat as ChatModel, Message as MessageModel, Discipline as DisciplineModel, Document as DocumentModel, Work as WorkModel, TeacherStudent as TeacherStudentModel, UserWork as UserWorkModel
from sqlmodel import Session, select, update
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import base64


app = FastAPI(title="API NeuroTutor", description="API для цифрового помощника", version="1.0.0", docs_url="/docs", openapi_url="/openapi.json", redoc_url=None)


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


class Document(BaseModel):
    name: str
    data: bytes


class Discipline(BaseModel):
    name: str
    documents: Optional[List[Document]] = None


class DisciplineUpdate(BaseModel):
    name: Optional[str] = None
    documents: Optional[List[Document]] = None


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


class AddStudentsToList(BaseModel):
    ids: list[int]


class AddStudentsToWork(BaseModel):
    ids: list[int]






class ChatUpdate(BaseModel):
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


# Обновить информацию о пользователе
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


# Получить все дисциплины текущего преподавателя
@app.get("/users/me/disciplines", summary="Получить все дисциплины текущего преподавателя", tags=["Дисциплины"])
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
@app.post("/users/me/disciplines/add", summary="Добавить новую дисциплину текущему преподавателю", tags=["Дисциплины"])
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
@app.get("/users/me/disciplines/{discipline_id}", summary="Получить информацию о дисциплине текущего преподавателя", tags=["Дисциплины"])
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
@app.put("/users/me/disciplines/{discipline_id}/update", summary="Обновить информацию о дисциплине текущего преподавателя", tags=["Дисциплины"])
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
@app.delete("/users/me/disciplines/{discipline_id}/delete", summary="Удалить дисциплину текущего преподавателя", tags=["Дисциплины"])
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
@app.delete("/disciplines/{discipline_id}/documents/{document_id}/delete", summary="Удалить документ из дисциплины", tags=["Дисциплины"])
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


# Добавить новую работу к дисциплине
@app.post("/disciplines/{discipline_id}/work/add", summary="Добавить новую работу в дисциплину", tags=["Работы"])
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
@app.delete("/disciplines/{discipline_id}/work/{work_id}/delete", summary="Удалить работу из дисциплины", tags=["Работы"])
async def delete_work(discipline_id: int, work_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
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
@app.get("/disciplines/{discipline_id}/work/{work_id}", summary="Получить информацию о работе", tags=["Работы"])
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

    return JSONResponse({"Work": {
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
    }}, status_code=200)


# Обновить информацию о работе
@app.put("/disciplines/{discipline_id}/work/{work_id}/update", summary="Обновить информацию о работе", tags=["Работы"])
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
@app.post("/disciplines/{discipline_id}/work/{work_id}/students/add", summary="Добавить студентов в работу", tags=["Работы"])
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

    # Добавляем студентов в работу
    for student_id in studentsIds.ids:
        # Проверяем, что студент существует
        student = session.exec(select(UserModel).where(UserModel.id == student_id)).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Студент с ID {student_id} не найден")

        # Проверяем, что связь студент-работа еще не существует
        existing_relation = session.exec(select(UserWorkModel).where(UserWorkModel.student_id == student_id, UserWorkModel.work_id == work_id)).first()
        if not existing_relation:
            new_user_work = UserWorkModel(student_id=student_id, work_id=work_id)
            session.add(new_user_work)

    session.commit()

    return JSONResponse({"message": "Студенты успешно добавлены в работу"}, status_code=201)


# Удалить студента из работы
@app.delete("/disciplines/{discipline_id}/work/{work_id}/students/{student_id}/remove", summary="Удалить студента из работы", tags=["Работы"])
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


# Получить список студентов по совпадению
@app.get("/users/search", summary="Поиск пользователей по фамилии или логину", tags=["Пользователи"])
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
@app.get("/users/me/students", summary="Получить всех студентов преподавателя", tags=["Студенты"])
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
@app.post("/users/me/students/add", summary="Добавить студентов в список преподавателя", tags=["Студенты"])
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
@app.delete("/users/me/student/{student_id}/remove", summary="Удалить студента из списка преподавателя", tags=["Студенты"])
async def delete_work(student_id: int, token: Annotated[str, Depends(oauth2_scheme)], session: Session = Depends(get_session)):
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


# Получить чат в режиме Помощь

# Получить чат в режиме Сдача работы













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

    chat_session = session.exec(select(ChatModel).where(ChatModel.id == session_id, ChatModel.user_id == user.id)).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    session.delete(chat_session)
    session.commit()

    return JSONResponse({"message": "Сессия чата успешно удалена"}, status_code=200)


# Обновить информацию о сессии чата
@app.put("/users/me/chat_sessions/{session_id}/update", summary="Обновить информацию о сессии чата", tags=["Сессии чата"])
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

    chat_sess = session.exec(select(ChatModel).where(ChatModel.id == request.chat_id, ChatModel.user_id == user.id)).first()
    if not chat_sess:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    # ─── 3. генерируем ответ целиком ───
    answer_text: str = await run_in_threadpool(generate_once, request.text)

    return JSONResponse({"answer": answer_text})