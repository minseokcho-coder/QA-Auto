"""QA 자동화 설정 파일

기존 config.py 패턴을 따라 환경변수 기반으로 설정을 관리합니다.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env.qa 파일 로드 (존재하는 경우)
env_qa_path = Path(__file__).parent.parent / ".env.qa"
if env_qa_path.exists():
    load_dotenv(env_qa_path)
else:
    load_dotenv()  # 기본 .env 사용

# === 기본 URL 설정 ===
BASE_URL = os.getenv("QA_BASE_URL", "https://qa.hiddenmoney.co.kr")

# 환경별 URL
URLS = {
    "qa": "https://qa.hiddenmoney.co.kr",
    "staging": "https://staging.hiddenmoney.co.kr",
    "prod": "https://www.hiddenmoney.co.kr",
}

# === 브라우저 설정 ===
BROWSER = os.getenv("QA_BROWSER", "chrome")  # chrome, firefox, edge
HEADLESS = os.getenv("QA_HEADLESS", "false").lower() == "true"
WINDOW_WIDTH = int(os.getenv("QA_WINDOW_WIDTH", "1280"))
WINDOW_HEIGHT = int(os.getenv("QA_WINDOW_HEIGHT", "800"))

# === 타임아웃 설정 (초 단위) ===
DEFAULT_TIMEOUT = int(os.getenv("QA_DEFAULT_TIMEOUT", "10"))
IMPLICIT_WAIT = int(os.getenv("QA_IMPLICIT_WAIT", "5"))
PAGE_LOAD_TIMEOUT = int(os.getenv("QA_PAGE_LOAD_TIMEOUT", "30"))

# === 재시도 설정 ===
RETRY_COUNT = int(os.getenv("QA_RETRY_COUNT", "2"))
RETRY_DELAY = int(os.getenv("QA_RETRY_DELAY", "1"))

# === 경로 설정 ===
QA_ROOT = Path(__file__).parent
REPORTS_DIR = QA_ROOT / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
LOGS_DIR = REPORTS_DIR / "logs"

# 디렉토리 생성
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# === 로깅 설정 ===
LOG_LEVEL = os.getenv("QA_LOG_LEVEL", "INFO")

# === 리포트 설정 ===
REPORT_TITLE = "SAVETAX QA 자동화 테스트 리포트"
REPORT_DESCRIPTION = "세금 환급 서비스 QA 자동화 테스트 결과"

# === 디바이스 프로필 (반응형 테스트) ===
DEVICE_PROFILES = {
    "mobile_small": {"width": 320, "height": 568, "name": "iPhone SE (1세대)"},
    "mobile": {"width": 375, "height": 667, "name": "iPhone 8"},
    "mobile_large": {"width": 414, "height": 896, "name": "iPhone 11"},
    "tablet": {"width": 768, "height": 1024, "name": "iPad"},
    "desktop": {"width": 1280, "height": 800, "name": "데스크톱"},
    "desktop_large": {"width": 1920, "height": 1080, "name": "대형 데스크톱"},
}


def print_config():
    """현재 설정 출력"""
    print("=" * 50)
    print("QA 자동화 설정")
    print("=" * 50)
    print(f"BASE_URL: {BASE_URL}")
    print(f"BROWSER: {BROWSER}")
    print(f"HEADLESS: {HEADLESS}")
    print(f"WINDOW_SIZE: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    print(f"DEFAULT_TIMEOUT: {DEFAULT_TIMEOUT}s")
    print("=" * 50)


if __name__ == "__main__":
    print_config()
