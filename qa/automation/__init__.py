"""QA 자동화 시스템 패키지

Full Auto QA System:
1. Figma 연동 - 디자인 변경 감지 및 TC 자동 생성
2. E2E 테스트 - Playwright 기반 플로우 테스트
3. Visual Regression - 스크린샷 비교 테스트
4. API 테스트 - 엔드포인트 검증
5. 성능 테스트 - Lighthouse 점수 측정
6. AI 분석 - 테스트 결과 분석 및 개선 제안
7. 리포팅 - Slack + 엑셀 자동 리포트
"""

__version__ = "1.0.0"
__all__ = [
    "FigmaIntegration",
    "TestRunner",
    "VisualRegression",
    "Reporter",
    "QAOrchestrator",
]
