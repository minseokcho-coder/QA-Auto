"""GeekNews 스크래퍼"""
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

from .base import BaseScraper, Article
from config import HOURS_LIMIT


class GeekNewsScraper(BaseScraper):
    """GeekNews (news.hada.io) 스크래퍼 - RSS 피드 사용"""

    name = "GeekNews"
    base_url = "https://news.hada.io"

    def scrape(self) -> list[Article]:
        """GeekNews RSS 피드에서 아티클 스크래핑"""
        articles = []

        rss_url = f"{self.base_url}/rss/news"

        try:
            feed = feedparser.parse(rss_url)

            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=HOURS_LIMIT)

            for entry in feed.entries[:30]:  # 최근 30개
                try:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    summary = entry.get("summary", "")

                    # 발행 시간 확인
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

                    # HTML 태그 제거
                    if summary:
                        soup = BeautifulSoup(summary, "html.parser")
                        summary = soup.get_text(strip=True)[:200]

                    if title and link:
                        articles.append(Article(
                            title=title,
                            url=link,
                            source=self.name,
                            summary=summary if summary else None,
                            published_at=published,
                        ))

                except Exception:
                    continue

        except Exception as e:
            print(f"[{self.name}] RSS 파싱 실패: {e}")

        # 키워드 필터링
        return self.filter_by_keywords(articles)
