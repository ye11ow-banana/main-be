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
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"


class EmailSettings(BaseModel):
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@example.com"
    smtp_port: int = 1025
    smtp_server: str = "mailpit"
    smtp_starttls: bool = False
    smtp_ssl_tls: bool = False


class TZSettings(BaseModel):
    local: str = "Europe/Kyiv"


class OpenAISettings(BaseModel):
    api_key: str = ""
    model_vision: str = ""
    model_text: str = ""


class Settings(BaseSettings):
    secret_key: str = "secret"

    db: PostgresDBSettings = PostgresDBSettings()
    jwt: JWTSettings = JWTSettings()
    email: EmailSettings = EmailSettings()
    tz: TZSettings = TZSettings()
    openai: OpenAISettings = OpenAISettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


settings = Settings()
