"""모바일 UI 상세 테스트"""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os

from qa.qa_config import BASE_URL, DEVICE_PROFILES, SCREENSHOTS_DIR


class TestMobileUI:
    """모바일 UI 상세 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """테스트 셋업"""
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.results = []

    def capture_screenshot(self, name: str, device: str) -> str:
        """스크린샷 캡처"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{device}_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        self.driver.save_screenshot(str(filepath))
        return str(filepath)

    def analyze_viewport(self) -> dict:
        """뷰포트 분석"""
        return {
            "viewport_width": self.driver.execute_script("return window.innerWidth"),
            "viewport_height": self.driver.execute_script("return window.innerHeight"),
            "device_pixel_ratio": self.driver.execute_script("return window.devicePixelRatio"),
            "scroll_height": self.driver.execute_script("return document.body.scrollHeight"),
        }

    def analyze_touch_targets(self) -> dict:
        """터치 타겟 분석 (44px 이상 권장)"""
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        links = self.driver.find_elements(By.TAG_NAME, "a")

        small_targets = []
        for el in buttons + links:
            try:
                if el.is_displayed():
                    size = el.size
                    if size["width"] < 44 or size["height"] < 44:
                        text = el.text[:20] if el.text else "(no text)"
                        small_targets.append({
                            "element": el.tag_name,
                            "text": text,
                            "width": size["width"],
                            "height": size["height"]
                        })
            except:
                pass

        return {
            "total_buttons": len(buttons),
            "total_links": len(links),
            "small_targets": small_targets[:10],  # 상위 10개만
            "small_target_count": len(small_targets)
        }

    def analyze_font_sizes(self) -> dict:
        """폰트 크기 분석 (16px 이상 권장)"""
        texts = self.driver.find_elements(By.XPATH, "//p | //span | //div[text()] | //h1 | //h2 | //h3")

        small_fonts = []
        for el in texts[:50]:  # 상위 50개만 검사
            try:
                if el.is_displayed():
                    font_size = el.value_of_css_property("font-size")
                    size_px = float(font_size.replace("px", ""))
                    if size_px < 14:
                        text = el.text[:30] if el.text else ""
                        if text:
                            small_fonts.append({
                                "text": text,
                                "font_size": font_size
                            })
            except:
                pass

        return {
            "small_font_count": len(small_fonts),
            "small_fonts": small_fonts[:5]
        }

    def analyze_horizontal_scroll(self) -> dict:
        """가로 스크롤 분석"""
        viewport_width = self.driver.execute_script("return window.innerWidth")
        body_width = self.driver.execute_script("return document.body.scrollWidth")

        return {
            "viewport_width": viewport_width,
            "body_width": body_width,
            "has_horizontal_scroll": body_width > viewport_width,
            "overflow_px": max(0, body_width - viewport_width)
        }

    @pytest.mark.mobile
    @pytest.mark.parametrize("device_name", list(DEVICE_PROFILES.keys()))
    def test_mobile_ui_analysis(self, driver, device_name):
        """디바이스별 모바일 UI 분석"""
        device = DEVICE_PROFILES[device_name]

        # 화면 크기 설정
        driver.set_window_size(device["width"], device["height"])
        driver.get(BASE_URL)

        # 페이지 로드 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        print(f"\n{'='*60}")
        print(f"[디바이스] {device_name} ({device['width']}x{device['height']})")
        print(f"{'='*60}")

        # 1. 뷰포트 분석
        viewport = self.analyze_viewport()
        print(f"\n[뷰포트 정보]")
        print(f"  - 뷰포트: {viewport['viewport_width']}x{viewport['viewport_height']}")
        print(f"  - 픽셀 비율: {viewport['device_pixel_ratio']}")
        print(f"  - 스크롤 높이: {viewport['scroll_height']}px")

        # 2. 가로 스크롤 분석
        h_scroll = self.analyze_horizontal_scroll()
        print(f"\n[가로 스크롤]")
        if h_scroll["has_horizontal_scroll"]:
            print(f"  [WARN] 가로 스크롤 발생: {h_scroll['overflow_px']}px 초과")
        else:
            print(f"  [OK] 가로 스크롤 없음")

        # 3. 터치 타겟 분석
        touch = self.analyze_touch_targets()
        print(f"\n[터치 타겟]")
        print(f"  - 버튼 수: {touch['total_buttons']}")
        print(f"  - 링크 수: {touch['total_links']}")
        if touch["small_target_count"] > 0:
            print(f"  [WARN] 작은 터치 타겟: {touch['small_target_count']}개 (44px 미만)")
            for t in touch["small_targets"][:3]:
                print(f"    - {t['element']}: {t['width']}x{t['height']}px '{t['text']}'")
        else:
            print(f"  [OK] 모든 터치 타겟 적정 크기")

        # 4. 폰트 크기 분석
        fonts = self.analyze_font_sizes()
        print(f"\n[폰트 크기]")
        if fonts["small_font_count"] > 0:
            print(f"  [WARN] 작은 폰트: {fonts['small_font_count']}개 (14px 미만)")
            for f in fonts["small_fonts"][:3]:
                print(f"    - '{f['text'][:20]}...' ({f['font_size']})")
        else:
            print(f"  [OK] 모든 폰트 적정 크기")

        # 5. 스크린샷 저장
        screenshot_path = self.capture_screenshot("mobile_ui", device_name)
        print(f"\n[스크린샷] {screenshot_path}")

        # 6. 주요 UI 요소 확인
        print(f"\n[UI 요소 체크]")

        # 헤더
        headers = driver.find_elements(By.TAG_NAME, "header")
        print(f"  - header: {'[OK]' if headers else '[X]'}")

        # 네비게이션
        navs = driver.find_elements(By.TAG_NAME, "nav")
        print(f"  - nav: {'[OK]' if navs else '[X]'}")

        # 메인 컨텐츠
        mains = driver.find_elements(By.TAG_NAME, "main")
        print(f"  - main: {'[OK]' if mains else '[X]'}")

        # 푸터
        footers = driver.find_elements(By.TAG_NAME, "footer")
        print(f"  - footer: {'[OK]' if footers else '[X]'}")

        # 햄버거 메뉴 (모바일)
        hamburger = driver.find_elements(By.CSS_SELECTOR,
            ".hamburger, .menu-toggle, [class*='burger'], [class*='mobile-menu'], button[aria-label*='menu']")
        if device["width"] < 768:
            print(f"  - 햄버거 메뉴: {'[OK]' if hamburger else '[X] (모바일에서 필요)'}")

        print(f"\n{'='*60}")

        # 치명적 이슈 없으면 통과
        assert not h_scroll["has_horizontal_scroll"], f"가로 스크롤 발생: {h_scroll['overflow_px']}px"


