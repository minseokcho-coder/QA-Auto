"""페이지 오브젝트 베이스 클래스

기존 BaseScraper 패턴을 참고하여 설계되었습니다.
모든 페이지 객체는 이 클래스를 상속받아 구현합니다.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import sys
sys.path.insert(0, str(__file__).rsplit("qa", 1)[0])
from qa.qa_config import DEFAULT_TIMEOUT


@dataclass
class Locator:
    """요소 로케이터 정의"""
    by: str  # By.ID, By.CSS_SELECTOR 등
    value: str
    description: str = ""  # 한글 설명

    def as_tuple(self) -> Tuple[str, str]:
        """(By, value) 튜플 반환"""
        return (self.by, self.value)


class BasePage(ABC):
    """페이지 오브젝트 베이스 클래스

    기존 BaseScraper 패턴을 따라 추상 클래스로 구현합니다.
    모든 페이지 객체는 이 클래스를 상속받아 구현합니다.
    """

    # 서브클래스에서 정의해야 하는 속성
    name: str = "base"  # 페이지 이름 (한글)
    path: str = ""  # URL 경로 (예: "/faq")

    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    @property
    @abstractmethod
    def page_loaded_locator(self) -> Locator:
        """페이지 로드 완료 확인용 로케이터

        페이지가 정상 로드되었음을 확인할 수 있는 고유 요소의 로케이터를 반환합니다.
        """
        pass

    def is_loaded(self) -> bool:
        """페이지가 정상 로드되었는지 확인"""
        try:
            locator = self.page_loaded_locator
            self.wait.until(EC.presence_of_element_located(locator.as_tuple()))
            return True
        except TimeoutException:
            return False

    def open(self, base_url: str) -> "BasePage":
        """페이지 열기"""
        url = f"{base_url.rstrip('/')}{self.path}"
        self.driver.get(url)
        return self

    # --- 요소 찾기 메서드 ---

    def find_element(self, locator: Locator) -> WebElement:
        """단일 요소 찾기"""
        return self.driver.find_element(*locator.as_tuple())

    def find_elements(self, locator: Locator) -> List[WebElement]:
        """복수 요소 찾기"""
        return self.driver.find_elements(*locator.as_tuple())

    def wait_for_element(
        self, locator: Locator, timeout: Optional[int] = None
    ) -> WebElement:
        """요소가 나타날 때까지 대기"""
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.presence_of_element_located(locator.as_tuple()))

    def wait_for_clickable(
        self, locator: Locator, timeout: Optional[int] = None
    ) -> WebElement:
        """요소가 클릭 가능해질 때까지 대기"""
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.element_to_be_clickable(locator.as_tuple()))

    def wait_for_visible(
        self, locator: Locator, timeout: Optional[int] = None
    ) -> WebElement:
        """요소가 보일 때까지 대기"""
        wait = WebDriverWait(self.driver, timeout or self.timeout)
        return wait.until(EC.visibility_of_element_located(locator.as_tuple()))

    # --- 액션 메서드 ---

    def click(self, locator: Locator) -> None:
        """요소 클릭"""
        element = self.wait_for_clickable(locator)
        element.click()

    def input_text(self, locator: Locator, text: str, clear_first: bool = True) -> None:
        """텍스트 입력"""
        element = self.wait_for_visible(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)

    def get_text(self, locator: Locator) -> str:
        """요소의 텍스트 가져오기"""
        element = self.wait_for_visible(locator)
        return element.text

    def is_element_present(self, locator: Locator) -> bool:
        """요소 존재 여부 확인"""
        try:
            self.driver.find_element(*locator.as_tuple())
            return True
        except NoSuchElementException:
            return False

    def is_element_visible(self, locator: Locator) -> bool:
        """요소 표시 여부 확인"""
        try:
            element = self.driver.find_element(*locator.as_tuple())
            return element.is_displayed()
        except NoSuchElementException:
            return False

    def get_current_url(self) -> str:
        """현재 URL 반환"""
        return self.driver.current_url

    def get_title(self) -> str:
        """페이지 타이틀 반환"""
        return self.driver.title

    def take_screenshot(self, filename: str) -> str:
        """스크린샷 저장"""
        from qa.qa_config import SCREENSHOTS_DIR
        filepath = str(SCREENSHOTS_DIR / filename)
        self.driver.save_screenshot(filepath)
        return filepath
