from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import get_db
from app.models.models import User, Shark, ChatSession, Message
from app.schemas.schemas import SharkRead, SessionRead
from app.routers.users import get_or_create_user

router = APIRouter()


@router.get("/", response_model=list[SharkRead])
def list_sharks(db: Session = Depends(get_db)):
	return list(db.scalars(select(Shark)).all())


@router.post("/{shark_id}/start", response_model=SessionRead)
def start_session(shark_id: int, x_user_email: str = Header(..., alias="X-User-Email"), db: Session = Depends(get_db)):
	user = get_or_create_user(x_user_email, db)
	shark = db.get(Shark, shark_id)
	if not shark:
		raise HTTPException(status_code=404, detail="Shark not found")
	if user.coins < shark.price_coins:
		raise HTTPException(status_code=402, detail="Not enough coins")
	user.coins -= shark.price_coins
	session = ChatSession(user_id=user.id, shark_id=shark.id)
	db.add(session)
	db.commit()
	db.refresh(session)
	# preload relationships
	db.refresh(session)
	session.messages = []
	session.shark = shark
	return session
