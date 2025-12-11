from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from console_log_server.core import get_settings
from console_log_server.core.logging_config import get_logger

logger = get_logger(__name__)


def get_current_datetime(tz: str = "Asia/Seoul") -> str:
    """지정된 타임존의 ISO 날짜/시간 문자열."""

    try:
        now = datetime.now(tz=ZoneInfo(tz))
    except Exception:
        now = datetime.now(tz=timezone.utc)
        logger.warning("Invalid timezone '%s', fallback to UTC", tz)
    result = now.isoformat()
    logger.debug("current_datetime tz=%s value=%s", tz, result)
    return result


def google_search(query: str, *, num_results: int = 3) -> str:
    """
    Google Custom Search API로 웹 검색. API 키와 CSE ID 필요.

    결과는 제목과 링크를 요약한 문자열로 반환.
    """

    settings = get_settings()
    if not settings.google_api_key or not settings.google_cse_id:
        logger.warning("Google search skipped: missing API key or CSE ID")
        return "google_search_error: missing GOOGLE_API_KEY or GOOGLE_CSE_ID"

    params = urllib.parse.urlencode(
        {
            "key": settings.google_api_key,
            "cx": settings.google_cse_id,
            "q": query,
            "num": num_results,
        }
    )
    url = f"https://www.googleapis.com/customsearch/v1?{params}"

    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # nosec B310
            data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        logger.error("google_search_error query=%s err=%s", query, exc)
        return f"google_search_error: {exc}"

    items = data.get("items") or []
    if not items:
        logger.info("google_search_empty query=%s", query)
        return "google_search_empty"

    lines = []
    for item in items[:num_results]:
        title = item.get("title", "").strip()
        link = item.get("link", "").strip()
        snippet = (item.get("snippet") or "").strip()
        lines.append(f"- {title} | {link} | {snippet}")

    result = "google_search_results:\n" + "\n".join(lines)
    logger.debug("google_search query=%s results=%d", query, len(lines))
    return result
