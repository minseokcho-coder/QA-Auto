"""시각적 회귀 테스트 모듈

1. Figma 디자인 이미지 다운로드
2. 실제 UI 스크린샷 캡처
3. 이미지 비교 (픽셀 diff)
4. 변경 리포트 생성
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import asyncio

try:
    from PIL import Image, ImageChops, ImageDraw
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class VisualDiff:
    """시각적 비교 결과"""
    screen_name: str
    baseline_path: str
    actual_path: str
    diff_path: str = ""
    diff_percentage: float = 0.0
    is_match: bool = True
    threshold: float = 0.1  # 허용 오차 (%)
    pixel_diff_count: int = 0
    total_pixels: int = 0
    error_message: str = ""


@dataclass
class VisualTestResult:
    """시각적 테스트 결과"""
    total: int = 0
    matched: int = 0
    mismatched: int = 0
    errors: int = 0
    diffs: List[VisualDiff] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    @property
    def match_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.matched / self.total) * 100


class VisualRegression:
    """시각적 회귀 테스트 클래스"""

    def __init__(
        self,
        baseline_dir: str = None,
        actual_dir: str = None,
        diff_dir: str = None,
        threshold: float = 0.1
    ):
        if not PIL_AVAILABLE:
            raise ImportError("Pillow가 필요합니다. `pip install Pillow numpy` 실행")

        base_path = Path(__file__).parent.parent / "reports" / "visual"

        self.baseline_dir = Path(baseline_dir) if baseline_dir else base_path / "baseline"
        self.actual_dir = Path(actual_dir) if actual_dir else base_path / "actual"
        self.diff_dir = Path(diff_dir) if diff_dir else base_path / "diff"
        self.threshold = threshold

        # 디렉토리 생성
        for d in [self.baseline_dir, self.actual_dir, self.diff_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def compare_images(self, baseline_path: Path, actual_path: Path, screen_name: str) -> VisualDiff:
        """두 이미지 비교"""
        diff = VisualDiff(
            screen_name=screen_name,
            baseline_path=str(baseline_path),
            actual_path=str(actual_path),
            threshold=self.threshold
        )

        try:
            # 이미지 로드
            baseline = Image.open(baseline_path).convert("RGB")
            actual = Image.open(actual_path).convert("RGB")

            # 크기 맞추기
            if baseline.size != actual.size:
                actual = actual.resize(baseline.size, Image.Resampling.LANCZOS)

            # 픽셀 차이 계산
            diff_image = ImageChops.difference(baseline, actual)

            # numpy로 변환하여 차이 계산
            diff_array = np.array(diff_image)
            diff.total_pixels = diff_array.shape[0] * diff_array.shape[1]

            # 차이가 있는 픽셀 카운트 (RGB 합이 threshold 이상인 경우)
            threshold_value = 30  # RGB 차이 threshold
            diff_mask = np.sum(diff_array, axis=2) > threshold_value
            diff.pixel_diff_count = np.sum(diff_mask)

            diff.diff_percentage = (diff.pixel_diff_count / diff.total_pixels) * 100
            diff.is_match = diff.diff_percentage <= self.threshold

            # Diff 이미지 생성 (차이 부분 빨간색 하이라이트)
            diff_path = self.diff_dir / f"{screen_name}_diff.png"
            self._create_diff_image(baseline, actual, diff_mask, diff_path)
            diff.diff_path = str(diff_path)

        except Exception as e:
            diff.is_match = False
            diff.error_message = str(e)

        return diff

    def _create_diff_image(self, baseline: Image, actual: Image, diff_mask: np.ndarray, save_path: Path):
        """차이 하이라이트 이미지 생성"""
        # 실제 이미지 복사
        diff_image = actual.copy()
        diff_array = np.array(diff_image)

        # 차이 부분 빨간색으로 하이라이트
        diff_array[diff_mask] = [255, 0, 0]  # Red

        result = Image.fromarray(diff_array)
        result.save(save_path)

    async def capture_screenshots(
        self,
        urls: List[Dict],
        base_url: str,
        viewport: Dict = None
    ) -> List[Path]:
        """Playwright로 스크린샷 캡처"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("playwright가 필요합니다.")

        viewport = viewport or {"width": 375, "height": 667}
        captured = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport=viewport, locale="ko-KR")

            for item in urls:
                name = item.get("name", "unknown")
                path = item.get("path", "/")
                url = f"{base_url.rstrip('/')}{path}"

                try:
                    page = await context.new_page()
                    await page.goto(url, wait_until="networkidle")

                    # 추가 대기 (동적 콘텐츠)
                    await page.wait_for_timeout(1000)

                    screenshot_path = self.actual_dir / f"{name}.png"
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                    captured.append(screenshot_path)

                    await page.close()
                except Exception as e:
                    print(f"스크린샷 캡처 실패 ({name}): {e}")

            await browser.close()

        return captured

    def run_comparison(self, screen_names: List[str] = None) -> VisualTestResult:
        """시각적 비교 실행"""
        result = VisualTestResult(started_at=datetime.now().isoformat())

        # 비교할 파일 목록
        if screen_names:
            baseline_files = [self.baseline_dir / f"{name}.png" for name in screen_names]
        else:
            baseline_files = list(self.baseline_dir.glob("*.png"))

        result.total = len(baseline_files)

        for baseline_path in baseline_files:
            screen_name = baseline_path.stem
            actual_path = self.actual_dir / f"{screen_name}.png"

            if not actual_path.exists():
                diff = VisualDiff(
                    screen_name=screen_name,
                    baseline_path=str(baseline_path),
                    actual_path="",
                    is_match=False,
                    error_message="실제 스크린샷 없음"
                )
                result.errors += 1
            else:
                diff = self.compare_images(baseline_path, actual_path, screen_name)

                if diff.is_match:
                    result.matched += 1
                else:
                    result.mismatched += 1

            result.diffs.append(diff)

        result.completed_at = datetime.now().isoformat()
        return result

    def update_baseline(self, screen_name: str = None):
        """베이스라인 업데이트 (actual -> baseline)"""
        if screen_name:
            actual_path = self.actual_dir / f"{screen_name}.png"
            baseline_path = self.baseline_dir / f"{screen_name}.png"

            if actual_path.exists():
                import shutil
                shutil.copy(actual_path, baseline_path)
                print(f"베이스라인 업데이트: {screen_name}")
        else:
            # 전체 업데이트
            import shutil
            for actual_path in self.actual_dir.glob("*.png"):
                baseline_path = self.baseline_dir / actual_path.name
                shutil.copy(actual_path, baseline_path)
            print(f"전체 베이스라인 업데이트 완료")


