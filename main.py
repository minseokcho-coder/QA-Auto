"""PM/PO 스크래핑 봇 메인 실행 파일"""
import argparse
import sys
import time
from datetime import datetime

import schedule

from scrapers import (
    YozmScraper,
    BrunchScraper,
    MediumScraper,
    GeekNewsScraper,
    DisquietScraper,
    OutstandingScraper,
    VentureSquareScraper,
    PlatumScraper,
    BylineScraper,
    Article,
)
from notifiers import SlackNotifier
from utils import Cache
from config import SCRAPERS_ENABLED, SCHEDULE_TIME, SLACK_WEBHOOK_URL, MAX_ARTICLES


def get_scrapers() -> list:
    """활성화된 스크래퍼 목록 반환"""
    scrapers = []

    if SCRAPERS_ENABLED.get("yozm", True):
        scrapers.append(YozmScraper())
    if SCRAPERS_ENABLED.get("brunch", False):
        scrapers.append(BrunchScraper())
    if SCRAPERS_ENABLED.get("medium", False):
        scrapers.append(MediumScraper())
    if SCRAPERS_ENABLED.get("geeknews", True):
        scrapers.append(GeekNewsScraper())
    if SCRAPERS_ENABLED.get("disquiet", False):
        scrapers.append(DisquietScraper())
    if SCRAPERS_ENABLED.get("outstanding", True):
        scrapers.append(OutstandingScraper())
    if SCRAPERS_ENABLED.get("venturesquare", True):
        scrapers.append(VentureSquareScraper())
    if SCRAPERS_ENABLED.get("platum", True):
        scrapers.append(PlatumScraper())
    if SCRAPERS_ENABLED.get("byline", True):
        scrapers.append(BylineScraper())

    return scrapers


def run_scraping(test_mode: bool = False) -> None:
    """스크래핑 실행 및 슬랙 전송"""
    print(f"\n{'=' * 50}")
    print(f"스크래핑 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 50}\n")

    cache = Cache()
    notifier = SlackNotifier()
    scrapers = get_scrapers()

    all_articles: list[Article] = []

    for scraper in scrapers:
        print(f"[{scraper.name}] 스크래핑 중...")
        try:
            articles = scraper.scrape()
            print(f"[{scraper.name}] {len(articles)}개 아티클 발견")

            # 중복 필터링
            new_articles = [a for a in articles if not cache.is_sent(a.url)]
            print(f"[{scraper.name}] {len(new_articles)}개 새 아티클")

            all_articles.extend(new_articles)

        except Exception as e:
            print(f"[{scraper.name}] 오류 발생: {e}")
            continue

    print(f"\n총 {len(all_articles)}개의 새 아티클 발견")

    # 최대 개수 제한
    if len(all_articles) > MAX_ARTICLES:
        print(f"→ {MAX_ARTICLES}개로 제한")
        all_articles = all_articles[:MAX_ARTICLES]

    if all_articles:
        # 슬랙 전송
        success = notifier.send(all_articles, test_mode=test_mode)

        if success and not test_mode:
            # 전송 성공 시 캐시에 저장
            for article in all_articles:
                cache.mark_sent(article.url)
            cache.save()
            print("캐시 저장 완료")
    else:
        print("새로운 아티클이 없습니다.")

    print(f"\n스크래핑 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def run_scheduler() -> None:
    """스케줄러 실행"""
    if not SLACK_WEBHOOK_URL:
        print("경고: SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        print(".env 파일에 SLACK_WEBHOOK_URL을 설정해주세요.")

    print(f"스케줄러 시작 - 매일 {SCHEDULE_TIME}에 실행됩니다.")
    print("종료하려면 Ctrl+C를 누르세요.\n")

    schedule.every().day.at(SCHEDULE_TIME).do(run_scraping)

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(
        description="PM/PO 콘텐츠 스크래핑 봇",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py --test     테스트 실행 (슬랙 전송 없이 미리보기)
  python main.py --run      즉시 실행 (슬랙 전송)
  python main.py            스케줄러 모드로 실행
        """
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="테스트 모드 (슬랙 전송 없이 결과만 출력)"
    )

    parser.add_argument(
        "--run",
        action="store_true",
        help="즉시 실행 (스케줄러 없이 한 번만 실행)"
    )

    args = parser.parse_args()

    if args.test:
        print("테스트 모드로 실행합니다...")
        run_scraping(test_mode=True)

    elif args.run:
        print("즉시 실행 모드...")
        run_scraping(test_mode=False)

    else:
        try:
            run_scheduler()
        except KeyboardInterrupt:
            print("\n스케줄러 종료")
            sys.exit(0)


if __name__ == "__main__":
    main()
