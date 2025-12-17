from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status

from console_log_server.api.schemas.fortune import FortuneRequest, FortuneResponse
from console_log_server.core.logging_config import get_logger
from console_log_server.services.prompts import FORTUNE_PROMPT
from console_log_server.utils.ollama import OllamaClient


class FortuneService:
    """LLM 기반 오늘의 운세 생성 서비스."""

    def __init__(self, client: OllamaClient | None = None) -> None:
        self.client = client or OllamaClient()
        self.logger = get_logger(__name__)

    def get_today_fortune(self, req: FortuneRequest) -> FortuneResponse:
        birth_time_label = self._birth_time_label(req.birth_time)
        today_date = self._today_kst()
        prompt = FORTUNE_PROMPT.format(
            birth_date=req.birth_date,
            calendar=req.calendar,
            gender=req.gender,
            birth_time=birth_time_label,
            today_date=today_date,
        )
        raw = self.client.chat(prompt)
        try:
            data = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            self.logger.error("fortune_json_parse_error raw=%s err=%s", raw, exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="운세 생성에 실패했습니다.",
            ) from exc

        return FortuneResponse(**data)

    @staticmethod
    def _birth_time_label(birth_time: int | None) -> str:
        branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
        if birth_time is None:
            return "미상"
        if 0 <= birth_time < len(branches):
            return branches[birth_time]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="birth_time은 0~11 범위여야 합니다.",
        )

    @staticmethod
    def _today_kst() -> str:
        """오늘 날짜(YYYY-MM-DD)를 KST 기준으로 반환."""

        return datetime.now(tz=ZoneInfo("Asia/Seoul")).date().isoformat()
