"""Google Sheets CSV 자동 읽기 및 월별 집계 모듈

스프레드시트에서 종소세/재산세 캠페인 데이터를 읽어
월별로 집계하고 전월 대비 비교 데이터를 반환합니다.
"""
import csv
import io
import urllib.request
from collections import defaultdict, OrderedDict

SPREADSHEET_ID = "1nfd0FP4nu2KmAUjSQKGceQErb2RWC1d2S6C3JmAl3e0"

SHEET_GIDS = {
    "jongso": 2122951693,   # 종소세_일자별 통계
    "jaesan": 1942138602,   # 재산세_일자별 통계
}


def _fetch_csv(gid: int) -> str:
    url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
        f"/gviz/tq?tqx=out:csv&gid={gid}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8-sig")


def _num(val: str) -> float:
    """'1,362,014' → 1362014.0 / '67.04%' → 67.04 / '' → 0"""
    if not val:
        return 0
    s = val.strip().replace(",", "").replace("%", "").replace("원", "")
    if not s or s in ("?", "#N/A", "-", "N/A"):
        return 0
    try:
        return float(s)
    except ValueError:
        return 0


def _get(row, idx):
    return row[idx].strip() if idx < len(row) else ""


# ── 종소세_일자별 통계 컬럼 인덱스 ──
_J = {
    "tier": 1, "date": 2, "cost": 3,
    "sends": 4, "views": 5, "clicks": 6,
    "view_rate": 7, "click_rate": 8,
    "signups": 11, "signup_rate": 12,
    "auths": 13, "auth_rate": 14,
    "jongso_valid": 25, "jongso_valid_amt": 26,
    "jongso_apply": 30, "jongso_apply_amt": 31,
    "jongso_apply_rate": 35,
    "jongso_epa": 40, "roas": 42,
    "cac_signup": 43, "cac_auth": 44,
    "cac_valid": 46, "cac_apply": 47,
    "free_valid": 49, "free_valid_amt": 50,
    "free_apply": 53, "free_apply_amt": 54,
    "jongbu_valid": 68, "jongbu_valid_amt": 69,
    "jongbu_apply": 72, "jongbu_apply_amt": 73,
    "yangdo_valid": 85, "yangdo_valid_amt": 86,
    "yangdo_apply": 89, "yangdo_apply_amt": 90,
    "total_epa": 101, "total_roas": 102,
    "total_apply_cac": 103,
}

# ── 재산세_일자별 통계 컬럼 인덱스 ──
# 실제 CSV 컬럼 확인: 합계행 기준
#   25=종소유효(266), 30=당일신청(135), 42=프리근로유효(3307),
#   46=프리근로신청(1702), 54=종부세유효(767), 58=종부세신청(330),
#   64=양도세유효(720), 68=양도세신청(350), 78=통합EPA(97,073,694),
#   79=ROAS종소+재산(126.07%), 74=가입CAC(2062), 75=인증CAC(3630)
_R = {
    "tier": 1, "date": 2, "cost": 3,
    "sends": 4, "views": 5, "clicks": 6,
    "view_rate": 7, "click_rate": 8,
    "signups": 11, "signup_rate": 12,
    "auths": 13, "auth_rate": 14,
    "jongso_valid": 25, "jongso_valid_amt": 26,
    "jongso_apply": 30, "jongso_apply_amt": 31,
    "jongso_apply_rate": 35,
    "free_apply": 46, "free_apply_amt": 47,
    "jongbu_valid": 54, "jongbu_valid_amt": 55,
    "jongbu_apply": 58, "jongbu_apply_amt": 59,
    "yangdo_valid": 64, "yangdo_valid_amt": 65,
    "yangdo_apply": 68, "yangdo_apply_amt": 69,
    "total_epa": 78, "total_roas": 79,
    "cac_signup": 74, "cac_auth": 75,
    "cac_valid": 76, "cac_apply": 77,
}


