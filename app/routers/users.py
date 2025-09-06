from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import get_db
from app.models.models import User, Purchase
from app.schemas.schemas import UserRead, PurchaseCreate, PurchaseRead
from app.services.payments import simulate_purchase

router = APIRouter()


def get_or_create_user(email: str, db: Session) -> User:
	user = db.scalar(select(User).where(User.email == email))
	if not user:
		user = User(email=email)
		db.add(user)
		db.commit()
		db.refresh(user)
	return user


@router.get("/me", response_model=UserRead)
def get_me(x_user_email: str = Header(..., alias="X-User-Email"), db: Session = Depends(get_db)):
	user = get_or_create_user(x_user_email, db)
	return user


@router.post("/me/purchases", response_model=PurchaseRead)
def create_purchase(payload: PurchaseCreate, x_user_email: str = Header(..., alias="X-User-Email"), db: Session = Depends(get_db)):
	user = get_or_create_user(x_user_email, db)
	coins, usd_amount = simulate_purchase(payload.coins)
	user.coins += coins
	purchase = Purchase(user_id=user.id, coins=coins, usd_amount=usd_amount)
	db.add(purchase)
	db.commit()
	db.refresh(purchase)
	return purchase
