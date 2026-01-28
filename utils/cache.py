"""중복 방지용 캐시 모듈"""
import json
import os
from datetime import datetime
from typing import Set

from config import CACHE_FILE


class Cache:
    """이미 전송한 글의 URL을 저장하여 중복 전송 방지"""

    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.sent_urls: Set[str] = set()
        self._load()

    def _load(self) -> None:
        """캐시 파일에서 URL 목록 로드"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.sent_urls = set(data.get("urls", []))
            except (json.JSONDecodeError, IOError):
                self.sent_urls = set()

    def save(self) -> None:
        """캐시 파일에 URL 목록 저장"""
        data = {
            "urls": list(self.sent_urls),
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def is_sent(self, url: str) -> bool:
        """URL이 이미 전송되었는지 확인"""
        return url in self.sent_urls

    def mark_sent(self, url: str) -> None:
        """URL을 전송 완료로 표시"""
        self.sent_urls.add(url)

    def filter_new(self, urls: list[str]) -> list[str]:
        """새로운 URL만 필터링"""
        return [url for url in urls if not self.is_sent(url)]

    def cleanup(self, max_entries: int = 10000) -> None:
        """캐시 크기 제한 (오래된 항목 삭제)"""
        if len(self.sent_urls) > max_entries:
            # 가장 오래된 항목부터 삭제 (set이므로 순서 보장 안됨, 랜덤 삭제)
            excess = len(self.sent_urls) - max_entries
            urls_list = list(self.sent_urls)
            self.sent_urls = set(urls_list[excess:])