def _empty_month():
    return {
        "total_cost": 0, "total_sends": 0, "total_views": 0, "total_clicks": 0,
        "total_signups": 0, "total_auths": 0,
        "jongso_valid": 0, "jongso_valid_amount": 0,
        "jongso_apply": 0, "jongso_apply_amount": 0,
        "free_apply": 0, "free_apply_amount": 0,
        "jongbu_valid": 0, "jongbu_valid_amount": 0,
        "jongbu_apply": 0, "jongbu_apply_amount": 0,
        "yangdo_valid": 0, "yangdo_valid_amount": 0,
        "yangdo_apply": 0, "yangdo_apply_amount": 0,
        "total_epa": 0, "roas": 0,
        "cac_signup": 0, "cac_auth": 0, "cac_valid": 0, "cac_apply": 0,
        "day_count": 0,
    }


def _add_row(month_data: dict, row: list, col_map: dict):
    """일별 데이터 행을 월별 누적에 더합니다."""
    sends = _num(_get(row, col_map["sends"]))
    if sends == 0:
        return  # 빈 행 스킵

    month_data["total_cost"] += _num(_get(row, col_map["cost"]))
    month_data["total_sends"] += sends
    month_data["total_views"] += _num(_get(row, col_map["views"]))
    month_data["total_clicks"] += _num(_get(row, col_map["clicks"]))
    month_data["total_signups"] += _num(_get(row, col_map["signups"]))
    month_data["total_auths"] += _num(_get(row, col_map["auths"]))
    month_data["jongso_valid"] += _num(_get(row, col_map["jongso_valid"]))
    month_data["jongso_valid_amount"] += _num(_get(row, col_map["jongso_valid_amt"]))
    month_data["jongso_apply"] += _num(_get(row, col_map["jongso_apply"]))
    month_data["jongso_apply_amount"] += _num(_get(row, col_map["jongso_apply_amt"]))
    month_data["free_apply"] += _num(_get(row, col_map.get("free_apply", 999)))
    month_data["free_apply_amount"] += _num(_get(row, col_map.get("free_apply_amt", 999)))
    month_data["jongbu_valid"] += _num(_get(row, col_map["jongbu_valid"]))
    month_data["jongbu_valid_amount"] += _num(_get(row, col_map["jongbu_valid_amt"]))
    month_data["jongbu_apply"] += _num(_get(row, col_map["jongbu_apply"]))
    month_data["jongbu_apply_amount"] += _num(_get(row, col_map["jongbu_apply_amt"]))
    month_data["yangdo_valid"] += _num(_get(row, col_map["yangdo_valid"]))
    month_data["yangdo_valid_amount"] += _num(_get(row, col_map["yangdo_valid_amt"]))
    month_data["yangdo_apply"] += _num(_get(row, col_map["yangdo_apply"]))
    month_data["yangdo_apply_amount"] += _num(_get(row, col_map["yangdo_apply_amt"]))
    month_data["total_epa"] += _num(_get(row, col_map.get("total_epa", col_map.get("jongso_epa", 999))))
    month_data["day_count"] += 1


def _calc_rates(m: dict):
    """누적 데이터에서 비율 재계산"""
    s = m["total_sends"]
    if s > 0:
        m["view_rate"] = round(m["total_views"] / s * 100, 2)
        m["click_rate"] = round(m["total_clicks"] / s * 100, 2)
        m["signup_rate"] = round(m["total_signups"] / s * 100, 2)
        m["auth_rate"] = round(m["total_auths"] / m["total_signups"] * 100, 2) if m["total_signups"] else 0
    if m["total_cost"] > 0 and m["total_epa"] > 0:
        m["roas"] = round(m["total_epa"] / m["total_cost"] * 100, 2)
    if m["total_signups"] > 0:
        m["cac_signup"] = round(m["total_cost"] / m["total_signups"])
    if m["total_auths"] > 0:
        m["cac_auth"] = round(m["total_cost"] / m["total_auths"])
    if m["jongso_valid"] > 0:
        m["cac_valid"] = round(m["total_cost"] / m["jongso_valid"])
    if m["jongso_apply"] > 0:
        m["cac_apply"] = round(m["total_cost"] / m["jongso_apply"])
    if m["jongso_apply"] > 0 and m["jongso_valid"] > 0:
        m["jongso_apply_rate"] = round(m["jongso_apply"] / m["jongso_valid"] * 100, 2)


