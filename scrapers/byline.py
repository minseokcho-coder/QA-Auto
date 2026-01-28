"""바이라인네트워크 스크래퍼"""
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone

from .base import BaseScraper, Article


class BylineScraper(BaseScraper):
    """바이라인네트워크 (byline.network) 스크래퍼 - IT 뉴스"""

    name = "바이라인네트워크"
    base_url = "https://byline.network"

    def scrape(self) -> list[Article]:
        """바이라인네트워크 RSS 피드에서 아티클 스크래핑"""
        articles = []

        rss_url = f"{self.base_url}/feed"

        try:
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:20]:
                try:
                    title = entry.get("title", "")
                    link = entry.get("link", "")
                    summary = entry.get("summary", "")

                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

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

        filtered = self.filter_by_keywords(articles)
        return filtered if filtered else articles[:10]
