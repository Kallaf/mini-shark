from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.db import get_db
from app.models.models import ChatSession, SessionStatus
from app.schemas.schemas import CountersRead, SessionRead
from app.routers.users import get_or_create_user

router = APIRouter()


@router.get("/counters", response_model=CountersRead)
def get_counters(x_user_email: str = Header(..., alias="X-User-Email"), db: Session = Depends(get_db)):
	user = get_or_create_user(x_user_email, db)
	q = select(ChatSession.status, func.count()).where(ChatSession.user_id == user.id).group_by(ChatSession.status)
	rows = db.execute(q).all()
	counts = {status: 0 for status in [SessionStatus.PENDING, SessionStatus.CLOSED, SessionStatus.REJECTED]}
	for status, count in rows:
		counts[status] = count
	return {"pending": counts[SessionStatus.PENDING], "closed": counts[SessionStatus.CLOSED], "rejected": counts[SessionStatus.REJECTED]}


@router.get("/sessions", response_model=list[SessionRead])
def list_sessions(status: SessionStatus | None = None, skip: int = 0, limit: int = 20, x_user_email: str = Header(..., alias="X-User-Email"), db: Session = Depends(get_db)):
	user = get_or_create_user(x_user_email, db)
	q = select(ChatSession).where(ChatSession.user_id == user.id)
	if status:
		q = q.where(ChatSession.status == status)
	sessions = db.scalars(q.offset(skip).limit(limit)).all()
	# touch relationships
	for s in sessions:
		s.messages
		s.shark
	return sessions
