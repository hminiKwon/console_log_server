# Repository Guidelines

## 프로젝트 구조 & 모듈 구성
핵심 애플리케이션은 `console_log_server/`에 있으며, FastAPI 앱 팩토리는 `app.py`, 실행 엔트리포인트는 `main.py`에 있습니다. API 라우터와 DTO 스키마는 각각 `console_log_server/api/routers`, `console_log_server/api/schemas`에서 관리합니다. 설정과 DB 연결은 `console_log_server/core`에 모여 있고, 도메인 계층은 `models/`, `repositories/`, `services/`로 분리되어 있습니다. 테스트는 `tests/`, 마이그레이션은 `alembic/` 디렉터리를 사용합니다.

## 빌드, 테스트, 개발 명령
- `uv sync`: 런타임 의존성 설치.
- `uv run console-log-server-dev`: 로컬 개발 서버 실행(기본 `http://127.0.0.1:8000`).
- `uv run console-log-server`: 프로덕션 엔트리포인트 실행.
- `uv run alembic upgrade head`: 최신 스키마 적용.
- `uv run alembic revision --autogenerate -m "message"`: 새 마이그레이션 생성.
- `uv sync --extra test` 후 `uv run pytest`: 테스트 의존성 설치 및 실행.

## 코딩 스타일 & 네이밍 규칙
Python PEP 8을 따르고 들여쓰기는 4칸을 사용합니다. 모듈/함수/변수는 `snake_case`, 클래스와 Pydantic 스키마는 `PascalCase`를 권장합니다. 라우터는 기능 단위로 `console_log_server/api/routers`에 추가하고, 대응하는 스키마는 `console_log_server/api/schemas`에 배치하세요.

## 테스트 가이드라인
테스트 프레임워크는 `pytest`이며 파일명은 `test_*.py` 규칙을 따릅니다(예: `tests/test_api.py`). 신규 엔드포인트나 설정 변경 시 최소 1개의 테스트를 추가하고, 공통 픽스처는 `tests/conftest.py`를 재사용합니다.

## 커밋 & PR 가이드라인
커밋 메시지는 `type: 요약` 형식으로 작성합니다(예: `feat: 인증 리프레시 추가`). 타입은 `feat`, `fix`, `docs`, `refactor`, `test`, `chore`를 사용합니다. PR에는 변경 요약, 마이그레이션/환경변수 변경 여부, 실행한 테스트 명령을 명시하세요.

## 설정 & 보안 팁
런타임 설정은 `.env`에서 읽습니다(`README.md`의 기본값 참고). `JWT_SECRET_KEY`, `GOOGLE_API_KEY`, DB 비밀번호 같은 민감 정보는 커밋하지 마세요. AI 챗 엔드포인트를 사용할 경우 `OLLAMA_HOST`와 `OLLAMA_MODEL`이 로컬 Ollama 설정과 일치해야 합니다.