def _parse_sheet(gid: int, col_map: dict, campaign_name: str) -> OrderedDict:
    """시트를 파싱하여 월별 집계 데이터를 반환합니다."""
    raw = _fetch_csv(gid)
    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    if len(rows) < 2:
        return OrderedDict()

    data_rows = rows[1:]  # 헤더 스킵
    monthly = defaultdict(_empty_month)
    summary_found = {}

    for row in data_rows:
        if len(row) < 10:
            continue

        tier = _get(row, col_map.get("tier", 1))
        date_str = _get(row, col_map["date"])
        cost_str = _get(row, col_map["cost"])
        sends_str = _get(row, col_map["sends"])

        # 완전히 빈 행 스킵
        if not sends_str and not cost_str and not date_str:
            continue

        # 합계 행: 티어/날짜 없고 데이터 있음
        if not tier and not date_str and _num(cost_str) > 0:
            # 합계 행의 데이터를 직접 사용 (더 정확)
            summary = _empty_month()
            summary["total_cost"] = _num(cost_str)
            summary["total_sends"] = _num(sends_str)
            summary["total_views"] = _num(_get(row, col_map["views"]))
            summary["total_clicks"] = _num(_get(row, col_map["clicks"]))
            summary["total_signups"] = _num(_get(row, col_map["signups"]))
            summary["total_auths"] = _num(_get(row, col_map["auths"]))
            summary["view_rate"] = _num(_get(row, col_map["view_rate"]))
            summary["click_rate"] = _num(_get(row, col_map["click_rate"]))
            summary["signup_rate"] = _num(_get(row, col_map["signup_rate"]))
            summary["auth_rate"] = _num(_get(row, col_map["auth_rate"]))
            summary["jongso_valid"] = _num(_get(row, col_map["jongso_valid"]))
            summary["jongso_valid_amount"] = _num(_get(row, col_map["jongso_valid_amt"]))
            summary["jongso_apply"] = _num(_get(row, col_map["jongso_apply"]))
            summary["jongso_apply_amount"] = _num(_get(row, col_map["jongso_apply_amt"]))
            summary["jongso_apply_rate"] = _num(_get(row, col_map.get("jongso_apply_rate", 999)))
            summary["free_apply"] = _num(_get(row, col_map.get("free_apply", 999)))
            summary["free_apply_amount"] = _num(_get(row, col_map.get("free_apply_amt", 999)))
            summary["jongbu_valid"] = _num(_get(row, col_map["jongbu_valid"]))
            summary["jongbu_valid_amount"] = _num(_get(row, col_map["jongbu_valid_amt"]))
            summary["jongbu_apply"] = _num(_get(row, col_map["jongbu_apply"]))
            summary["jongbu_apply_amount"] = _num(_get(row, col_map["jongbu_apply_amt"]))
            summary["yangdo_valid"] = _num(_get(row, col_map["yangdo_valid"]))
            summary["yangdo_valid_amount"] = _num(_get(row, col_map["yangdo_valid_amt"]))
            summary["yangdo_apply"] = _num(_get(row, col_map["yangdo_apply"]))
            summary["yangdo_apply_amount"] = _num(_get(row, col_map["yangdo_apply_amt"]))
            summary["total_epa"] = _num(_get(row, col_map.get("total_epa", col_map.get("jongso_epa", 999))))
            summary["roas"] = _num(_get(row, col_map.get("total_roas", col_map.get("roas", 999))))
            summary["cac_signup"] = _num(_get(row, col_map["cac_signup"]))
            summary["cac_auth"] = _num(_get(row, col_map["cac_auth"]))
            summary["cac_valid"] = _num(_get(row, col_map["cac_valid"]))
            summary["cac_apply"] = _num(_get(row, col_map["cac_apply"]))
            # 어떤 월인지 마지막으로 본 월 사용
            summary_found["latest"] = summary
            continue

        # 일별 데이터 행
        if not date_str or not date_str.startswith("202"):
            continue

        month_key = date_str[:7]  # "2026-01" or "2026-02"
        _add_row(monthly[month_key], row, col_map)

    # 합계 행이 있으면 해당 월의 일별 집계 대신 사용
    # (합계 행은 보통 1월 데이터 직후에 나옴)
    result = OrderedDict()
    for month_key in sorted(monthly.keys()):
        m = monthly[month_key]
        if m["total_sends"] == 0:
            continue
        _calc_rates(m)
        result[month_key] = m

    # 합계 행이 있고, 1월 데이터가 있으면 1월을 합계 행으로 대체
    if "latest" in summary_found and "2026-01" in result:
        s = summary_found["latest"]
        # 합계 행의 비율은 이미 정확하므로 그대로 사용
        result["2026-01"] = s

    # 라벨 추가
    for key in result:
        if key == "2025-Q4":
            result[key]["label"] = "2025 Q4"
        else:
            year, month = key.split("-")
            result[key]["label"] = f"{year}년 {int(month)}월"
        result[key]["campaign"] = campaign_name

    return result


