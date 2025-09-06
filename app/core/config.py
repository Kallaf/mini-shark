from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

	DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/mini_shark"))
	INITIAL_COINS: int = 200
	AI_REPLY_STUB: bool = True
	COINS_PER_USD: int = 100


settings = Settings()