class FigmaVisualComparison(VisualRegression):
    """Figma 디자인과 실제 UI 비교"""

    def __init__(self, figma_integration, **kwargs):
        super().__init__(**kwargs)
        self.figma = figma_integration

    async def download_figma_screens(self, file_key: str, node_ids: List[str]) -> List[Path]:
        """Figma 화면 이미지 다운로드"""
        downloaded = []

        try:
            # 이미지 URL 조회
            images_data = self.figma.get_image(file_key, node_ids)
            images = images_data.get("images", {})

            for node_id, url in images.items():
                if url:
                    # 노드 정보 조회하여 이름 가져오기
                    safe_name = node_id.replace(":", "-")
                    save_path = self.baseline_dir / f"figma_{safe_name}.png"
                    self.figma.download_image(url, save_path)
                    downloaded.append(save_path)
                    print(f"Figma 이미지 다운로드: {save_path}")

        except Exception as e:
            print(f"Figma 이미지 다운로드 실패: {e}")

        return downloaded

    async def compare_with_figma(
        self,
        file_key: str,
        screens: List[Dict],
        base_url: str
    ) -> VisualTestResult:
        """Figma 디자인과 실제 UI 비교"""
        # 1. Figma 이미지 다운로드
        node_ids = [s.get("figma_node_id") for s in screens if s.get("figma_node_id")]
        if node_ids:
            await self.download_figma_screens(file_key, node_ids)

        # 2. 실제 UI 스크린샷 캡처
        urls = [{"name": s.get("name"), "path": s.get("path", "/")} for s in screens]
        await self.capture_screenshots(urls, base_url)

        # 3. 비교 실행
        return self.run_comparison()


# CLI 실행
if __name__ == "__main__":
    # 기본 시각적 회귀 테스트
    vr = VisualRegression()

    # 베이스라인이 있는 경우 비교 실행
    result = vr.run_comparison()

    print(f"시각적 테스트 결과: {result.matched}/{result.total} 일치 ({result.match_rate:.1f}%)")

    for diff in result.diffs:
        status = "✓" if diff.is_match else "✗"
        print(f"  {status} {diff.screen_name}: {diff.diff_percentage:.2f}% 차이")
