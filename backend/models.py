from sqlmodel import SQLModel, Field, Relationship, Column, ForeignKey, Text
from typing import Optional, List
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGBLOB
from enum import Enum
from sqlalchemy import Enum as SQLEnum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN   = "admin"


class SenderType(str, Enum):
    AI   = "ai"
    USER = "user"


# Этапы сдачи работы
class ChatStage(str, Enum):
    NEW                     = "new"                       # чат только создан, работа не загружена
    CHECKING_THE_WORK       = "checking_the_work"         # проверка загруженной работы
    RETURNED_FOR_REVISION   = "returned_for_revision"     # возвращено на доработку
    CHECKING_CORRECTED_WORK = "checking_corrected_work" # проверка исправленной работы
    DIALOGUE                = "dialogue"                  # диалог в формате вопрос-ответ
    REVIEW                  = "review"                    # статистика по ответам
    FINISHED                = "finished"                  # работа зачтена / не зачтена


# Статусы попытки сдачи работы студентом
class WorkStatus(str, Enum):
    NOT_STARTED = "Не начата"
    NEED_FIX    = "На доработке"
    IN_PROGRESS = "В процессе"
    PASSED      = "Принята"
    FAILED      = "Отклонена"


class TeacherStudent(SQLModel, table=True):
    __tablename__ = "teacher_student"
    teacher_id: Optional[int] = Field(sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True))
    student_id: Optional[int] = Field(sa_column=Column(ForeignKey("user.id", ondelete="RESTRICT"), primary_key=True))


class StudentDiscipline(SQLModel, table=True):
    __tablename__ = "student_discipline"
    student_id: Optional[int] = Field(sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True))
    discipline_id: Optional[int] = Field(sa_column=Column(ForeignKey("discipline.id", ondelete="CASCADE"), primary_key=True))


class UserWork(SQLModel, table=True):
    __tablename__ = "user_work"
    student_id: Optional[int] = Field(sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True))
    work_id: Optional[int] = Field(sa_column=Column(ForeignKey("work.id", ondelete="CASCADE"), primary_key=True))
    status: WorkStatus = Field(default=WorkStatus.NOT_STARTED, sa_column=Column(SQLEnum(WorkStatus, name="work_status")))


class User(SQLModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(primary_key=True)
    login: str = Field(max_length=30, unique=True, index=True)
    password: str = Field(max_length=100)
    last_name: str = Field(max_length=50)
    first_name: str = Field(max_length=50)
    role: UserRole = Field()
    # role: UserRole = Field(default=UserRole.STUDENT)

    disciplines: List["Discipline"] = Relationship(back_populates="teacher", sa_relationship_kwargs={"cascade": "all, delete"})
    # дисциплины, в которых участвует студент
    enrolled_disciplines: List["Discipline"] = Relationship(
        back_populates="students",
        link_model=StudentDiscipline,
        sa_relationship_kwargs={"passive_deletes": True}
    )
    works: List["Work"] = Relationship(
        back_populates="students",
        link_model=UserWork,
        sa_relationship_kwargs={"passive_deletes": True}
    )
    students: List["User"] = Relationship(
        back_populates="teachers",
        link_model=TeacherStudent,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==TeacherStudent.teacher_id",
            "secondaryjoin": "User.id==TeacherStudent.student_id",
            "passive_deletes": True,
        },
    )
    teachers: List["User"] = Relationship(
        back_populates="students",
        link_model=TeacherStudent,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==TeacherStudent.student_id",
            "secondaryjoin": "User.id==TeacherStudent.teacher_id",
        },
    )
    chats: List["Chat"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})
    

class Chat(SQLModel, table=True):
    __tablename__ = "chat"
    id: Optional[int] = Field(primary_key=True)
    mode: str = Field(max_length=45)
    document_data: Optional[bytes] = Field(sa_column=Column(LONGBLOB()))
    document_name: Optional[str] = Field(default=None, max_length=255)  # имя файла для определения расширения
    user_id: int = Field(sa_column=Column(ForeignKey("user.id", ondelete="CASCADE")))
    work_id: Optional[int] = Field(sa_column=Column(ForeignKey("work.id", ondelete="CASCADE")))
    stage: ChatStage = Field(default=ChatStage.NEW, sa_column=Column(SQLEnum(ChatStage, name="chat_stage")))
    meta: Optional[str] = Field(sa_column=Column(Text())) # JSON: qs, stats
    current_q: int = Field(default=0)
    score: float = Field(default=0.0)

    user: Optional[User] = Relationship(back_populates="chats")
    messages: List["Message"] = Relationship(back_populates="chat", sa_relationship_kwargs={"passive_deletes": True})
    work: Optional["Work"] = Relationship(back_populates="chats")
 

class Message(SQLModel, table=True):
    __tablename__ = "message"
    id: Optional[int] = Field(primary_key=True)
    sender: SenderType = Field(
        sa_column=Column(
            SQLEnum(SenderType, name="sender_enum"),
            nullable=False
        )
    )
    text: Optional[str] = Field(sa_column=Column(Text()))
    chat_id: int = Field(sa_column=Column(ForeignKey("chat.id", ondelete="CASCADE")))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    chat: Optional[Chat] = Relationship(back_populates="messages")


class Discipline(SQLModel, table=True):
    __tablename__ = "discipline"
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(max_length=255)
    teacher_id: int = Field(sa_column=Column(ForeignKey("user.id", ondelete="CASCADE")))

    teacher: Optional["User"] = Relationship(back_populates="disciplines")
    # студенты, записанные на дисциплину
    students: List[User] = Relationship(
        back_populates="enrolled_disciplines",
        link_model=StudentDiscipline,
        sa_relationship_kwargs={"passive_deletes": True}
    )
    documents: List["Document"] = Relationship(back_populates="discipline", sa_relationship_kwargs={"passive_deletes": True})
    works: List["Work"] = Relationship(back_populates="discipline", sa_relationship_kwargs={"passive_deletes": True})


class Document(SQLModel, table=True):
    __tablename__ = "document"
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(max_length=255)
    data: Optional[bytes] = Field(sa_column=Column(LONGBLOB()))
    discipline_id: int =  Field(sa_column=Column(ForeignKey("discipline.id", ondelete="CASCADE")))

    discipline: Optional[Discipline] = Relationship(back_populates="documents")
    works: List["Work"] = Relationship(back_populates="document")


class Work(SQLModel, table=True):
    __tablename__ = "work"
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(max_length=255)
    task: Optional[str] = Field(sa_column=Column(Text()))
    number: int = Field(nullable=False)
    document_id: Optional[int] = Field(sa_column=Column(ForeignKey("document.id", ondelete="SET NULL")))
    document_section: Optional[str] = Field(max_length=255)
    discipline_id: Optional[int] = Field(sa_column=Column(ForeignKey("discipline.id", ondelete="CASCADE")))

    discipline: Optional[Discipline] = Relationship(back_populates="works", sa_relationship_kwargs={"passive_deletes": True})
    document: Optional[Document] = Relationship(back_populates="works")
    students: List["User"] = Relationship(
        back_populates="works",
        link_model=UserWork,
        sa_relationship_kwargs={"passive_deletes": True,}
    )
    chats: List["Chat"] = Relationship(back_populates="work")
