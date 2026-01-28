"""브런치 스크래퍼 - 현재 비활성화됨

브런치는 클라이언트 사이드 렌더링을 사용하여
일반적인 HTTP 요청으로는 콘텐츠를 가져올 수 없습니다.
Selenium/Playwright 등의 헤드리스 브라우저가 필요합니다.
"""
from .base import BaseScraper, Article


class BrunchScraper(BaseScraper):
    """브런치 (brunch.co.kr) 스크래퍼 - 현재 비활성화"""

    name = "브런치"
    base_url = "https://brunch.co.kr"

    def scrape(self) -> list[Article]:
        """브런치 스크래핑 - CSR로 인해 현재 비활성화"""
        # 브런치는 클라이언트 사이드 렌더링(CSR)을 사용하여
        # 일반 HTTP 요청으로는 콘텐츠를 가져올 수 없음
        # 추후 Selenium/Playwright 통합 시 구현 예정
        return []
