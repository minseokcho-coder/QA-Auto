"""E2E 테스트 자동 실행 모듈

TC 기반으로:
1. Playwright 테스트 코드 생성
2. 테스트 실행
3. 결과 수집
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class TestResult:
    """테스트 결과"""
    tc_no: int
    title: str
    status: str  # PASS, FAIL, SKIP, ERROR
    duration_ms: float = 0
    error_message: str = ""
    screenshot_path: str = ""
    actual_result: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestSuiteResult:
    """테스트 스위트 결과"""
    suite_name: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_ms: float = 0
    results: List[TestResult] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    @property
    def pass_rate(self) -> float:
        """통과율"""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100


class PlaywrightTestRunner:
    """Playwright 기반 E2E 테스트 러너"""

    def __init__(self, base_url: str, headless: bool = True):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("playwright가 설치되지 않았습니다. `pip install playwright && playwright install` 실행")

        self.base_url = base_url
        self.headless = headless
        self.screenshots_dir = Path(__file__).parent.parent / "reports" / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def run_test_cases(self, test_cases: List[Dict], timeout_ms: int = 30000) -> TestSuiteResult:
        """TC 목록 실행"""
        suite_result = TestSuiteResult(
            suite_name="E2E Test Suite",
            total=len(test_cases),
            started_at=datetime.now().isoformat()
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 375, "height": 667},  # 모바일 뷰포트
                locale="ko-KR"
            )

            for tc in test_cases:
                result = await self._run_single_test(context, tc, timeout_ms)
                suite_result.results.append(result)

                # 통계 업데이트
                if result.status == "PASS":
                    suite_result.passed += 1
                elif result.status == "FAIL":
                    suite_result.failed += 1
                elif result.status == "SKIP":
                    suite_result.skipped += 1
                else:
                    suite_result.errors += 1

                suite_result.duration_ms += result.duration_ms

            await browser.close()

        suite_result.completed_at = datetime.now().isoformat()
        return suite_result

    async def _run_single_test(self, context, tc: Dict, timeout_ms: int) -> TestResult:
        """단일 TC 실행"""
        tc_no = tc.get("No", 0)
        title = tc.get("title", "Unknown")
        start_time = datetime.now()

        result = TestResult(
            tc_no=tc_no,
            title=title,
            status="SKIP"
        )

        try:
            page = await context.new_page()
            page.set_default_timeout(timeout_ms)

            # TC 타입에 따른 테스트 실행
            if "화면 정상 로드" in title or "화면 확인" in title:
                result = await self._test_page_load(page, tc, result)
            elif "버튼" in title:
                result = await self._test_button(page, tc, result)
            elif "입력" in title:
                result = await self._test_input(page, tc, result)
            else:
                # 기본: 페이지 로드 테스트
                result = await self._test_page_load(page, tc, result)

            # 스크린샷 저장
            screenshot_path = self.screenshots_dir / f"tc_{tc_no}_{result.status.lower()}.png"
            await page.screenshot(path=str(screenshot_path))
            result.screenshot_path = str(screenshot_path)

            await page.close()

        except Exception as e:
            result.status = "ERROR"
            result.error_message = str(e)

        result.duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        return result

    async def _test_page_load(self, page: Page, tc: Dict, result: TestResult) -> TestResult:
        """페이지 로드 테스트"""
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")

            # 페이지 타이틀 확인
            title = await page.title()
            result.actual_result = f"페이지 로드 완료. 타이틀: {title}"
            result.status = "PASS"

        except Exception as e:
            result.status = "FAIL"
            result.error_message = str(e)

        return result

    async def _test_button(self, page: Page, tc: Dict, result: TestResult) -> TestResult:
        """버튼 테스트"""
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")

            # 버튼 텍스트 추출 (TC 제목에서)
            title = tc.get("title", "")
            # '[화면명] '버튼명' 버튼 동작 확인' 형식에서 버튼명 추출
            if "'" in title:
                button_text = title.split("'")[1]
            else:
                button_text = "button"

            # 버튼 찾기
            button = page.locator(f"button:has-text('{button_text}'), [role='button']:has-text('{button_text}')")

            if await button.count() > 0:
                result.actual_result = f"'{button_text}' 버튼 발견"
                result.status = "PASS"
            else:
                result.actual_result = f"'{button_text}' 버튼을 찾을 수 없음"
                result.status = "FAIL"

        except Exception as e:
            result.status = "FAIL"
            result.error_message = str(e)

        return result

    async def _test_input(self, page: Page, tc: Dict, result: TestResult) -> TestResult:
        """입력 필드 테스트"""
        try:
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")

            # 입력 필드 찾기
            inputs = page.locator("input, textarea")
            count = await inputs.count()

            if count > 0:
                result.actual_result = f"입력 필드 {count}개 발견"
                result.status = "PASS"
            else:
                result.actual_result = "입력 필드를 찾을 수 없음"
                result.status = "FAIL"

        except Exception as e:
            result.status = "FAIL"
            result.error_message = str(e)

        return result


class SeleniumTestRunner:
    """Selenium 기반 테스트 러너 (기존 인프라 활용)"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.reports_dir = Path(__file__).parent.parent / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_pytest(self, test_path: str = None, markers: str = None) -> TestSuiteResult:
        """pytest 실행"""
        qa_dir = Path(__file__).parent.parent

        cmd = [
            "python", "-m", "pytest",
            str(qa_dir / "tests") if not test_path else test_path,
            "-v",
            "--tb=short",
            f"--html={self.reports_dir / 'report.html'}",
            "--self-contained-html",
            f"--json-report",
            f"--json-report-file={self.reports_dir / 'report.json'}"
        ]

        if markers:
            cmd.extend(["-m", markers])

        start_time = datetime.now()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(qa_dir.parent),
                timeout=600  # 10분 타임아웃
            )
        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                suite_name="pytest",
                errors=1,
                started_at=start_time.isoformat(),
                completed_at=datetime.now().isoformat()
            )

        # JSON 리포트 파싱
        suite_result = self._parse_json_report()
        suite_result.started_at = start_time.isoformat()
        suite_result.completed_at = datetime.now().isoformat()

        return suite_result

    def _parse_json_report(self) -> TestSuiteResult:
        """pytest JSON 리포트 파싱"""
        report_file = self.reports_dir / "report.json"

        suite_result = TestSuiteResult(suite_name="pytest")

        if not report_file.exists():
            return suite_result

        try:
            data = json.loads(report_file.read_text(encoding="utf-8"))
            summary = data.get("summary", {})

            suite_result.total = summary.get("total", 0)
            suite_result.passed = summary.get("passed", 0)
            suite_result.failed = summary.get("failed", 0)
            suite_result.skipped = summary.get("skipped", 0)
            suite_result.errors = summary.get("error", 0)
            suite_result.duration_ms = data.get("duration", 0) * 1000

            # 개별 테스트 결과
            for test in data.get("tests", []):
                result = TestResult(
                    tc_no=0,
                    title=test.get("nodeid", ""),
                    status=test.get("outcome", "unknown").upper(),
                    duration_ms=test.get("duration", 0) * 1000,
                    error_message=test.get("call", {}).get("longrepr", "")
                )
                suite_result.results.append(result)

        except Exception as e:
            print(f"리포트 파싱 오류: {e}")

        return suite_result


