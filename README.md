# console-log-server

FastAPI 기반의 기본 서버 템플릿입니다. 헬스 체크와 간단한 Hello API만 포함하지만, 로그인·회원관리·AI 챗봇 등 다양한 기능을 추가하기 쉬운 모듈 구조를 유지합니다.

## 폴더 구조

```
console_log_server/
├── __init__.py
├── app.py                 # FastAPI 앱 팩토리 및 전역 인스턴스
├── api/
│   ├── __init__.py        # 라우터 등록
│   ├── deps.py            # FastAPI 의존성 함수
│   ├── routers/           # 엔드포인트 모음 (health, hello, auth)
│   └── schemas/           # 요청/응답 DTO
│       ├── auth.py
│       └── responses.py
├── core/
│   ├── __init__.py
│   ├── settings.py        # Pydantic BaseSettings
│   └── database.py        # SQLAlchemy 엔진 관리
├── models/                # 도메인/ORM 모델
├── repositories/          # 데이터 접근 계층
├── services/              # 비즈니스 로직
├── utils/                 # 공용 유틸리티 (확장용)
├── main.py                # uvicorn 엔트리포인트
└── tests/                 # pytest 스위트
```

## 요구 사항

- [uv](https://github.com/astral-sh/uv) 0.2.0 이상
- Python 3.14+
- 로컬 Ollama에서 `qwen3:1.7b` 모델이 준비되어 있어야 `/ai/chat` 엔드포인트가 동작합니다. (`ollama pull qwen3:1.7b`)

## 빠른 시작

```bash
uv sync
uv run console-log-server-dev
```

개발 서버는 기본적으로 `http://127.0.0.1:8000`에서 동작합니다.

## 환경 변수

기본값은 `.env`에 저장되어 있습니다.

```
HOST=127.0.0.1
PORT=8000
DEBUG=false
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=console_log
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7
JWT_REFRESH_COOKIE_NAME=refresh_token
JWT_REFRESH_COOKIE_SECURE=false
JWT_REFRESH_COOKIE_SAMESITE=lax
JWT_SESSION_COOKIE_NAME=session_id
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:1.7b
```

## 데이터베이스 마이그레이션

Alembic을 사용해 스키마 변화를 관리합니다.

- 최신 스키마 적용: `uv run alembic upgrade head`
- 새 마이그레이션 생성(자동 생성 활용): `uv run alembic revision --autogenerate -m "change description"`
- 로컬 개발 환경에서 초기화 시 `alembic/` 디렉터리에 버전이 쌓이므로 소스 컨트롤에 커밋하세요.

## 테스트

```bash
uv sync --extra test
uv run pytest
```

설정 로딩과 기본 API 엔드포인트를 검증합니다.

## 커밋 규칙

명확하고 일관된 히스토리를 위해 다음 규칙을 지켜 주세요.

1. **메시지 형식**: `타입: 간단한 설명` (예: `feat: 사용자 인증 API 추가`)
2. **타입 가이드**
   - `feat`: 새로운 기능
   - `fix`: 버그 수정
   - `docs`: 문서만 변경
   - `refactor`: 리팩터링 (동작 변화 없음)
   - `test`: 테스트 코드 추가/수정
   - `chore`: 기타 자잘한 작업(빌드, 설정 등)
3. **본문**: 필요 시 변경 이유, 영향 범위를 한글로 작성하고 72자 이내 줄바꿈을 권장합니다.
4. **한 커밋 = 한 작업**: 의미 있는 단위로 작업을 나누고, 불필요한 포맷팅 변경은 별도 커밋으로 분리합니다.

## API

- `GET /health` — 헬스 체크
- `GET /hello` — "Hello, FastAPI!" 메시지를 반환
- `POST /auth/register` — 사용자 생성 + 액세스 토큰 반환 (리프레시 토큰은 HttpOnly 쿠키, 세션 ID는 일반 쿠키에 저장)
- `POST /auth/login` — 인증 후 액세스 토큰 갱신 (같은 세션 ID 기준으로 기존 리프레시 토큰 폐기)
- `POST /auth/refresh` — 쿠키에 저장된 리프레시 토큰/세션 정보로 액세스 토큰 재발급
- `POST /ai/chat` — 로컬 Ollama(`qwen3:1.7b`)를 사용한 챗봇 응답 반환, 보호된 엔드포인트

모든 보호된 API 요청에는 `Authorization: Bearer <access_token>` 헤더가 필요합니다.

이 템플릿을 기반으로 필요한 도메인 기능을 자유롭게 확장할 수 있습니다.
