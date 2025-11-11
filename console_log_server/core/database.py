from __future__ import annotations

from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from console_log_server.core.settings import get_settings
from console_log_server.models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """SQLAlchemy 엔진을 싱글톤으로 반환."""

    global _engine

    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            future=True,
            pool_pre_ping=True,
        )

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """세션 팩토리를 반환."""

    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            future=True,
        )

    return _session_factory


def get_session() -> Generator[Session, None, None]:
    """FastAPI 의존성 주입용 DB 세션."""

    session = get_session_factory()()

    try:
        yield session
    finally:
        session.close()


def create_all_tables() -> None:
    """모든 데이터베이스 테이블을 생성."""

    Base.metadata.create_all(get_engine())


def reset_engine() -> None:
    """테스트용으로 엔진 캐시를 초기화."""

    global _engine, _session_factory

    if _session_factory is not None:
        _session_factory.close_all()

    _engine = None
    _session_factory = None
