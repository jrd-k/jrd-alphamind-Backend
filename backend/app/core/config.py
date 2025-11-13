from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "jrd-alphamind-backend"
    debug: bool = True
    database_url: str = "sqlite:///./dev.db"
    redis_url: str = "redis://localhost:6379/0"
    # JWT settings
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
