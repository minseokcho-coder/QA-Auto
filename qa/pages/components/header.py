"""헤더 컴포넌트"""
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from qa.core.base_page import Locator
from qa.qa_config import DEFAULT_TIMEOUT


class HeaderLocators:
    """헤더 로케이터"""

    HEADER = Locator(By.TAG_NAME, "header", "헤더")
    LOGO = Locator(By.CSS_SELECTOR, "header img, header svg, header .logo", "로고")
    NAV = Locator(By.CSS_SELECTOR, "header nav", "네비게이션")
    NAV_LINKS = Locator(By.CSS_SELECTOR, "header nav a", "네비게이션 링크")
    LOGIN_BUTTON = Locator(By.CSS_SELECTOR, "header button, header a.login", "로그인 버튼")


class Header:
    """헤더 컴포넌트

    페이지 상단의 헤더 영역을 다룹니다.
    """

    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.locators = HeaderLocators

    def is_visible(self) -> bool:
        """헤더 표시 여부 확인"""
        try:
            element = self.driver.find_element(*self.locators.HEADER.as_tuple())
            return element.is_displayed()
        except:
            return False

    def is_logo_visible(self) -> bool:
        """로고 표시 여부 확인"""
        try:
            element = self.driver.find_element(*self.locators.LOGO.as_tuple())
            return element.is_displayed()
        except:
            return False

    def get_nav_links(self) -> list:
        """네비게이션 링크 목록 반환"""
        try:
            elements = self.driver.find_elements(*self.locators.NAV_LINKS.as_tuple())
            return [
                {"text": el.text, "href": el.get_attribute("href")}
                for el in elements
            ]
        except:
            return []

    def click_logo(self) -> None:
        """로고 클릭 (홈으로 이동)"""
        element = self.wait.until(
            EC.element_to_be_clickable(self.locators.LOGO.as_tuple())
        )
        element.click()

    def click_login(self) -> None:
        """로그인 버튼 클릭"""
        element = self.wait.until(
            EC.element_to_be_clickable(self.locators.LOGIN_BUTTON.as_tuple())
        )
        element.click()
