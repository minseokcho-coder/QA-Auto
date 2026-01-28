"""슬랙 알림 모듈"""
import os
import requests
from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from scrapers.base import Article
from config import SLACK_WEBHOOK_URL


# Bot Token 설정 (환경변수에서 로드)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "")


class SlackNotifier:
    """슬랙 알림 전송 (Webhook 또는 Bot Token 방식)"""

    def __init__(self, webhook_url: str = None, bot_token: str = None, channel: str = None):
        self.webhook_url = webhook_url or SLACK_WEBHOOK_URL
        self.bot_token = bot_token or SLACK_BOT_TOKEN
        self.channel = channel or SLACK_CHANNEL

        if self.bot_token:
            self.client = WebClient(token=self.bot_token)
        else:
            self.client = None

    def send(self, articles: list[Article], test_mode: bool = False) -> bool:
        """아티클 목록을 슬랙으로 전송"""
        if not articles:
            print("전송할 아티클이 없습니다.")
            return True

        blocks = self._format_blocks(articles)
        text = self._format_fallback(articles)

        if test_mode:
            print("=" * 50)
            print("[테스트 모드] 슬랙 메시지 미리보기:")
            print("=" * 50)
            try:
                print(text)
            except UnicodeEncodeError:
                clean_message = text.encode('ascii', 'ignore').decode('ascii')
                print(clean_message)
            print("=" * 50)
            return True

        # Bot Token 방식 (우선)
        if self.bot_token and self.channel:
            return self._send_via_bot(blocks, text, len(articles))

        # Webhook 방식 (대체)
        if self.webhook_url:
            return self._send_via_webhook(blocks, text, len(articles))

        print("슬랙 설정이 없습니다.")
        return False

    def _send_via_bot(self, blocks: list, text: str, article_count: int) -> bool:
        """Bot Token으로 메시지 전송"""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=text,
                unfurl_links=False,
                unfurl_media=False,
            )
            print(f"슬랙 전송 성공 (Bot): {article_count}개 아티클 → {self.channel}")
            return True

        except SlackApiError as e:
            print(f"슬랙 전송 실패 (Bot): {e.response['error']}")
            return False

    def _send_via_webhook(self, blocks: list, text: str, article_count: int) -> bool:
        """Webhook으로 메시지 전송"""
        try:
            response = requests.post(
                self.webhook_url,
                json={"blocks": blocks, "text": text},
                timeout=10
            )
            response.raise_for_status()
            print(f"슬랙 전송 성공 (Webhook): {article_count}개 아티클")
            return True

        except requests.RequestException as e:
            print(f"슬랙 전송 실패 (Webhook): {e}")
            return False

    def _format_blocks(self, articles: list[Article]) -> list:
        """Slack Block Kit 형식으로 포맷팅"""
        today = datetime.now().strftime("%Y년 %m월 %d일")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📚 오늘의 PM/PO 아티클",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 {today} | 총 *{len(articles)}개* 아티클"
                    }
                ]
            },
            {"type": "divider"}
        ]

        # 출처별로 그룹핑
        by_source: dict[str, list[Article]] = {}
        for article in articles:
            if article.source not in by_source:
                by_source[article.source] = []
            by_source[article.source].append(article)

        for source, source_articles in by_source.items():
            # 소스 헤더
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🏷️ {source}* ({len(source_articles)}개)"
                }
            })

            # 각 아티클
            for article in source_articles[:10]:  # 소스당 최대 10개
                article_text = f"• <{article.url}|{article.title}>"
                if article.summary:
                    summary = article.summary[:80] + "..." if len(article.summary) > 80 else article.summary
                    article_text += f"\n   _{summary}_"

                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": article_text
                    }
                })

            blocks.append({"type": "divider"})

        # 푸터
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "🤖 _PM Scraper Bot에서 자동 수집_"
                }
            ]
        })

        return blocks

    def _format_fallback(self, articles: list[Article]) -> str:
        """알림용 텍스트 (blocks 미지원 클라이언트용)"""
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [f"📚 오늘의 PM/PO 아티클 ({today})"]
        lines.append(f"총 {len(articles)}개 아티클이 발견되었습니다.")
        return "\n".join(lines)

    def send_error(self, error_message: str) -> bool:
        """에러 메시지를 슬랙으로 전송"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *PM Scraper Bot 오류*\n\n```{error_message}```"
                }
            }
        ]
        text = f"⚠️ PM Scraper Bot 오류: {error_message}"

        if self.bot_token and self.channel:
            try:
                self.client.chat_postMessage(
                    channel=self.channel,
                    blocks=blocks,
                    text=text
                )
                return True
            except SlackApiError:
                return False

        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json={"blocks": blocks, "text": text}, timeout=10)
                return True
            except requests.RequestException:
                return False

        return False
