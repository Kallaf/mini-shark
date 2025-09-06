from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import ChatSession, Message, User
from app.schemas.schemas import MessageCreate, MessageRead, SessionRead
from app.services.ai import generate_ai_reply
from app.routers.users import get_or_create_user

router = APIRouter()


@router.get("/sessions/{session_id}", response_model=SessionRead)
def get_session(session_id: int, x_user_email: str = Header(..., alias="X-User-Email"), db: Session = Depends(get_db)):
	user = get_or_create_user(x_user_email, db)
	session = db.get(ChatSession, session_id)
	if not session or session.user_id != user.id:
		raise HTTPException(status_code=404, detail="Session not found")
	# Load relationships
	session.messages  # access to ensure loading
	session.shark
	return session


@router.post("/sessions/{session_id}/messages", response_model=MessageRead)
def send_message(session_id: int, payload: MessageCreate, x_user_email: str = Header(..., alias="X-User-Email"), db: Session = Depends(get_db)):
	user = get_or_create_user(x_user_email, db)
	session = db.get(ChatSession, session_id)
	if not session or session.user_id != user.id:
		raise HTTPException(status_code=404, detail="Session not found")
	user_msg = Message(session_id=session.id, sender="user", content=payload.content)
	db.add(user_msg)
	db.commit()
	db.refresh(user_msg)
	# AI reply
	reply_text = generate_ai_reply(session, payload.content)
	ai_msg = Message(session_id=session.id, sender="shark", content=reply_text)
	db.add(ai_msg)
	db.commit()
	db.refresh(ai_msg)
	return ai_msg
