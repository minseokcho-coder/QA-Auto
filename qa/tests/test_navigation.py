"""네비게이션 테스트 케이스"""
import pytest

from qa.pages.home_page import HomePage
from qa.pages.components.header import Header
from qa.pages.components.footer import Footer
from qa.qa_config import BASE_URL


class TestHeaderNavigation:
    """헤더 네비게이션 테스트"""

    @pytest.mark.navigation
    def test_header_visible(self, driver, base_url):
        """헤더가 표시되는지 확인"""
        driver.get(base_url)
        header = Header(driver)
        is_visible = header.is_visible()
        print(f"[헤더 표시] {is_visible}")

    @pytest.mark.navigation
    def test_header_logo_visible(self, driver, base_url):
        """헤더 로고가 표시되는지 확인"""
        driver.get(base_url)
        header = Header(driver)
        is_visible = header.is_logo_visible()
        print(f"[로고 표시] {is_visible}")

    @pytest.mark.navigation
    def test_collect_nav_links(self, driver, base_url):
        """네비게이션 링크 수집"""
        driver.get(base_url)
        header = Header(driver)
        links = header.get_nav_links()
        print(f"[네비게이션 링크 수] {len(links)}")
        for link in links:
            print(f"  - {link['text']}: {link['href']}")


class TestFooterNavigation:
    """푸터 네비게이션 테스트"""

    @pytest.mark.navigation
    def test_footer_visible(self, driver, base_url):
        """푸터가 표시되는지 확인"""
        driver.get(base_url)
        footer = Footer(driver)
        footer.scroll_to_footer()
        is_visible = footer.is_visible()
        print(f"[푸터 표시] {is_visible}")

    @pytest.mark.navigation
    def test_footer_links(self, driver, base_url):
        """푸터 링크 수집"""
        driver.get(base_url)
        footer = Footer(driver)
        links = footer.get_all_links()
        print(f"[푸터 링크 수] {len(links)}")
        for link in links[:5]:
            print(f"  - {link['text']}: {link['href']}")

    @pytest.mark.navigation
    def test_footer_copyright(self, driver, base_url):
        """푸터 저작권 텍스트 확인"""
        driver.get(base_url)
        footer = Footer(driver)
        copyright_text = footer.get_copyright_text()
        print(f"[저작권] {copyright_text}")


class TestPageNavigation:
    """페이지 간 이동 테스트"""

    @pytest.mark.navigation
    def test_navigate_and_return(self, home_page: HomePage, base_url: str):
        """다른 페이지로 이동 후 홈으로 복귀"""
        # 현재 URL 저장
        original_url = home_page.get_current_url()
        print(f"[시작 URL] {original_url}")

        # 링크 수집
        links = home_page.get_all_links()
        if links:
            # 첫 번째 링크 정보 출력
            first_link = links[0]
            print(f"[첫 번째 링크] {first_link['text']}: {first_link['href']}")

        # 홈으로 복귀
        home_page.open(base_url)
        final_url = home_page.get_current_url()
        print(f"[최종 URL] {final_url}")
        assert base_url in final_url