class TestMobileInteraction:
    """모바일 인터랙션 테스트"""

    @pytest.mark.mobile
    def test_mobile_menu_toggle(self, driver):
        """모바일 메뉴 토글 테스트"""
        # 모바일 크기로 설정
        driver.set_window_size(375, 667)
        driver.get(BASE_URL)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 햄버거 메뉴 버튼 찾기
        menu_selectors = [
            ".hamburger",
            ".menu-toggle",
            "[class*='burger']",
            "[class*='mobile-menu']",
            "button[aria-label*='menu']",
            "[class*='nav-toggle']",
        ]

        menu_btn = None
        for selector in menu_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and elements[0].is_displayed():
                menu_btn = elements[0]
                break

        if menu_btn:
            print("[모바일 메뉴] 햄버거 메뉴 버튼 발견")

            # 메뉴 클릭
            menu_btn.click()
            print("[모바일 메뉴] 메뉴 버튼 클릭")

            # 메뉴 열림 확인
            import time
            time.sleep(0.5)

            # 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            driver.save_screenshot(f"qa/reports/screenshots/mobile_menu_open_{timestamp}.png")
            print("[스크린샷] 모바일 메뉴 열림 상태 저장")
        else:
            print("[모바일 메뉴] 햄버거 메뉴 버튼 없음 (다른 방식 사용 가능)")

    @pytest.mark.mobile
    def test_scroll_behavior(self, driver):
        """스크롤 동작 테스트"""
        driver.set_window_size(375, 667)
        driver.get(BASE_URL)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 페이지 스크롤
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")

        print(f"[스크롤] 전체 높이: {scroll_height}px, 뷰포트: {viewport_height}px")

        # 하단으로 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        import time
        time.sleep(0.5)

        # 스크롤 위치 확인
        scroll_pos = driver.execute_script("return window.pageYOffset")
        print(f"[스크롤] 현재 위치: {scroll_pos}px")

        # 스크린샷
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"qa/reports/screenshots/mobile_scroll_bottom_{timestamp}.png")

        # 상단으로 복귀
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(0.3)

        print("[스크롤] 테스트 완료")


class TestMobileAccessibility:
    """모바일 접근성 테스트"""

    @pytest.mark.mobile
    @pytest.mark.a11y
    def test_viewport_meta(self, driver):
        """뷰포트 메타 태그 확인"""
        driver.set_window_size(375, 667)
        driver.get(BASE_URL)

        viewport_meta = driver.find_elements(By.CSS_SELECTOR, "meta[name='viewport']")

        if viewport_meta:
            content = viewport_meta[0].get_attribute("content")
            print(f"[뷰포트 메타] {content}")

            # 권장 설정 확인
            checks = {
                "width=device-width": "width=device-width" in content,
                "initial-scale=1": "initial-scale=1" in content,
            }

            for check, passed in checks.items():
                status = "[OK]" if passed else "[WARN]"
                print(f"  {status} {check}")

            assert checks["width=device-width"], "viewport에 width=device-width 필요"
        else:
            print("[뷰포트 메타] [X] 뷰포트 메타 태그 없음")
            pytest.fail("뷰포트 메타 태그가 없습니다")

    @pytest.mark.mobile
    @pytest.mark.a11y
    def test_tap_highlight(self, driver):
        """탭 하이라이트 설정 확인"""
        driver.set_window_size(375, 667)
        driver.get(BASE_URL)

        # -webkit-tap-highlight-color 확인
        body = driver.find_element(By.TAG_NAME, "body")
        tap_color = body.value_of_css_property("-webkit-tap-highlight-color")

        print(f"[탭 하이라이트] {tap_color}")
