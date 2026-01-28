"""디스콰이엇 스크래퍼 - 현재 비활성화됨

디스콰이엇은 클라이언트 사이드 렌더링을 사용하여
일반적인 HTTP 요청으로는 콘텐츠를 가져올 수 없습니다.
Selenium/Playwright 등의 헤드리스 브라우저가 필요합니다.
"""
from .base import BaseScraper, Article


class DisquietScraper(BaseScraper):
    """디스콰이엇 (disquiet.io) 스크래퍼 - 현재 비활성화"""

    name = "디스콰이엇"
    base_url = "https://disquiet.io"

    def scrape(self) -> list[Article]:
        """디스콰이엇 스크래핑 - CSR로 인해 현재 비활성화"""
        # 디스콰이엇은 클라이언트 사이드 렌더링(CSR)을 사용하여
        # 일반 HTTP 요청으로는 콘텐츠를 가져올 수 없음
        # 추후 Selenium/Playwright 통합 시 구현 예정
        return []
