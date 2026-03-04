from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ICT Community API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./ict_community.db"

    # JWT / Auth (configure later)
    SECRET_KEY: str = "change-this-to-a-secure-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
