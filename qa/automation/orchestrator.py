"""QA 자동화 오케스트레이터

전체 QA 파이프라인을 자동으로 실행:
1. Figma 변경 감지
2. TC 자동 생성/업데이트
3. E2E 테스트 실행
4. 시각적 회귀 테스트
5. 리포트 생성 및 전송
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from qa.automation.figma_integration import FigmaIntegration, FigmaFlow
from qa.automation.test_runner import TestRunner, TestSuiteResult
from qa.automation.visual_regression import VisualRegression, VisualTestResult
from qa.automation.reporter import Reporter, QAReport


@dataclass
class QAConfig:
    """QA 설정"""
    # Figma
    figma_file_key: str = "rcxhAYTksM5DmkrjqTuvHc"
    figma_node_id: str = "9987-46608"
    figma_token: str = ""

    # 테스트
    base_url: str = "https://qa.hiddenmoney.co.kr"
    headless: bool = True
    use_playwright: bool = True

    # 리포트
    slack_webhook: str = ""
    report_title: str = "세이브택스 QA"

    # 실행 옵션
    run_e2e: bool = True
    run_visual: bool = True
    check_figma: bool = True
    generate_tc: bool = False

    @classmethod
    def from_env(cls):
        """환경변수에서 설정 로드"""
        return cls(
            figma_file_key=os.getenv("FIGMA_FILE_KEY", "rcxhAYTksM5DmkrjqTuvHc"),
            figma_node_id=os.getenv("FIGMA_NODE_ID", "9987-46608"),
            figma_token=os.getenv("FIGMA_ACCESS_TOKEN", ""),
            base_url=os.getenv("QA_BASE_URL", "https://qa.hiddenmoney.co.kr"),
            headless=os.getenv("QA_HEADLESS", "true").lower() == "true",
            slack_webhook=os.getenv("SLACK_WEBHOOK_URL", ""),
        )


class QAOrchestrator:
    """QA 자동화 오케스트레이터"""

    def __init__(self, config: QAConfig = None):
        self.config = config or QAConfig.from_env()
        self.figma: Optional[FigmaIntegration] = None
        self.runner: Optional[TestRunner] = None
        self.visual: Optional[VisualRegression] = None
        self.reporter: Optional[Reporter] = None

        self._init_components()

    def _init_components(self):
        """컴포넌트 초기화"""
        # Figma 연동
        if self.config.figma_token:
            try:
                self.figma = FigmaIntegration(self.config.figma_token)
            except Exception as e:
                print(f"Figma 연동 초기화 실패: {e}")

        # 테스트 러너
        self.runner = TestRunner(
            base_url=self.config.base_url,
            use_playwright=self.config.use_playwright,
            headless=self.config.headless
        )

        # 시각적 회귀 테스트
        try:
            self.visual = VisualRegression()
        except ImportError as e:
            print(f"Visual Regression 초기화 실패: {e}")

        # 리포터
        self.reporter = Reporter(
            slack_webhook=self.config.slack_webhook
        )

    async def run_full_pipeline(self) -> QAReport:
        """전체 QA 파이프라인 실행"""
        print("=" * 60)
        print("🚀 QA 자동화 파이프라인 시작")
        print("=" * 60)
        print(f"환경: {self.config.base_url}")
        print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        figma_changes = None
        flow = None
        test_cases = []
        test_result = None
        visual_result = None

        # 1. Figma 변경 감지
        if self.config.check_figma and self.figma:
            print("📐 Step 1: Figma 디자인 변경 감지...")
            try:
                figma_changes = self.figma.detect_changes(
                    self.config.figma_file_key,
                    self.config.figma_node_id
                )
                if figma_changes["has_changes"]:
                    print(f"   ⚠️ 디자인 변경 감지됨!")
                    print(f"   - 새 화면: {figma_changes['new_screens']}")
                    print(f"   - 수정된 화면: {figma_changes['modified_screens']}")
                    print(f"   - 삭제된 화면: {figma_changes['removed_screens']}")
                else:
                    print("   ✓ 변경 없음")
            except Exception as e:
                print(f"   ✗ Figma 체크 실패: {e}")
            print()

        # 2. TC 자동 생성 (옵션)
        if self.config.generate_tc and self.figma:
            print("📝 Step 2: TC 자동 생성...")
            try:
                flow = self.figma.extract_flow(
                    self.config.figma_file_key,
                    self.config.figma_node_id
                )
                test_cases = self.figma.generate_tc_from_flow(flow)
                print(f"   ✓ {len(test_cases)}개 TC 생성됨")
            except Exception as e:
                print(f"   ✗ TC 생성 실패: {e}")
            print()

        # 3. E2E 테스트 실행
        if self.config.run_e2e:
            print("🧪 Step 3: E2E 테스트 실행...")
            try:
                if test_cases:
                    test_result = await self.runner.run_tests(test_cases)
                else:
                    test_result = self.runner.run_tests_sync()

                print(f"   ✓ 테스트 완료: {test_result.passed}/{test_result.total} 통과 ({test_result.pass_rate:.1f}%)")
                if test_result.failed > 0:
                    print(f"   ⚠️ 실패: {test_result.failed}개")
            except Exception as e:
                print(f"   ✗ 테스트 실패: {e}")
                # 더미 결과 생성
                test_result = TestSuiteResult(
                    suite_name="E2E",
                    errors=1
                )
            print()

        # 4. 시각적 회귀 테스트
        if self.config.run_visual and self.visual:
            print("👁️ Step 4: 시각적 회귀 테스트...")
            try:
                visual_result = self.visual.run_comparison()
                print(f"   ✓ 비교 완료: {visual_result.matched}/{visual_result.total} 일치 ({visual_result.match_rate:.1f}%)")
                if visual_result.mismatched > 0:
                    print(f"   ⚠️ 불일치: {visual_result.mismatched}개")
            except Exception as e:
                print(f"   ✗ 시각적 테스트 실패: {e}")
            print()

        # 5. 리포트 생성
        print("📊 Step 5: 리포트 생성...")
        if test_result is None:
            test_result = TestSuiteResult(suite_name="Empty", total=0)

        report = self.reporter.generate_report(
            title=self.config.report_title,
            environment=self.config.base_url,
            test_result=test_result,
            visual_result=visual_result,
            figma_changes=figma_changes
        )

        # 엑셀 리포트
        excel_path = self.reporter.generate_excel(report)
        if excel_path:
            print(f"   ✓ 엑셀 리포트: {excel_path}")

        # Slack 전송
        if self.config.slack_webhook:
            slack_sent = self.reporter.send_slack(report)
            if slack_sent:
                print("   ✓ Slack 알림 전송됨")
            else:
                print("   ✗ Slack 전송 실패")
        print()

        # 결과 요약
        print("=" * 60)
        print("📋 QA 자동화 파이프라인 완료")
        print("=" * 60)
        print(f"총 TC: {report.total_tc}")
        print(f"통과율: {report.pass_rate:.1f}%")
        if report.visual_match_rate > 0:
            print(f"시각적 일치율: {report.visual_match_rate:.1f}%")
        print("=" * 60)

        return report

    def run(self) -> QAReport:
        """동기 실행"""
        return asyncio.run(self.run_full_pipeline())


def main():
    """CLI 엔트리포인트"""
    parser = argparse.ArgumentParser(description="QA 자동화 시스템")
    parser.add_argument("--url", default=None, help="테스트 대상 URL")
    parser.add_argument("--headless", action="store_true", help="헤드리스 모드")
    parser.add_argument("--no-headless", action="store_true", help="브라우저 표시")
    parser.add_argument("--skip-figma", action="store_true", help="Figma 체크 스킵")
    parser.add_argument("--skip-visual", action="store_true", help="시각적 테스트 스킵")
    parser.add_argument("--skip-e2e", action="store_true", help="E2E 테스트 스킵")
    parser.add_argument("--generate-tc", action="store_true", help="TC 자동 생성")
    parser.add_argument("--slack", action="store_true", help="Slack 알림 전송")

    args = parser.parse_args()

    # 설정
    config = QAConfig.from_env()

    if args.url:
        config.base_url = args.url
    if args.no_headless:
        config.headless = False
    if args.headless:
        config.headless = True
    if args.skip_figma:
        config.check_figma = False
    if args.skip_visual:
        config.run_visual = False
    if args.skip_e2e:
        config.run_e2e = False
    if args.generate_tc:
        config.generate_tc = True

    # 실행
    orchestrator = QAOrchestrator(config)
    report = orchestrator.run()

    # 종료 코드
    if report.pass_rate < 80:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
