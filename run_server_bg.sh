#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

# 환경 변수 우선, 없으면 기본 포트 8000 사용
PORT="${PORT:-8000}"
APP_CMD="${APP_CMD:-uv run console-log-server}"
LOG_FILE="${LOG_DIR}/server.log"

echo "[console-log-server] 포트 ${PORT}에서 실행할 프로세스를 종료합니다(있다면)."
if PIDS="$(lsof -ti TCP:"${PORT}" 2>/dev/null)"; then
  if [[ -n "${PIDS}" ]]; then
    echo "  기존 프로세스 종료: ${PIDS}"
    kill ${PIDS}
  else
    echo "  종료할 프로세스 없음."
  fi
else
  echo "  lsof로 열린 포트를 확인하지 못했습니다(무시)."
fi

echo "[console-log-server] 백그라운드 실행(상용 모드): ${APP_CMD}"
nohup ${APP_CMD} > "${LOG_FILE}" 2>&1 &
NEW_PID=$!

echo "[console-log-server] 프로세스 PID=${NEW_PID}, 로그=${LOG_FILE}"
echo "  tail -f ${LOG_FILE}"
