from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SECRET_KEY: str
    ADMIN_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    DATABASE_URL: str
    ADMIN_USUARIO: str
    ADMIN_SENHA_HASH: str


settings = Settings()