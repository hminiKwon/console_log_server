from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 전역 설정."""

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = ""
    db_name: str = "db_name"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 30
    jwt_refresh_token_expires_days: int = 7
    jwt_refresh_cookie_name: str = "refresh_token"
    jwt_refresh_cookie_secure: bool = False
    jwt_refresh_cookie_samesite: str = "lax"
    jwt_session_cookie_name: str = "session_id"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def database_url(self) -> str:
        """SQLAlchemy 연결 문자열 생성."""

        from urllib.parse import quote_plus

        password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{self.db_user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """싱글톤 설정 인스턴스를 반환."""

    return Settings()
