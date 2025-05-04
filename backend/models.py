from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import CheckConstraint, String
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "user"
    id: Optional[int] = Field(default=None, primary_key=True)
    login: str = Field(max_length=30, unique=True, index=True)
    password: str = Field(max_length=100)

    chat_sessions: List["ChatSession"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_session"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    mode: str = Field(max_length=50)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="chat_sessions")
    messages: List["Message"] = Relationship(back_populates="chat_session", sa_relationship_kwargs={"cascade": "all, delete"})


class Message(SQLModel, table=True):
    __tablename__ = "message"
    id: Optional[int] = Field(default=None, primary_key=True)
    context: str = Field()
    sender: str = Field(
        sa_column=Column(
            String(50),  # Указываем тип данных явно
            CheckConstraint("sender IN ('ai', 'user')"),
            nullable=False
        )
    )
    chat_session_id: Optional[int] = Field(default=None, foreign_key="chat_session.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    chat_session: Optional[ChatSession] = Relationship(back_populates="messages")
