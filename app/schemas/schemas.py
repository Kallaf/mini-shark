from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models.models import SessionStatus


class UserRead(BaseModel):
	id: int
	email: EmailStr
	coins: int
	created_at: datetime

	class Config:
		from_attributes = True


class PurchaseCreate(BaseModel):
	coins: int


class PurchaseRead(BaseModel):
	id: int
	coins: int
	usd_amount: int
	created_at: datetime

	class Config:
		from_attributes = True


class SharkRead(BaseModel):
	id: int
	name: str
	price_coins: int
	personality: str
	expertise: str
	image_url: str

	class Config:
		from_attributes = True


class MessageCreate(BaseModel):
	content: str


class MessageRead(BaseModel):
	id: int
	sender: str
	content: str
	created_at: datetime

	class Config:
		from_attributes = True


class SessionRead(BaseModel):
	id: int
	status: SessionStatus
	report: Optional[str]
	created_at: datetime
	updated_at: datetime
	shark: SharkRead
	messages: List[MessageRead]

	class Config:
		from_attributes = True


class CountersRead(BaseModel):
	pending: int
	closed: int
	rejected: int
