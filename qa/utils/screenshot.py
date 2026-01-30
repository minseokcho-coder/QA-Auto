"""스크린샷 유틸리티"""
import os
from datetime import datetime
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver

from qa.qa_config import SCREENSHOTS_DIR


def take_screenshot(driver: WebDriver, name: str, subfolder: str = "") -> str:
    """스크린샷 저장

    Args:
        driver: WebDriver 인스턴스
        name: 파일명 (확장자 없이)
        subfolder: 하위 폴더명 (선택)

    Returns:
        저장된 파일 경로
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"

    if subfolder:
        save_dir = SCREENSHOTS_DIR / subfolder
        save_dir.mkdir(parents=True, exist_ok=True)
    else:
        save_dir = SCREENSHOTS_DIR

    filepath = save_dir / filename
    driver.save_screenshot(str(filepath))

    return str(filepath)


def take_full_page_screenshot(driver: WebDriver, name: str) -> str:
    """전체 페이지 스크린샷 (스크롤 포함)

    Args:
        driver: WebDriver 인스턴스
        name: 파일명 (확장자 없이)

    Returns:
        저장된 파일 경로
    """
    # 페이지 전체 높이 계산
    total_height = driver.execute_script("return document.body.scrollHeight")
    viewport_height = driver.execute_script("return window.innerHeight")

    # 원래 크기 저장
    original_size = driver.get_window_size()

    # 전체 페이지 크기로 창 조정 (Chrome에서만 동작)
    try:
        driver.set_window_size(original_size["width"], total_height)
        filepath = take_screenshot(driver, f"{name}_full")
    finally:
        # 원래 크기로 복원
        driver.set_window_size(original_size["width"], original_size["height"])

    return filepath


def compare_screenshots(image1_path: str, image2_path: str) -> float:
    """두 스크린샷 비교 (향후 구현)

    Args:
        image1_path: 첫 번째 이미지 경로
        image2_path: 두 번째 이미지 경로

    Returns:
        유사도 (0.0 ~ 1.0)
    """
    # TODO: Pillow 또는 pixelmatch로 구현
    raise NotImplementedError("스크린샷 비교 기능은 아직 구현되지 않았습니다")


def cleanup_old_screenshots(days: int = 7) -> int:
    """오래된 스크린샷 정리

    Args:
        days: 보관 기간 (일)

    Returns:
        삭제된 파일 수
    """
    import time

    cutoff = time.time() - (days * 24 * 60 * 60)
    deleted = 0

    for filepath in SCREENSHOTS_DIR.glob("**/*.png"):
        if filepath.stat().st_mtime < cutoff:
            filepath.unlink()
            deleted += 1

    return deleted
