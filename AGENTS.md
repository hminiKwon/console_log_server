# Codex 작업 가이드

## 프로젝트 개요
- FastAPI 기반 콘솔 로그 서버 템플릿입니다.
- 앱 팩토리와 엔트리포인트는 `console_log_server/app.py`와 `console_log_server/main.py`에 있습니다.
- 설정은 `console_log_server/core/settings.py`에서 `.env`를 읽어 캐시된 `get_settings()`로 제공합니다.
- 요청 로깅 및 파일 로깅은 `console_log_server/core/logging_config.py`와 미들웨어에서 처리합니다.

## 실행/개발 명령
- 의존성 설치: `uv sync`
- 개발 서버(리로드): `uv run console-log-server-dev`
- 운영 서버: `uv run console-log-server`
- 백그라운드 실행 스크립트: `./run_server_bg.sh` (환경 변수 `PORT`, `APP_CMD` 지원)

## 폴더 구조 요약
- `console_log_server/api`: 라우터/스키마/의존성 주입
- `console_log_server/services`: 비즈니스 로직 (`auth`, `room`, `ai`, `fortune`, `janus`, `langgraph`)
- `console_log_server/repositories`: 데이터 접근 계층
- `console_log_server/models`: SQLAlchemy ORM 모델
- `console_log_server/core`: 설정, DB, 로깅
- `tests`: pytest 스위트

## 주요 엔드포인트
- `GET /health`, `GET /hello`, `POST /auth/*`, `POST /ai/chat`, `POST /fortune/today`, `POST /rooms/*`
- 보호된 엔드포인트는 `Authorization: Bearer <token>` 필요 (`console_log_server/api/deps.py`).

## 외부 의존 및 환경
- Python 버전: `.python-version` 및 `pyproject.toml` 기준 3.14+
- DB: MySQL + SQLAlchemy(`pymysql`), URL은 `Settings.database_url`
- 마이그레이션: Alembic (`alembic/`, `alembic.ini`)
- LLM: 로컬 Ollama 필요 (`OLLAMA_HOST`, `OLLAMA_MODEL`) — `/ai/chat`, `/fortune/today` 사용
- Janus 연동: 방 생성/삭제 시 Admin API 호출 (`janus_*` 환경 변수)

## 테스트
- `uv sync --extra test`
- `uv run pytest`
- 테스트는 인메모리 SQLite로 DB 세션을 오버라이드합니다.

## 작업 시 유의사항
- 라우터 추가/변경은 `console_log_server/api/routers/__init__.py` 등록 필요.
- 설정값 변경 시 `get_settings()` 캐시를 고려해야 합니다.
- 기존 스타일(타입 힌트, 함수형 구조)을 유지하고 불필요한 포맷 변경은 피합니다.
