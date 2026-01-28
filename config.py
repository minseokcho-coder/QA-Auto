"""설정 파일"""
import os
from dotenv import load_dotenv

load_dotenv()

# Slack 설정
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# 스케줄 설정
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")

# 캐시 설정
CACHE_FILE = os.getenv("CACHE_FILE", "cache.json")

# 스크래핑 시간 제한 (시간 단위)
HOURS_LIMIT = int(os.getenv("HOURS_LIMIT", "24"))

# 검색 키워드
KEYWORDS = [
    "PM",
    "PO",
    "프로덕트",
    "프로덕트 매니저",
    "프로덕트 오너",
    "기획",
    "기획자",
    "서비스 기획",
    "product manager",
    "product owner",
    "product management",
    "프로덕트 디자인",
    "UX",
    "사용자 경험",
]

# 각 스크래퍼 활성화 여부
SCRAPERS_ENABLED = {
    "yozm": True,
    "brunch": False,
    "medium": False,
    "geeknews": True,
    "disquiet": False,
    "outstanding": True,      # 아웃스탠딩
    "venturesquare": True,    # 벤처스퀘어
    "platum": True,           # 플래텀
    "byline": True,           # 바이라인네트워크
}

# 최대 아티클 수 제한
MAX_ARTICLES = 20
