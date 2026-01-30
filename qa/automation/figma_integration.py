"""Figma 연동 모듈

Figma API를 통해:
1. 디자인 변경 감지
2. 플로우/화면 정보 추출
3. TC 자동 생성/업데이트
"""

import os
import json
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class FigmaScreen:
    """Figma 화면 정보"""
    id: str
    name: str
    type: str
    visible: bool = True
    children: List[Dict] = field(default_factory=list)
    texts: List[str] = field(default_factory=list)
    buttons: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)


@dataclass
class FigmaFlow:
    """Figma 플로우 정보"""
    id: str
    name: str
    screens: List[FigmaScreen] = field(default_factory=list)
    connectors: List[Dict] = field(default_factory=list)
    last_modified: str = ""
    version: str = ""


class FigmaIntegration:
    """Figma API 연동 클래스"""

    BASE_URL = "https://api.figma.com/v1"

    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("FIGMA_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("FIGMA_ACCESS_TOKEN이 필요합니다.")

        self.headers = {"X-Figma-Token": self.access_token}
        self.cache_dir = Path(__file__).parent.parent / "data" / "figma_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_file(self, file_key: str) -> Dict:
        """Figma 파일 정보 조회"""
        url = f"{self.BASE_URL}/files/{file_key}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_node(self, file_key: str, node_id: str, depth: int = 10) -> Dict:
        """특정 노드 정보 조회"""
        url = f"{self.BASE_URL}/files/{file_key}/nodes"
        params = {"ids": node_id, "depth": depth}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_image(self, file_key: str, node_ids: List[str], scale: int = 2, format: str = "png") -> Dict:
        """노드 이미지 URL 조회"""
        url = f"{self.BASE_URL}/images/{file_key}"
        params = {
            "ids": ",".join(node_ids),
            "scale": scale,
            "format": format
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def download_image(self, image_url: str, save_path: Path) -> Path:
        """이미지 다운로드"""
        response = requests.get(image_url)
        response.raise_for_status()
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(response.content)
        return save_path

    def extract_flow(self, file_key: str, node_id: str) -> FigmaFlow:
        """플로우 정보 추출"""
        data = self.get_node(file_key, node_id)
        node_key = node_id.replace("-", ":")

        if node_key not in data.get("nodes", {}):
            raise ValueError(f"노드를 찾을 수 없습니다: {node_id}")

        node_data = data["nodes"][node_key]
        document = node_data["document"]

        flow = FigmaFlow(
            id=document["id"],
            name=document["name"],
            last_modified=data.get("lastModified", ""),
            version=data.get("version", "")
        )

        # 화면 및 커넥터 추출
        self._extract_children(document.get("children", []), flow)

        return flow

    def _extract_children(self, children: List[Dict], flow: FigmaFlow):
        """자식 요소 추출"""
        for child in children:
            child_type = child.get("type", "")
            name = child.get("name", "")
            visible = child.get("visible", True)

            # 커넥터 (플로우 연결선)
            if child_type == "CONNECTOR":
                flow.connectors.append({
                    "id": child.get("id"),
                    "name": name,
                    "start": child.get("connectorStart", {}),
                    "end": child.get("connectorEnd", {})
                })

            # 프레임 (화면)
            elif child_type == "FRAME" and visible:
                # Group, Frame 1234 등 제외
                if not name.startswith("Frame ") and not name.startswith("Group"):
                    screen = self._extract_screen(child)
                    flow.screens.append(screen)

            # 섹션
            elif child_type == "SECTION":
                # 섹션 내부 탐색
                self._extract_children(child.get("children", []), flow)

    def _extract_screen(self, node: Dict) -> FigmaScreen:
        """화면 정보 추출"""
        screen = FigmaScreen(
            id=node.get("id", ""),
            name=node.get("name", ""),
            type=node.get("type", ""),
            visible=node.get("visible", True)
        )

        # 텍스트, 버튼, 입력 필드 추출
        self._extract_ui_elements(node.get("children", []), screen)

        return screen

    def _extract_ui_elements(self, children: List[Dict], screen: FigmaScreen):
        """UI 요소 추출 (재귀)"""
        for child in children:
            child_type = child.get("type", "")
            name = child.get("name", "").lower()

            # 텍스트
            if child_type == "TEXT":
                chars = child.get("characters", "").strip()
                if chars and len(chars) > 1:
                    screen.texts.append(chars)

            # 버튼 (이름에 button, btn, cta 포함)
            elif any(kw in name for kw in ["button", "btn", "cta"]):
                # 버튼 내 텍스트 찾기
                btn_text = self._find_text_in_node(child)
                if btn_text:
                    screen.buttons.append(btn_text)

            # 입력 필드 (이름에 input, field, 입력 포함)
            elif any(kw in name for kw in ["input", "field", "입력", "textfield"]):
                screen.inputs.append(name)

            # 자식 탐색
            if "children" in child:
                self._extract_ui_elements(child["children"], screen)

    def _find_text_in_node(self, node: Dict) -> Optional[str]:
        """노드 내 텍스트 찾기"""
        if node.get("type") == "TEXT":
            return node.get("characters", "").strip()

        for child in node.get("children", []):
            text = self._find_text_in_node(child)
            if text:
                return text

        return None

    def detect_changes(self, file_key: str, node_id: str) -> Dict:
        """디자인 변경 감지"""
        cache_file = self.cache_dir / f"{file_key}_{node_id.replace(':', '-')}.json"

        # 현재 플로우 추출
        current_flow = self.extract_flow(file_key, node_id)
        current_hash = self._calculate_hash(current_flow)

        changes = {
            "has_changes": False,
            "new_screens": [],
            "removed_screens": [],
            "modified_screens": [],
            "current_version": current_flow.version,
            "current_modified": current_flow.last_modified
        }

        # 캐시된 데이터와 비교
        if cache_file.exists():
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            cached_hash = cached_data.get("hash", "")

            if cached_hash != current_hash:
                changes["has_changes"] = True
                changes["previous_version"] = cached_data.get("version", "")
                changes["previous_modified"] = cached_data.get("last_modified", "")

                # 화면 비교
                cached_screens = {s["name"] for s in cached_data.get("screens", [])}
                current_screens = {s.name for s in current_flow.screens}

                changes["new_screens"] = list(current_screens - cached_screens)
                changes["removed_screens"] = list(cached_screens - current_screens)

                # 수정된 화면 찾기 (같은 이름이지만 내용 다름)
                for screen in current_flow.screens:
                    cached_screen = next(
                        (s for s in cached_data.get("screens", []) if s["name"] == screen.name),
                        None
                    )
                    if cached_screen:
                        if self._screen_changed(screen, cached_screen):
                            changes["modified_screens"].append(screen.name)
        else:
            changes["has_changes"] = True
            changes["new_screens"] = [s.name for s in current_flow.screens]

        # 캐시 업데이트
        cache_data = {
            "hash": current_hash,
            "version": current_flow.version,
            "last_modified": current_flow.last_modified,
            "screens": [asdict(s) for s in current_flow.screens],
            "cached_at": datetime.now().isoformat()
        }
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8")

        return changes

    def _calculate_hash(self, flow: FigmaFlow) -> str:
        """플로우 해시 계산"""
        content = json.dumps([asdict(s) for s in flow.screens], sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def _screen_changed(self, current: FigmaScreen, cached: Dict) -> bool:
        """화면 변경 여부 확인"""
        # 텍스트 비교
        if set(current.texts) != set(cached.get("texts", [])):
            return True
        # 버튼 비교
        if set(current.buttons) != set(cached.get("buttons", [])):
            return True
        # 입력 필드 비교
        if set(current.inputs) != set(cached.get("inputs", [])):
            return True
        return False

    def generate_tc_from_flow(self, flow: FigmaFlow) -> List[Dict]:
        """플로우에서 TC 자동 생성"""
        test_cases = []
        tc_no = 1

        for screen in flow.screens:
            # 화면 로드 TC
            test_cases.append({
                "No": tc_no,
                "preconditions": f"1. 서비스 진입\n2. {screen.name} 화면 접근 가능 상태",
                "title": f"[{screen.name}] 화면 정상 로드 확인",
                "steps_actions": f"1. {screen.name} 화면 진입\n2. 화면 구성 요소 확인",
                "steps_result": self._generate_expected_result(screen),
                "priority": "High",
                "결과": "",
                "비고": "",
                "설명": f"Figma: {screen.name} (ID: {screen.id})"
            })
            tc_no += 1

            # 버튼 TC
            for button in screen.buttons:
                test_cases.append({
                    "No": tc_no,
                    "preconditions": f"1. {screen.name} 화면 진입",
                    "title": f"[{screen.name}] '{button}' 버튼 동작 확인",
                    "steps_actions": f"1. '{button}' 버튼 선택\n2. 동작 결과 확인",
                    "steps_result": "1. 버튼 정상 동작\n2. 다음 단계로 이동 또는 예상 동작 수행",
                    "priority": "High",
                    "결과": "",
                    "비고": "",
                    "설명": f"Figma: {screen.name} > {button}"
                })
                tc_no += 1

            # 입력 필드 TC
            for input_field in screen.inputs:
                test_cases.append({
                    "No": tc_no,
                    "preconditions": f"1. {screen.name} 화면 진입",
                    "title": f"[{screen.name}] '{input_field}' 입력 필드 동작 확인",
                    "steps_actions": f"1. '{input_field}' 입력 필드 선택\n2. 값 입력\n3. 입력 결과 확인",
                    "steps_result": "1. 키보드/입력 UI 노출\n2. 입력값 정상 반영\n3. 유효성 검사 동작",
                    "priority": "High",
                    "결과": "",
                    "비고": "",
                    "설명": f"Figma: {screen.name} > {input_field}"
                })
                tc_no += 1

        return test_cases

    def _generate_expected_result(self, screen: FigmaScreen) -> str:
        """예상 결과 생성"""
        results = []

        # 텍스트 기반 예상 결과
        important_texts = [t for t in screen.texts if len(t) > 5][:5]
        for i, text in enumerate(important_texts, 1):
            results.append(f"{i}. '{text[:50]}...' 텍스트 노출" if len(text) > 50 else f"{i}. '{text}' 텍스트 노출")

        # 버튼 존재 확인
        if screen.buttons:
            results.append(f"{len(results)+1}. 버튼 정상 노출: {', '.join(screen.buttons[:3])}")

        # 입력 필드 존재 확인
        if screen.inputs:
            results.append(f"{len(results)+1}. 입력 필드 정상 노출")

        return "\n".join(results) if results else "화면 정상 로드"


# CLI 실행
if __name__ == "__main__":
    import sys

    token = os.getenv("FIGMA_ACCESS_TOKEN")
    if not token:
        print("FIGMA_ACCESS_TOKEN 환경변수를 설정해주세요.")
        sys.exit(1)

    figma = FigmaIntegration(token)

    # 테스트: 세이브택스 통합 플로우
    file_key = "rcxhAYTksM5DmkrjqTuvHc"
    node_id = "9987-46608"

    print("플로우 추출 중...")
    flow = figma.extract_flow(file_key, node_id)
    print(f"플로우: {flow.name}")
    print(f"화면 수: {len(flow.screens)}")
    print(f"커넥터 수: {len(flow.connectors)}")

    print("\n변경 감지 중...")
    changes = figma.detect_changes(file_key, node_id)
    print(f"변경 여부: {changes['has_changes']}")
    if changes['has_changes']:
        print(f"새 화면: {changes['new_screens']}")
        print(f"삭제된 화면: {changes['removed_screens']}")
        print(f"수정된 화면: {changes['modified_screens']}")
