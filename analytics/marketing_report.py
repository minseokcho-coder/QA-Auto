"""마케팅 성과 분석 Slack 리포트 모듈

Google Sheets에서 종소세/재산세 캠페인 데이터를 자동으로 읽어
전월 대비 비교 분석 리포트를 생성합니다.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

from analytics.sheet_reader import fetch_all_data

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "")


def _fmt_won(amount: float) -> str:
    amount = int(amount)
    if amount >= 100_000_000:
        return f"{amount / 100_000_000:.1f}억"
    if amount >= 10_000:
        return f"{amount / 10_000:.0f}만"
    return f"{amount:,}"


def _change_emoji(before: float, after: float) -> str:
    diff = after - before
    if diff > 0:
        return f":arrow_up: +{diff:.1f}%p"
    if diff < 0:
        return f":arrow_down: {diff:.1f}%p"
    return "→ 동일"


def _change_pct(before: float, after: float, invert: bool = False) -> str:
    if before == 0:
        return "N/A"
    pct = ((after - before) / before) * 100
    up = ":arrow_down:" if invert else ":arrow_up:"
    down = ":arrow_up:" if invert else ":arrow_down:"
    if pct > 0:
        return f"{up} +{pct:.1f}%"
    if pct < 0:
        return f"{down} {pct:.1f}%"
    return "-> 동일"


def _build_campaign_blocks(prev: dict, curr: dict, prev_label: str, curr_label: str,
                           campaign_name: str, is_partial: bool = False) -> list:
    """한 캠페인에 대한 비교 블록 생성"""
    blocks = []
    partial_note = " (진행 중)" if is_partial else ""

    # ── 캠페인 헤더 ──
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*:mega: {campaign_name} 캠페인{partial_note}*\n{prev_label} vs {curr_label}",
        },
    })

    # ── KPI ──
    kpi_fields = []
    if curr.get("total_cost"):
        prev_cost = prev.get("total_cost", 0)
        text = f"*집행 비용*\n{_fmt_won(curr['total_cost'])}"
        if prev_cost:
            text += f" {_change_pct(prev_cost, curr['total_cost'])}"
        kpi_fields.append({"type": "mrkdwn", "text": text})

    prev_sends = prev.get("total_sends", 0)
    curr_sends = curr.get("total_sends", 0)
    if curr_sends:
        kpi_fields.append({
            "type": "mrkdwn",
            "text": f"*총 발송*\n{curr_sends:,.0f} {_change_pct(prev_sends, curr_sends)}"
        })

    if curr.get("roas"):
        kpi_fields.append({
            "type": "mrkdwn",
            "text": f"*ROAS*\n{curr['roas']:.1f}% {_change_emoji(prev.get('roas', 0), curr['roas'])}"
        })

    if curr.get("total_epa"):
        text = f"*통합 EPA*\n{_fmt_won(curr['total_epa'])}"
        if prev.get("total_epa"):
            text += f" {_change_pct(prev['total_epa'], curr['total_epa'])}"
        kpi_fields.append({"type": "mrkdwn", "text": text})

    if kpi_fields:
        blocks.append({"type": "section", "fields": kpi_fields})

    # ── 전환율 비교 ──
    rate_fields = []
    for key, name in [("view_rate", "열람율"), ("click_rate", "클릭율"),
                       ("signup_rate", "가입율"), ("auth_rate", "인증율")]:
        prev_val = prev.get(key, 0)
        curr_val = curr.get(key, 0)
        if curr_val > 0:
            rate_fields.append({
                "type": "mrkdwn",
                "text": f"*{name}*\n{prev_val:.1f}% → {curr_val:.1f}% {_change_emoji(prev_val, curr_val)}"
            })

    if rate_fields:
        blocks.append({"type": "section", "fields": rate_fields})

    # ── 채널별 성과 ──
    channel_lines = []
    if curr.get("jongso_valid"):
        apply_rate = curr.get("jongso_apply_rate", 0)
        line = (
            f":one: *종소세 사업자*: 유효 {curr['jongso_valid']:,.0f}명 | "
            f"신청 {curr['jongso_apply']:,.0f}명"
        )
        if apply_rate:
            line += f" ({apply_rate:.1f}%)"
        if curr.get("jongso_apply_amount"):
            line += f" | 신청환급 {_fmt_won(curr['jongso_apply_amount'])}"
        channel_lines.append(line)

    if curr.get("free_apply"):
        channel_lines.append(
            f":two: *프리/근로*: 신청 {curr['free_apply']:,.0f}명 | "
            f"신청환급 {_fmt_won(curr.get('free_apply_amount', 0))}"
        )

    if curr.get("jongbu_valid"):
        channel_lines.append(
            f":three: *종부세*: 유효 {curr['jongbu_valid']:,.0f}명 | "
            f"신청 {curr['jongbu_apply']:,.0f}명 | "
            f"유효환급 {_fmt_won(curr['jongbu_valid_amount'])}"
        )

    if curr.get("yangdo_valid"):
        channel_lines.append(
            f":four: *양도세*: 유효 {curr['yangdo_valid']:,.0f}명 | "
            f"신청 {curr['yangdo_apply']:,.0f}명 | "
            f"유효환급 {_fmt_won(curr['yangdo_valid_amount'])}"
        )

    if channel_lines:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "\n".join(channel_lines)},
        })

    # ── 전월 대비 채널별 변화 ──
    if prev.get("jongso_valid") and curr.get("jongso_valid"):
        mom_lines = []
        for label, v_key, a_key in [
            ("종소세", "jongso_valid", "jongso_apply"),
            ("종부세", "jongbu_valid", "jongbu_apply"),
            ("양도세", "yangdo_valid", "yangdo_apply"),
        ]:
            if prev.get(v_key) and curr.get(v_key):
                mom_lines.append(
                    f"- *{label}*: 유효 {prev[v_key]:,.0f}→{curr[v_key]:,.0f}명 "
                    f"{_change_pct(prev[v_key], curr[v_key])}, "
                    f"신청 {prev[a_key]:,.0f}→{curr[a_key]:,.0f}명 "
                    f"{_change_pct(prev[a_key], curr[a_key])}"
                )
        if prev.get("free_apply") and curr.get("free_apply"):
            mom_lines.append(
                f"- *프리/근로*: 신청 {prev['free_apply']:,.0f}→{curr['free_apply']:,.0f}명 "
                f"{_change_pct(prev['free_apply'], curr['free_apply'])}"
            )
        if mom_lines:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*:arrows_counterclockwise: 전월 대비 변화*\n" + "\n".join(mom_lines),
                },
            })

    # ── CAC 비교 ──
    if curr.get("cac_signup"):
        cac_fields = []
        for key, name in [("cac_signup", "가입CAC"), ("cac_auth", "인증CAC"),
                           ("cac_valid", "유효CAC"), ("cac_apply", "신청CAC")]:
            if not curr.get(key):
                continue
            text = f"*{name}*\n{curr[key]:,.0f}원"
            if prev.get(key):
                text += f" {_change_pct(prev[key], curr[key], invert=True)}"
            cac_fields.append({"type": "mrkdwn", "text": text})
        if cac_fields:
            blocks.append({"type": "section", "fields": cac_fields})

    return blocks


def _build_insights(prev: dict, curr: dict, prev_label: str, curr_label: str) -> str:
    """자동 인사이트 생성"""
    improved = []
    declined = []

    for key, name in [("view_rate", "열람율"), ("click_rate", "클릭율"),
                       ("signup_rate", "가입율"), ("auth_rate", "인증율"),
                       ("roas", "ROAS")]:
        pv = prev.get(key, 0)
        cv = curr.get(key, 0)
        if cv == 0:
            continue
        diff = cv - pv
        if diff > 0.1:
            improved.append(f"{name}(+{diff:.1f}%p)")
        elif diff < -0.1:
            declined.append(f"{name}({diff:.1f}%p)")

    prev_sends = prev.get("total_sends", 0)
    curr_sends = curr.get("total_sends", 0)
    if prev_sends and curr_sends:
        pct = ((curr_sends - prev_sends) / prev_sends) * 100
        if pct < -5:
            declined.append(f"발송모수({pct:.1f}%)")
        elif pct > 5:
            improved.append(f"발송모수(+{pct:.1f}%)")

    if not improved and not declined:
        return ""

    lines = [f"*:bulb: 핵심 인사이트 ({prev_label} → {curr_label})*\n"]
    if improved:
        lines.append(f":white_check_mark: *개선*: {', '.join(improved)}")
    if declined:
        lines.append(f":x: *하락*: {', '.join(declined)}")

    if prev.get("total_epa") and curr.get("total_epa"):
        diff = curr["total_epa"] - prev["total_epa"]
        if diff > 0:
            lines.append(f":chart_with_upwards_trend: *EPA 성장*: +{_fmt_won(diff)}")
        elif diff < 0:
            lines.append(f":chart_with_downwards_trend: *EPA 감소*: {_fmt_won(abs(diff))}")

    return "\n".join(lines)


def _build_analysis_summary(sheet_data: dict) -> str:
    """전체 캠페인 종합 분석 요약"""
    points = []
    actions = []

    for camp_key, camp_name in [("jongso", "종소세"), ("jaesan", "재산세")]:
        months = sheet_data.get(camp_key, {})
        keys = list(months.keys())
        if len(keys) < 2:
            continue

        prev, curr = months[keys[-2]], months[keys[-1]]
        prev_label = prev.get("label", keys[-2])
        curr_label = curr.get("label", keys[-1])
        is_partial = curr.get("day_count", 0) > 0 and curr.get("day_count", 31) < 20

        # 비용 효율 분석
        prev_cost = prev.get("total_cost", 0)
        curr_cost = curr.get("total_cost", 0)
        prev_roas = prev.get("roas", 0)
        curr_roas = curr.get("roas", 0)
        if prev_cost and curr_cost and prev_roas and curr_roas:
            cost_pct = ((curr_cost - prev_cost) / prev_cost) * 100
            roas_diff = curr_roas - prev_roas
            if cost_pct > 10 and roas_diff < 0:
                points.append(f"*{camp_name}*: 비용 {cost_pct:+.0f}% 증가 대비 ROAS {roas_diff:.1f}%p 하락 - 비용 효율 점검 필요")
                actions.append(f"{camp_name} 타겟팅/소재 최적화 검토")
            elif cost_pct < -5 and roas_diff > 0:
                points.append(f"*{camp_name}*: 비용 절감(-{abs(cost_pct):.0f}%)하면서 ROAS 개선(+{roas_diff:.1f}%p) - 효율 우수")

        # 전환 퍼널 분석
        view_r = curr.get("view_rate", 0)
        signup_r = curr.get("signup_rate", 0)
        auth_r = curr.get("auth_rate", 0)
        prev_view = prev.get("view_rate", 0)
        prev_signup = prev.get("signup_rate", 0)
        prev_auth = prev.get("auth_rate", 0)

        if view_r > 0 and signup_r > 0:
            # 열람은 높은데 가입이 낮으면
            if view_r > prev_view and signup_r < prev_signup:
                points.append(f"*{camp_name}*: 열람율 상승({view_r:.1f}%) 대비 가입율 하락({signup_r:.2f}%) - 랜딩 페이지 전환 병목")
                actions.append(f"{camp_name} 랜딩 페이지 CTA/UX 개선 검토")
            # 가입은 높은데 인증이 낮으면
            if signup_r > prev_signup and auth_r < prev_auth and auth_r > 0:
                points.append(f"*{camp_name}*: 가입율 상승 대비 인증율 하락({auth_r:.1f}%) - 인증 단계 이탈 분석 필요")
                actions.append(f"{camp_name} 본인인증 UX 개선 또는 리마인드 발송 검토")

        # CAC 분석
        prev_cac = prev.get("cac_signup", 0)
        curr_cac = curr.get("cac_signup", 0)
        if prev_cac and curr_cac:
            cac_pct = ((curr_cac - prev_cac) / prev_cac) * 100
            if cac_pct > 20:
                points.append(f"*{camp_name}*: 가입CAC {prev_cac:,.0f}원 -> {curr_cac:,.0f}원 (+{cac_pct:.0f}%) - 획득 비용 급등")
                actions.append(f"{camp_name} 모수 확대 또는 단가 협상 필요")
            elif cac_pct < -10:
                points.append(f"*{camp_name}*: 가입CAC {curr_cac:,.0f}원으로 {abs(cac_pct):.0f}% 절감 - 효율 개선")

        # 채널별 신청율 분석
        apply_rate = curr.get("jongso_apply_rate", 0)
        prev_apply_rate = prev.get("jongso_apply_rate", 0)
        if apply_rate and prev_apply_rate:
            diff = apply_rate - prev_apply_rate
            if diff < -5:
                points.append(f"*{camp_name}*: 종소세 신청율 {prev_apply_rate:.1f}% -> {apply_rate:.1f}% 하락 - 유효->신청 전환 점검")
            elif diff > 5:
                points.append(f"*{camp_name}*: 종소세 신청율 {apply_rate:.1f}%로 개선(+{diff:.1f}%p)")

        # 진행 중 월 페이스 예측
        if is_partial and curr.get("day_count", 0) > 3:
            days = curr["day_count"]
            curr_sends = curr.get("total_sends", 0)
            prev_sends = prev.get("total_sends", 0)
            if curr_sends and prev_sends:
                projected = curr_sends / days * 30
                pace_pct = (projected / prev_sends) * 100
                if pace_pct < 80:
                    points.append(f"*{camp_name}*: {days}일 기준 월말 예상 발송 {projected:,.0f}건 (전월 대비 {pace_pct:.0f}% 페이스)")
                    actions.append(f"{camp_name} 발송 모수 확대 계획 수립 필요")

    if not points and not actions:
        return ""

    lines = ["*:mag: 종합 분석 요약*\n"]
    for p in points:
        lines.append(f"- {p}")

    if actions:
        lines.append("\n*:pushpin: Action Items*")
        for i, a in enumerate(actions, 1):
            lines.append(f"{i}. {a}")

    return "\n".join(lines)


def build_report_blocks(sheet_data: dict = None) -> list:
    """Google Sheets 데이터로 Slack 리포트 블록을 생성합니다."""
    if sheet_data is None:
        sheet_data = fetch_all_data()

    today = datetime.now().strftime("%Y년 %m월 %d일")

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "마케팅 성과 분석 리포트", "emoji": True},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f":calendar: {today} | Google Sheets 실시간 데이터"}],
        },
        {"type": "divider"},
    ]

    # ── 각 캠페인별 비교 ──
    campaign_labels = {"jongso": "종소세 TMS", "jaesan": "재산세 TMS"}

    for camp_key, camp_name in campaign_labels.items():
        months = sheet_data.get(camp_key, {})
        if not months:
            continue

        keys = list(months.keys())

        if len(keys) >= 2:
            prev_key, curr_key = keys[-2], keys[-1]
            prev, curr = months[prev_key], months[curr_key]
            prev_label = prev.get("label", prev_key)
            curr_label = curr.get("label", curr_key)
            is_partial = curr.get("day_count", 0) > 0 and curr.get("day_count", 31) < 20

            camp_blocks = _build_campaign_blocks(
                prev, curr, prev_label, curr_label, camp_name, is_partial
            )
            blocks.extend(camp_blocks)

            # 인사이트
            insights = _build_insights(prev, curr, prev_label, curr_label)
            if insights:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": insights},
                })

            blocks.append({"type": "divider"})

        elif len(keys) == 1:
            # 한 달만 있으면 단독 표시
            curr = months[keys[0]]
            curr_label = curr.get("label", keys[0])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*:mega: {camp_name} 캠페인 ({curr_label})*\n"
                        f"발송 {curr['total_sends']:,.0f} | "
                        f"열람율 {curr.get('view_rate', 0):.1f}% | "
                        f"ROAS {curr.get('roas', 0):.1f}% | "
                        f"EPA {_fmt_won(curr.get('total_epa', 0))}"
                    ),
                },
            })
            blocks.append({"type": "divider"})

    # ── 통합 트렌드 테이블 (종소세 기준) ──
    jongso = sheet_data.get("jongso", {})
    if len(jongso) >= 2:
        lines = ["*:chart_with_upwards_trend: 종소세 월별 추이*\n```"]
        lines.append(f"{'기간':<12} {'발송':>10} {'열람율':>8} {'가입율':>8} {'인증율':>8} {'ROAS':>8} {'EPA':>10}")
        lines.append("-" * 72)
        for key, m in jongso.items():
            label = m.get("label", key)[:10]
            partial = "*" if m.get("day_count", 0) > 0 and m.get("day_count", 31) < 20 else " "
            lines.append(
                f"{label:<12}{partial}"
                f"{m['total_sends']:>9,.0f} "
                f"{m.get('view_rate', 0):>7.1f}% "
                f"{m.get('signup_rate', 0):>7.2f}% "
                f"{m.get('auth_rate', 0):>7.1f}% "
                f"{m.get('roas', 0):>7.1f}% "
                f"{_fmt_won(m.get('total_epa', 0)):>9}"
            )
        lines.append("```")
        lines.append("_* 진행 중인 월_")
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "\n".join(lines)},
        })

    # ── 분석 요약 ──
    summary = _build_analysis_summary(sheet_data)
    if summary:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary},
        })

    # ── 푸터 ──
    blocks.append({
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": ":robot_face: _PM Scraper Bot | Google Sheets 자동 연동_",
        }],
    })

    return blocks


def send_marketing_report(channel: str = None, test_mode: bool = False) -> bool:
    """마케팅 성과 분석 리포트를 Slack으로 전송"""
    sheet_data = fetch_all_data()
    blocks = build_report_blocks(sheet_data)
    text = f"마케팅 성과 분석 리포트 - {datetime.now().strftime('%Y년 %m월')}"

    if test_mode:
        print("=" * 60)
        print("[테스트 모드] 마케팅 리포트 미리보기")
        print("=" * 60)
        for block in blocks:
            btype = block.get("type")
            if btype == "header":
                print(f"\n### {block['text']['text']}")
            elif btype == "section":
                if "fields" in block:
                    for f in block["fields"]:
                        print(f"  {f['text']}")
                elif "text" in block:
                    print(f"  {block['text']['text']}")
            elif btype == "divider":
                print("-" * 40)
            elif btype == "context":
                for el in block.get("elements", []):
                    print(f"  {el.get('text', '')}")
        print("=" * 60)
        return True

    if not SLACK_BOT_TOKEN:
        print("SLACK_BOT_TOKEN이 설정되지 않았습니다.")
        return False

    target_channel = channel or SLACK_CHANNEL
    if not target_channel:
        print("SLACK_CHANNEL이 설정되지 않았습니다.")
        return False

    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        client.chat_postMessage(
            channel=target_channel,
            blocks=blocks,
            text=text,
            unfurl_links=False,
            unfurl_media=False,
        )
        print(f"마케팅 리포트 전송 성공 → {target_channel}")
        return True
    except SlackApiError as e:
        print(f"마케팅 리포트 전송 실패: {e.response['error']}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="마케팅 성과 분석 Slack 리포트")
    parser.add_argument("--test", action="store_true", help="테스트 모드 (콘솔 출력만)")
    parser.add_argument("--channel", type=str, help="전송할 Slack 채널 ID")
    args = parser.parse_args()

    send_marketing_report(channel=args.channel, test_mode=args.test)
