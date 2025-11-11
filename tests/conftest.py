from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from console_log_server.api.deps import get_db_session
from console_log_server.app import create_app
from console_log_server.core import database as database_module
from console_log_server.models import Base


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(engine) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    app = create_app()

    # 테스트 환경에서는 실제 DB 연결을 막기 위해 초기화 이벤트를 제거
    app.router.on_startup = [
        handler
        for handler in app.router.on_startup
        if handler.__name__ != "_initialize_database"
    ]

    database_module._engine = None  # type: ignore[attr-defined]
    database_module._session_factory = None  # type: ignore[attr-defined]

    def _get_test_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = _get_test_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    database_module._engine = None  # type: ignore[attr-defined]
    database_module._session_factory = None  # type: ignore[attr-defined]
