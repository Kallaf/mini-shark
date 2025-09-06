from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from contextlib import contextmanager

from app.core.config import settings


class Base(DeclarativeBase):
	pass


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def db_session():
	session = SessionLocal()
	try:
		yield session
	finally:
		session.close()


def get_db():
	with db_session() as session:
		yield session


def init_db() -> None:
	# Import models so metadata is populated
	from app.models.models import User, Shark, ChatSession, Message, Purchase  # noqa: F401
	Base.metadata.create_all(bind=engine)

	# Seed sharks on first run
	from app.models.models import Shark

	with db_session() as session:
		count = session.query(Shark).count()
		if count == 0:
			seed_sharks = [
				{"name": "Mr. Byte", "price_coins": 30, "personality": "Analytical and frugal", "expertise": "Fintech", "image_url": "/static/sharks/byte.gif"},
				{"name": "Ms. Cloud", "price_coins": 40, "personality": "Visionary and bold", "expertise": "Cloud & SaaS", "image_url": "/static/sharks/cloud.gif"},
				{"name": "Captain Crypto", "price_coins": 50, "personality": "Risk-taker", "expertise": "Web3", "image_url": "/static/sharks/crypto.gif"},
				{"name": "Doc Data", "price_coins": 35, "personality": "Data-driven", "expertise": "AI & ML", "image_url": "/static/sharks/data.gif"},
				{"name": "Lady Growth", "price_coins": 45, "personality": "Marketing guru", "expertise": "Growth & GTM", "image_url": "/static/sharks/growth.gif"},
			]
			for s in seed_sharks:
				shark = Shark(**s)
				session.add(shark)
			session.commit()
