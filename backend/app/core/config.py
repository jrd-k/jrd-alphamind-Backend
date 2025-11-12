from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "jrd-alphamind-backend"
    debug: bool = True
    database_url: str = "sqlite:///./dev.db"


settings = Settings()
