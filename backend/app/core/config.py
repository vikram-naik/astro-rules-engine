from pydantic import BaseSettings


class Settings(BaseSettings):
database_url: str = "sqlite:///./astro_rules.db"


class Config:
env_file = ".env"


settings = Settings()