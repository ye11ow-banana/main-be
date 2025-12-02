from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresDBSettings(BaseModel):
    host: str = "localhost"
    port: str = "5432"
    user: str = "postgres"
    password: str = "postgres"
    db_name: str = "postgres"


class JWTSettings(BaseModel):
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"


class Settings(BaseSettings):
    secret_key: str = "secret"

    db: PostgresDBSettings = PostgresDBSettings()
    jwt: JWTSettings = JWTSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


settings = Settings()
