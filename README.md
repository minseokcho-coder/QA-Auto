# PM/PO 자료 스크래핑 봇

서비스 기획, 프로덕트 매니저(PM), 프로덕트 오너(PO) 관련 콘텐츠를 자동으로 수집하여 슬랙으로 알림을 보내는 봇입니다.

## 기능

- PM/PO 관련 아티클 자동 수집
- 키워드 기반 필터링
- 슬랙 Webhook을 통한 알림
- 중복 전송 방지 (캐시)
- 스케줄링 지원 (매일 지정 시간 실행)

## 스크래핑 소스

| 소스 | 상태 | 방식 |
|------|------|------|
| 요즘IT | ✅ 활성 | RSS |
| Medium | ✅ 활성 | RSS |
| GeekNews | ✅ 활성 | RSS |
| 브런치 | ⚠️ 비활성 | CSR 사이트 |
| 디스콰이엇 | ⚠️ 비활성 | CSR 사이트 |

## 설치

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
copy .env.example .env
# .env 파일에서 SLACK_WEBHOOK_URL 설정
```

## 사용법

### 테스트 실행 (슬랙 전송 없이)
```bash
python main.py --test
```

### 즉시 실행 (슬랙 전송)
```bash
python main.py --run
```

### 스케줄러 모드 (매일 지정 시간 실행)
```bash
python main.py
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| SLACK_WEBHOOK_URL | 슬랙 Webhook URL | (필수) |
| SCHEDULE_TIME | 스케줄 실행 시간 | 09:00 |
| CACHE_FILE | 캐시 파일 경로 | cache.json |
| HOURS_LIMIT | 스크래핑 시간 제한 | 24 |

## 프로젝트 구조

```
pm-scraper-bot/
├── config.py           # 설정
├── main.py             # 메인 실행
├── requirements.txt    # 의존성
├── .env.example        # 환경변수 예시
├── scrapers/           # 스크래퍼
│   ├── base.py         # 베이스 클래스
│   ├── yozm.py         # 요즘IT
│   ├── medium.py       # Medium
│   ├── geeknews.py     # GeekNews
│   ├── brunch.py       # 브런치 (비활성)
│   └── disquiet.py     # 디스콰이엇 (비활성)
├── notifiers/
│   └── slack.py        # 슬랙 알림
└── utils/
    └── cache.py        # 중복 방지 캐시
```

## Slack Webhook 설정

1. https://api.slack.com/apps 접속
2. "Create New App" → "From scratch"
3. App 이름: `PM Scraper Bot`
4. "Incoming Webhooks" 활성화
5. "Add New Webhook to Workspace" 클릭
6. 채널 선택 후 "Allow"
7. 생성된 URL을 `.env` 파일에 설정

## 키워드 설정

`config.py`에서 검색 키워드를 수정할 수 있습니다:

```python
KEYWORDS = [
    "PM", "PO", "프로덕트", "기획", "기획자",
    "product manager", "product owner", "UX", ...
]
```