class TestRunner:
    """통합 테스트 러너"""

    def __init__(self, base_url: str, use_playwright: bool = True, headless: bool = True):
        self.base_url = base_url
        self.headless = headless

        if use_playwright and PLAYWRIGHT_AVAILABLE:
            self.runner = PlaywrightTestRunner(base_url, headless)
            self.runner_type = "playwright"
        else:
            self.runner = SeleniumTestRunner(base_url)
            self.runner_type = "selenium"

    async def run_tests(self, test_cases: List[Dict] = None) -> TestSuiteResult:
        """테스트 실행"""
        if self.runner_type == "playwright" and test_cases:
            return await self.runner.run_test_cases(test_cases)
        else:
            return self.runner.run_pytest()

    def run_tests_sync(self, test_cases: List[Dict] = None) -> TestSuiteResult:
        """동기 테스트 실행"""
        return asyncio.run(self.run_tests(test_cases))


# CLI 실행
if __name__ == "__main__":
    import sys

    base_url = os.getenv("QA_BASE_URL", "https://qa.hiddenmoney.co.kr")

    # Selenium 테스트 실행
    runner = SeleniumTestRunner(base_url)
    result = runner.run_pytest()

    print(f"테스트 결과: {result.passed}/{result.total} 통과 ({result.pass_rate:.1f}%)")
    print(f"실패: {result.failed}, 에러: {result.errors}, 스킵: {result.skipped}")
