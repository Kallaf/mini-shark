from fastapi import FastAPI

from app.routers.users import router as users_router
from app.routers.sharks import router as sharks_router
from app.routers.sessions import router as sessions_router
from app.routers.history import router as history_router
from app.core.db import init_db

app = FastAPI(title="Mini Shark Backend", version="0.1.0")


@app.on_event("startup")
async def on_startup() -> None:
	init_db()


app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(sharks_router, prefix="/api/v1/sharks", tags=["sharks"])
app.include_router(sessions_router, prefix="/api/v1", tags=["sessions"])
app.include_router(history_router, prefix="/api/v1/history", tags=["history"])
