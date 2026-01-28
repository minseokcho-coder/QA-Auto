"""베이스 스크래퍼 클래스"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from config import KEYWORDS


@dataclass
class Article:
    """스크래핑된 아티클 정보"""

    title: str
    url: str
    source: str
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "summary": self.summary,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }


class BaseScraper(ABC):
    """스크래퍼 베이스 클래스"""

    name: str = "base"
    base_url: str = ""

    def __init__(self, keywords: list[str] = None):
        self.keywords = keywords or KEYWORDS
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @abstractmethod
    def scrape(self) -> list[Article]:
        """사이트에서 아티클 스크래핑"""
        pass

    def matches_keywords(self, text: str) -> bool:
        """텍스트가 키워드와 매칭되는지 확인"""
        if not text:
            return False
        text_lower = text.lower()
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                return True
        return False

    def filter_by_keywords(self, articles: list[Article]) -> list[Article]:
        """키워드에 매칭되는 아티클만 필터링"""
        filtered = []
        for article in articles:
            # 제목 또는 요약에서 키워드 매칭
            if self.matches_keywords(article.title) or self.matches_keywords(article.summary):
                filtered.append(article)
        return filtered
