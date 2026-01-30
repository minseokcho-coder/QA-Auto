"""테스트 데이터 정의

기존 Article dataclass 패턴을 따릅니다.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TestUser:
    """테스트 사용자 정보"""

    email: str
    password: str
    name: Optional[str] = None
    phone: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "email": self.email,
            "password": self.password,
            "name": self.name,
            "phone": self.phone,
        }


@dataclass
class ExpectedElement:
    """예상 UI 요소 데이터"""

    name: str  # 요소 이름 (한글)
    selector: str  # CSS 셀렉터
    text: Optional[str] = None  # 예상 텍스트
    visible: bool = True  # 표시 여부
    clickable: bool = False  # 클릭 가능 여부


@dataclass
class PageInfo:
    """페이지 정보"""

    name: str  # 페이지 이름
    path: str  # URL 경로
    title_contains: Optional[str] = None  # 타이틀 포함 문자열
    required_elements: List[str] = field(default_factory=list)  # 필수 요소 셀렉터


# === 테스트 데이터 상수 ===

# 유효하지 않은 이메일 목록 (폼 검증 테스트용)
INVALID_EMAILS = [
    "invalid",
    "invalid@",
    "@example.com",
    "test@.com",
    "test@example",
    "",
    " ",
]

# 예상 페이지 목록
EXPECTED_PAGES = [
    PageInfo(name="홈", path="/", title_contains="SAVETAX"),
    PageInfo(name="FAQ", path="/faq", title_contains="FAQ"),
    PageInfo(name="이용약관", path="/terms", title_contains="약관"),
    PageInfo(name="개인정보처리방침", path="/privacy", title_contains="개인정보"),
]

# 디바이스 프로필 (반응형 테스트)
DEVICE_SIZES = {
    "mobile": (375, 667),
    "tablet": (768, 1024),
    "desktop": (1280, 800),
    "large": (1920, 1080),
}
