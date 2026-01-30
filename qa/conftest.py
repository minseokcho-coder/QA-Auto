"""pytest 공통 fixtures 및 설정"""
import os
import pytest
from datetime import datetime
from typing import Generator
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from qa.qa_config import (
    BASE_URL,
    BROWSER,
    HEADLESS,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    IMPLICIT_WAIT,
    SCREENSHOTS_DIR,
)
from qa.pages.home_page import HomePage


# --- 브라우저 Fixtures ---


@pytest.fixture(scope="session")
def browser_options():
    """브라우저 옵션 설정"""
    if BROWSER.lower() == "firefox":
        options = FirefoxOptions()
        if HEADLESS:
            options.add_argument("--headless")
        return options
    else:
        # 기본값: Chrome
        options = ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")
        # 한글 처리
        options.add_argument("--lang=ko-KR")
        return options


@pytest.fixture(scope="function")
def driver(browser_options) -> Generator[webdriver.Remote, None, None]:
    """WebDriver 인스턴스 생성 (테스트 함수별)"""
    if BROWSER.lower() == "firefox":
        service = Service(GeckoDriverManager().install())
        _driver = webdriver.Firefox(service=service, options=browser_options)
    else:
        service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=service, options=browser_options)

    _driver.implicitly_wait(IMPLICIT_WAIT)
    _driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)

    yield _driver

    # Teardown: 브라우저 종료
    _driver.quit()


@pytest.fixture(scope="class")
def class_driver(browser_options) -> Generator[webdriver.Remote, None, None]:
    """WebDriver 인스턴스 생성 (테스트 클래스별 - 성능 최적화용)"""
    if BROWSER.lower() == "firefox":
        service = Service(GeckoDriverManager().install())
        _driver = webdriver.Firefox(service=service, options=browser_options)
    else:
        service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=service, options=browser_options)

    _driver.implicitly_wait(IMPLICIT_WAIT)
    _driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)

    yield _driver

    _driver.quit()


# --- 페이지 Fixtures ---


@pytest.fixture
def home_page(driver) -> HomePage:
    """홈페이지 Page Object"""
    page = HomePage(driver)
    page.open(BASE_URL)
    return page


# --- 유틸리티 Fixtures ---


@pytest.fixture
def base_url() -> str:
    """베이스 URL 반환"""
    return BASE_URL


@pytest.fixture(autouse=True)
def test_setup_teardown(request, driver):
    """각 테스트 전후 처리"""
    # Setup
    test_name = request.node.name
    print(f"\n[테스트 시작] {test_name}")

    yield

    # Teardown: 테스트 실패 시 스크린샷 저장
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{test_name}_{timestamp}.png"
        filepath = os.path.join(str(SCREENSHOTS_DIR), filename)
        driver.save_screenshot(filepath)
        print(f"[스크린샷 저장] {filepath}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """테스트 결과 리포트 훅 (스크린샷 저장용)"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# --- 반응형 테스트용 Fixtures ---


@pytest.fixture(
    params=[
        (375, 667, "mobile"),  # iPhone SE
        (768, 1024, "tablet"),  # iPad
        (1280, 800, "desktop"),  # 일반 데스크톱
        (1920, 1080, "large"),  # 대형 데스크톱
    ]
)
def responsive_driver(request, browser_options) -> Generator[tuple, None, None]:
    """반응형 테스트용 드라이버 (다양한 화면 크기)"""
    width, height, device = request.param

    if BROWSER.lower() == "firefox":
        service = Service(GeckoDriverManager().install())
        _driver = webdriver.Firefox(service=service, options=browser_options)
    else:
        service = Service(ChromeDriverManager().install())
        _driver = webdriver.Chrome(service=service, options=browser_options)

    _driver.set_window_size(width, height)
    _driver.implicitly_wait(IMPLICIT_WAIT)

    yield _driver, device

    _driver.quit()
