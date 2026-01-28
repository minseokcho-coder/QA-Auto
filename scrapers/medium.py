"""Medium 스크래퍼"""
import requests
from bs4 import BeautifulSoup
import feedparser

from .base import BaseScraper, Article


class MediumScraper(BaseScraper):
    """Medium 스크래퍼 (Product Management 태그)"""

    name = "Medium"
    base_url = "https://medium.com"

    def scrape(self) -> list[Article]:
        """Medium에서 Product Management 관련 아티클 스크래핑"""
        articles = []

        # Medium RSS 피드 사용
        rss_urls = [
            "https://medium.com/feed/tag/product-management",
            "https://medium.com/feed/tag/product-manager",
            "https://medium.com/feed/tag/product-owner",
        ]

        for rss_url in rss_urls:
            try:
                feed = feedparser.parse(rss_url)

                for entry in feed.entries[:10]:  # 태그당 최근 10개
                    try:
                        title = entry.get("title", "")
                        link = entry.get("link", "")
                        summary = entry.get("summary", "")

                        # HTML 태그 제거
                        if summary:
                            soup = BeautifulSoup(summary, "html.parser")
                            summary = soup.get_text(strip=True)[:200]

                        if title and link:
                            # 중복 체크
                            if not any(a.url == link for a in articles):
                                articles.append(Article(
                                    title=title,
                                    url=link,
                                    source=self.name,
                                    summary=summary if summary else None,
                                ))
                    except Exception:
                        continue

            except Exception as e:
                print(f"[{self.name}] RSS 파싱 실패 ({rss_url}): {e}")
                continue

        # RSS가 실패하면 웹 스크래핑 시도
        if not articles:
            try:
                tag_url = f"{self.base_url}/tag/product-management"
                response = requests.get(tag_url, headers=self.headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    # 아티클 링크 찾기
                    article_links = soup.select("article a[href*='/'], div[data-testid] a[href*='/']")

                    seen_urls = set()
                    for link in article_links:
                        try:
                            href = link.get("href", "")
                            title_elem = link.select_one("h2, h3")

                            if title_elem:
                                title = title_elem.get_text(strip=True)
                            else:
                                title = link.get_text(strip=True)

                            if href and title and len(title) > 10:
                                article_url = href if href.startswith("http") else f"{self.base_url}{href}"

                                if article_url not in seen_urls:
                                    seen_urls.add(article_url)
                                    articles.append(Article(
                                        title=title,
                                        url=article_url,
                                        source=self.name,
                                    ))
                        except Exception:
                            continue

            except requests.RequestException as e:
                print(f"[{self.name}] 웹 스크래핑 실패: {e}")

        return articles  # Medium은 이미 PM 태그이므로 추가 필터링 불필요
