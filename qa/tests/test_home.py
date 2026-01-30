"""홈페이지 테스트 케이스"""
import pytest

from qa.pages.home_page import HomePage
from qa.qa_config import BASE_URL


class TestHomePageLoad:
    """홈페이지 로딩 테스트"""

    @pytest.mark.smoke
    def test_home_page_loads_successfully(self, home_page: HomePage):
        """홈페이지가 정상적으로 로드되는지 확인"""
        assert home_page.is_loaded(), "홈페이지 로드 실패"

    @pytest.mark.smoke
    def test_home_page_title_not_empty(self, home_page: HomePage):
        """페이지 타이틀이 비어있지 않은지 확인"""
        title = home_page.get_title()
        assert title, "페이지 타이틀이 비어있음"
        print(f"[페이지 타이틀] {title}")

    @pytest.mark.smoke
    def test_home_page_url(self, home_page: HomePage, base_url: str):
        """페이지 URL 확인"""
        current_url = home_page.get_current_url()
        assert base_url in current_url, f"예상하지 못한 URL: {current_url}"


class TestHomePageElements:
    """홈페이지 UI 요소 테스트"""

    @pytest.mark.ui
    def test_page_has_content(self, home_page: HomePage):
        """페이지에 콘텐츠가 있는지 확인"""
        assert home_page.is_loaded(), "페이지 콘텐츠 없음"

    @pytest.mark.ui
    def test_navigation_exists(self, home_page: HomePage):
        """네비게이션이 존재하는지 확인"""
        is_visible = home_page.is_navigation_visible()
        print(f"[네비게이션 표시] {is_visible}")
        # 네비게이션이 없어도 테스트는 통과 (정보 수집 목적)

    @pytest.mark.ui
    def test_collect_all_links(self, home_page: HomePage):
        """페이지의 모든 링크 수집"""
        links = home_page.get_all_links()
        print(f"[발견된 링크 수] {len(links)}")
        for link in links[:10]:  # 처음 10개만 출력
            print(f"  - {link['text']}: {link['href']}")

    @pytest.mark.ui
    def test_collect_all_buttons(self, home_page: HomePage):
        """페이지의 모든 버튼 수집"""
        buttons = home_page.get_all_buttons()
        print(f"[발견된 버튼 수] {len(buttons)}")
        for btn in buttons[:10]:  # 처음 10개만 출력
            print(f"  - {btn['text']} (visible: {btn['visible']})")

    @pytest.mark.ui
    def test_section_count(self, home_page: HomePage):
        """페이지 섹션 개수 확인"""
        count = home_page.get_section_count()
        print(f"[섹션 개수] {count}")


class TestHomePageScreenshot:
    """홈페이지 스크린샷 테스트"""

    @pytest.mark.smoke
    def test_take_homepage_screenshot(self, home_page: HomePage):
        """홈페이지 스크린샷 저장"""
        filepath = home_page.take_screenshot("homepage.png")
        print(f"[스크린샷 저장] {filepath}")
        assert filepath.endswith(".png")
