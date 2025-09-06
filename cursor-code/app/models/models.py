from datetime import datetime
from enum import Enum
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.config import settings


class SessionStatus(str, Enum):
	PENDING = "pending"
	CLOSED = "closed"
	REJECTED = "rejected"


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
	coins: Mapped[int] = mapped_column(Integer, default=settings.INITIAL_COINS, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
	purchases: Mapped[list["Purchase"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Shark(Base):
	__tablename__ = "sharks"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	name: Mapped[str] = mapped_column(String(100), nullable=False)
	price_coins: Mapped[int] = mapped_column(Integer, nullable=False)
	personality: Mapped[str] = mapped_column(String(255), nullable=False)
	expertise: Mapped[str] = mapped_column(String(255), nullable=False)
	image_url: Mapped[str] = mapped_column(String(255), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	sessions: Mapped[list["ChatSession"]] = relationship(back_populates="shark")


class ChatSession(Base):
	__tablename__ = "chat_sessions"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	shark_id: Mapped[int] = mapped_column(ForeignKey("sharks.id"), nullable=False)
	status: Mapped[SessionStatus] = mapped_column(SAEnum(SessionStatus), default=SessionStatus.PENDING, nullable=False)
	report: Mapped[str | None] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

	user: Mapped[User] = relationship(back_populates="sessions")
	shark: Mapped[Shark] = relationship(back_populates="sessions")
	messages: Mapped[list["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Message(Base):
	__tablename__ = "messages"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
	sender: Mapped[str] = mapped_column(String(20))  # 'user' or 'shark'
	content: Mapped[str] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	session: Mapped[ChatSession] = relationship(back_populates="messages")


class Purchase(Base):
	__tablename__ = "purchases"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
	coins: Mapped[int] = mapped_column(Integer, nullable=False)
	usd_amount: Mapped[int] = mapped_column(Integer, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	user: Mapped[User] = relationship(back_populates="purchases")
