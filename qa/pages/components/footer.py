"""푸터 컴포넌트"""
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from qa.core.base_page import Locator
from qa.qa_config import DEFAULT_TIMEOUT


class FooterLocators:
    """푸터 로케이터"""

    FOOTER = Locator(By.TAG_NAME, "footer", "푸터")
    LINKS = Locator(By.CSS_SELECTOR, "footer a", "푸터 링크")
    COPYRIGHT = Locator(By.CSS_SELECTOR, "footer .copyright, footer p", "저작권")
    SOCIAL_LINKS = Locator(By.CSS_SELECTOR, "footer .social a, footer a[href*='instagram'], footer a[href*='facebook']", "소셜 링크")


class Footer:
    """푸터 컴포넌트

    페이지 하단의 푸터 영역을 다룹니다.
    """

    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.locators = FooterLocators

    def is_visible(self) -> bool:
        """푸터 표시 여부 확인"""
        try:
            element = self.driver.find_element(*self.locators.FOOTER.as_tuple())
            return element.is_displayed()
        except:
            return False

    def get_all_links(self) -> list:
        """푸터 링크 목록 반환"""
        try:
            elements = self.driver.find_elements(*self.locators.LINKS.as_tuple())
            return [
                {"text": el.text, "href": el.get_attribute("href")}
                for el in elements
            ]
        except:
            return []

    def get_copyright_text(self) -> str:
        """저작권 텍스트 반환"""
        try:
            element = self.driver.find_element(*self.locators.COPYRIGHT.as_tuple())
            return element.text
        except:
            return ""

    def get_social_links(self) -> list:
        """소셜 미디어 링크 반환"""
        try:
            elements = self.driver.find_elements(*self.locators.SOCIAL_LINKS.as_tuple())
            return [el.get_attribute("href") for el in elements]
        except:
            return []

    def scroll_to_footer(self) -> None:
        """푸터로 스크롤"""
        element = self.driver.find_element(*self.locators.FOOTER.as_tuple())
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
