from sqlmodel import SQLModel, Field, Relationship, Column, ForeignKey, Text
from sqlalchemy import CheckConstraint, String
from typing import Optional, List
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGBLOB
from enum import Enum
from sqlalchemy import Enum as SQLEnum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class SenderType(str, Enum):
    AI = "ai"
    USER = "user"


class TeacherStudent(SQLModel, table=True):
    __tablename__ = "teacher_student"
    teacher_id: Optional[int] = Field(sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True))
    student_id: Optional[int] = Field(sa_column=Column(ForeignKey("user.id", ondelete="RESTRICT"), primary_key=True))


class UserWork(SQLModel, table=True):
    __tablename__ = "user_work"
    student_id: Optional[int] = Field(sa_column=Column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True))
    work_id: Optional[int] = Field(sa_column=Column(ForeignKey("work.id", ondelete="CASCADE"), primary_key=True))
    status: str = Field(max_length=20, default="Не начата")


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
    user_id: int = Field(sa_column=Column(ForeignKey("user.id", ondelete="CASCADE")))
    work_id: Optional[int] = Field(sa_column=Column(ForeignKey("work.id", ondelete="CASCADE")))

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
