"""SAVETAX 홈페이지 Page Object

기존 YozmScraper가 BaseScraper를 상속받는 패턴을 따릅니다.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from qa.core.base_page import BasePage, Locator


class HomePageLocators:
    """홈페이지 로케이터 정의

    CSS Selector 또는 XPath를 사용하여 요소를 찾습니다.
    한글 description으로 로케이터 용도를 명확히 합니다.
    """

    # 메인 요소
    BODY = Locator(By.TAG_NAME, "body", "페이지 바디")
    MAIN_LOGO = Locator(By.CSS_SELECTOR, "header img, header svg, .logo", "메인 로고")
    MAIN_TITLE = Locator(By.CSS_SELECTOR, "h1, .main-title", "메인 타이틀")

    # 네비게이션
    NAV_MENU = Locator(By.CSS_SELECTOR, "nav, header", "메인 네비게이션")
    NAV_LINKS = Locator(By.CSS_SELECTOR, "nav a, header a", "네비게이션 링크")

    # CTA 버튼
    CTA_BUTTONS = Locator(By.CSS_SELECTOR, "button, a.btn, .cta", "CTA 버튼들")

    # 섹션
    SECTIONS = Locator(By.CSS_SELECTOR, "section, .section", "섹션들")


class HomePage(BasePage):
    """SAVETAX 홈페이지 Page Object

    메인 랜딩 페이지의 요소 및 동작을 정의합니다.
    로그인 없이 접근 가능한 공개 페이지입니다.
    """

    name = "홈페이지"
    path = "/"

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
        self.locators = HomePageLocators

    @property
    def page_loaded_locator(self) -> Locator:
        """페이지 로드 확인용 로케이터 - body 태그"""
        return self.locators.BODY

    # --- 검증 메서드 ---

    def get_page_title(self) -> str:
        """페이지 타이틀 반환"""
        return self.get_title()

    def is_logo_visible(self) -> bool:
        """로고 표시 여부 확인"""
        return self.is_element_visible(self.locators.MAIN_LOGO)

    def is_navigation_visible(self) -> bool:
        """네비게이션 표시 여부 확인"""
        return self.is_element_visible(self.locators.NAV_MENU)

    def get_all_links(self) -> list:
        """모든 네비게이션 링크 반환"""
        elements = self.find_elements(self.locators.NAV_LINKS)
        return [
            {"text": el.text, "href": el.get_attribute("href")}
            for el in elements
            if el.get_attribute("href")
        ]

    def get_all_buttons(self) -> list:
        """모든 CTA 버튼 반환"""
        elements = self.find_elements(self.locators.CTA_BUTTONS)
        return [{"text": el.text, "visible": el.is_displayed()} for el in elements]

    def get_section_count(self) -> int:
        """섹션 개수 반환"""
        elements = self.find_elements(self.locators.SECTIONS)
        return len(elements)

    # --- 액션 메서드 ---

    def click_first_cta(self) -> None:
        """첫 번째 CTA 버튼 클릭"""
        self.click(self.locators.CTA_BUTTONS)

    def navigate_to_link(self, link_text: str) -> None:
        """특정 텍스트의 링크 클릭"""
        links = self.find_elements(self.locators.NAV_LINKS)
        for link in links:
            if link_text.lower() in link.text.lower():
                link.click()
                return
        raise ValueError(f"링크를 찾을 수 없음: {link_text}")
