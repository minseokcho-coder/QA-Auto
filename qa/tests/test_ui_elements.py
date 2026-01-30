"""UI 요소 테스트 케이스"""
import pytest
from selenium.webdriver.common.by import By

from qa.pages.home_page import HomePage
from qa.core.base_page import Locator
from qa.qa_config import BASE_URL, DEVICE_PROFILES


class TestResponsiveDesign:
    """반응형 디자인 테스트"""

    @pytest.mark.responsive
    def test_responsive_layout(self, responsive_driver, base_url):
        """다양한 화면 크기에서 레이아웃 확인"""
        driver, device = responsive_driver
        driver.get(base_url)

        # 현재 화면 크기
        size = driver.get_window_size()
        print(f"[디바이스] {device} - {size['width']}x{size['height']}")

        # 페이지 로드 확인
        body = driver.find_element(By.TAG_NAME, "body")
        assert body.is_displayed(), f"{device}에서 페이지 로드 실패"

        # 스크린샷 저장
        driver.save_screenshot(f"qa/reports/screenshots/responsive_{device}.png")
        print(f"[스크린샷] responsive_{device}.png 저장됨")


class TestPageStructure:
    """페이지 구조 테스트"""

    @pytest.mark.ui
    def test_html_structure(self, driver, base_url):
        """HTML 기본 구조 확인"""
        driver.get(base_url)

        # 기본 태그 존재 확인
        elements = {
            "html": driver.find_elements(By.TAG_NAME, "html"),
            "head": driver.find_elements(By.TAG_NAME, "head"),
            "body": driver.find_elements(By.TAG_NAME, "body"),
            "header": driver.find_elements(By.TAG_NAME, "header"),
            "main": driver.find_elements(By.TAG_NAME, "main"),
            "footer": driver.find_elements(By.TAG_NAME, "footer"),
        }

        print("[HTML 구조 분석]")
        for tag, els in elements.items():
            count = len(els)
            status = "O" if count > 0 else "X"
            print(f"  {status} <{tag}>: {count}개")

    @pytest.mark.ui
    def test_meta_tags(self, driver, base_url):
        """메타 태그 확인"""
        driver.get(base_url)

        meta_tags = driver.find_elements(By.TAG_NAME, "meta")
        print(f"[메타 태그 수] {len(meta_tags)}")

        # 주요 메타 태그 확인
        for meta in meta_tags:
            name = meta.get_attribute("name")
            content = meta.get_attribute("content")
            if name and content:
                print(f"  - {name}: {content[:50]}...")

    @pytest.mark.ui
    def test_images_have_alt(self, driver, base_url):
        """이미지 alt 속성 확인 (접근성)"""
        driver.get(base_url)

        images = driver.find_elements(By.TAG_NAME, "img")
        print(f"[이미지 수] {len(images)}")

        missing_alt = 0
        for img in images:
            alt = img.get_attribute("alt")
            if not alt:
                src = img.get_attribute("src")
                print(f"  [경고] alt 없음: {src[:50] if src else 'unknown'}...")
                missing_alt += 1

        print(f"[alt 누락] {missing_alt}/{len(images)}")


class TestInteractiveElements:
    """인터랙티브 요소 테스트"""

    @pytest.mark.ui
    def test_buttons_are_clickable(self, driver, base_url):
        """버튼 클릭 가능 여부 확인"""
        driver.get(base_url)

        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"[버튼 수] {len(buttons)}")

        clickable_count = 0
        for btn in buttons:
            if btn.is_displayed() and btn.is_enabled():
                clickable_count += 1
                print(f"  - 클릭 가능: {btn.text[:30] if btn.text else '(텍스트 없음)'}")

        print(f"[클릭 가능 버튼] {clickable_count}/{len(buttons)}")

    @pytest.mark.ui
    def test_links_have_href(self, driver, base_url):
        """링크 href 속성 확인"""
        driver.get(base_url)

        links = driver.find_elements(By.TAG_NAME, "a")
        print(f"[링크 수] {len(links)}")

        missing_href = 0
        for link in links:
            href = link.get_attribute("href")
            if not href or href == "#":
                text = link.text[:30] if link.text else "(텍스트 없음)"
                print(f"  [경고] href 없음/무효: {text}")
                missing_href += 1

        print(f"[href 누락/무효] {missing_href}/{len(links)}")

    @pytest.mark.ui
    def test_form_elements(self, driver, base_url):
        """폼 요소 확인"""
        driver.get(base_url)

        forms = driver.find_elements(By.TAG_NAME, "form")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        selects = driver.find_elements(By.TAG_NAME, "select")

        print("[폼 요소 분석]")
        print(f"  - form: {len(forms)}개")
        print(f"  - input: {len(inputs)}개")
        print(f"  - textarea: {len(textareas)}개")
        print(f"  - select: {len(selects)}개")

        # input 타입별 분류
        if inputs:
            types = {}
            for inp in inputs:
                t = inp.get_attribute("type") or "text"
                types[t] = types.get(t, 0) + 1
            print("  [input 타입]")
            for t, count in types.items():
                print(f"    - {t}: {count}개")