def fetch_all_data() -> dict:
    """모든 시트에서 월별 데이터를 가져옵니다.

    Returns:
        {
            "jongso": OrderedDict {"2026-01": {...}, "2026-02": {...}},
            "jaesan": OrderedDict {"2026-01": {...}},
        }
    """
    result = {}
    print("Google Sheets에서 데이터를 가져오는 중...")

    try:
        print("  [종소세] 읽는 중...")
        result["jongso"] = _parse_sheet(SHEET_GIDS["jongso"], _J, "종소세")
        for k, v in result["jongso"].items():
            print(f"    {k}: 발송 {v['total_sends']:,.0f} / 가입 {v['total_signups']:,.0f}")
    except Exception as e:
        print(f"  [종소세] 오류: {e}")
        result["jongso"] = OrderedDict()

    try:
        print("  [재산세] 읽는 중...")
        result["jaesan"] = _parse_sheet(SHEET_GIDS["jaesan"], _R, "재산세")
        for k, v in result["jaesan"].items():
            print(f"    {k}: 발송 {v['total_sends']:,.0f} / 가입 {v['total_signups']:,.0f}")
    except Exception as e:
        print(f"  [재산세] 오류: {e}")
        result["jaesan"] = OrderedDict()

    return result


def get_monthly_comparison(campaign: str = "jongso") -> tuple:
    """지정된 캠페인의 최근 두 달 데이터를 반환합니다.

    Returns:
        (prev_key, curr_key, prev_data, curr_data) 또는 None
    """
    data = fetch_all_data()
    camp = data.get(campaign, {})
    if len(camp) < 2:
        return None

    keys = list(camp.keys())
    return keys[-2], keys[-1], camp[keys[-2]], camp[keys[-1]]


if __name__ == "__main__":
    data = fetch_all_data()

    for campaign, months in data.items():
        print(f"\n{'=' * 60}")
        print(f"캠페인: {campaign}")
        print(f"{'=' * 60}")
        for month_key, m in months.items():
            label = m.get("label", month_key)
            print(f"\n  [{label}] ({m.get('day_count', '?')}일)")
            print(f"    비용: {m['total_cost']:,.0f}원")
            print(f"    발송: {m['total_sends']:,.0f}")
            print(f"    열람율: {m.get('view_rate', 0):.2f}%")
            print(f"    클릭율: {m.get('click_rate', 0):.2f}%")
            print(f"    가입율: {m.get('signup_rate', 0):.2f}%")
            print(f"    인증율: {m.get('auth_rate', 0):.2f}%")
            print(f"    ROAS: {m.get('roas', 0):.2f}%")
            print(f"    종소 유효: {m['jongso_valid']:,.0f}명 / 신청: {m['jongso_apply']:,.0f}명")
            print(f"    종부세 유효: {m['jongbu_valid']:,.0f}명 / 신청: {m['jongbu_apply']:,.0f}명")
            print(f"    양도세 유효: {m['yangdo_valid']:,.0f}명 / 신청: {m['yangdo_apply']:,.0f}명")
            print(f"    통합 EPA: {m['total_epa']:,.0f}원")
            if m.get("cac_signup"):
                print(f"    가입CAC: {m['cac_signup']:,.0f}원 / 인증CAC: {m['cac_auth']:,.0f}원")
