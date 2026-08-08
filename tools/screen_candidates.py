#!/usr/bin/env python3
"""
종목 선정 스크리너 — 시가총액/섹터 조건으로 미국 상장 후보 티커를 조회한다.

yfinance의 EquityQuery/screen()으로 조건에 맞는 티커를 조회한 뒤,
- data/analysis_index.txt 기준 최근 N개월 이내 분석된 티커
- data/watchlist.txt 에 이미 대기 중인 티커
를 제외한 후보 목록을 stdout에 출력한다. 파일은 읽기만 하며 아무것도 쓰지 않는다.

Claude Code Remote(클라우드) 세션 등 egress 정책상 외부 도메인 접근이 막혀
yfinance 조회 자체가 불가능한 환경에서는 --tickers 로 후보 티커를 직접 넘기면
네트워크 호출 없이 동일한 로컬 제외 필터(최근 분석/watchlist 중복)만 적용해
결과를 낼 수 있다 (예: WebSearch로 후보를 수집한 뒤 이 옵션으로 걸러내기).

사용법:
    python3 tools/screen_candidates.py [옵션]

옵션:
    --sectors                콤마 구분 섹터 목록
                              (기본값: Technology,Healthcare,Consumer Cyclical,Consumer Defensive)
    --market-cap-min          최소 시가총액(달러, 기본값: 300000000)
    --market-cap-max          최대 시가총액(달러, 기본값: 10000000000)
    --exclude-recent-months   이 개월 수 이내 분석된 티커 제외 (기본값: 3, 0이면 제외 안 함)
    --limit                   최대 결과 개수 (기본값: 20)
    --region                  yfinance region 코드 (기본값: us, NYSE/NASDAQ 근사)
    --tickers                 콤마 구분 티커 목록. 주어지면 yfinance 조회를 건너뛰고
                              로컬 제외 필터만 적용한다 (네트워크 불필요).

의존성: yfinance (pip install -r requirements.txt) — --tickers 사용 시에는 불필요.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WATCHLIST_FILE = PROJECT_ROOT / "data" / "watchlist.txt"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis_index  # noqa: E402 (tools/analysis_index.py 재사용)

DEFAULT_SECTORS = ["Technology", "Healthcare", "Consumer Cyclical", "Consumer Defensive"]
DEFAULT_MARKET_CAP_MIN = 300_000_000
DEFAULT_MARKET_CAP_MAX = 10_000_000_000
DEFAULT_EXCLUDE_RECENT_MONTHS = 3
DEFAULT_LIMIT = 20


def parse_args(argv):
    parser = argparse.ArgumentParser(description="시가총액/섹터 기반 종목 스크리너")
    parser.add_argument("--sectors", default=",".join(DEFAULT_SECTORS))
    parser.add_argument("--market-cap-min", type=int, default=DEFAULT_MARKET_CAP_MIN)
    parser.add_argument("--market-cap-max", type=int, default=DEFAULT_MARKET_CAP_MAX)
    parser.add_argument("--exclude-recent-months", type=int, default=DEFAULT_EXCLUDE_RECENT_MONTHS)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--region", default="us")
    parser.add_argument(
        "--tickers",
        default=None,
        help="콤마 구분 티커 목록. 주어지면 yfinance 조회를 건너뛰고 로컬 제외 필터만 적용한다.",
    )
    return parser.parse_args(argv)


def load_watchlist_tickers() -> set:
    """data/watchlist.txt 에 이미 대기 중인 티커 집합을 반환."""
    tickers = set()
    if not WATCHLIST_FILE.exists():
        return tickers
    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].strip()
            if line:
                tickers.add(line.upper())
    return tickers


def recently_analyzed_tickers(months: int) -> set:
    """최근 `months` 개월 이내 분석된 티커 집합을 반환. months <= 0이면 빈 집합."""
    if months <= 0:
        return set()
    cutoff = datetime.now() - timedelta(days=months * 30)
    excluded = set()
    for ticker, date_str in analysis_index.load_index().items():
        try:
            analyzed_on = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        if analyzed_on >= cutoff:
            excluded.add(ticker)
    return excluded


def build_query(sectors, market_cap_min, market_cap_max, region):
    try:
        import yfinance as yf
    except ImportError as e:
        raise SystemExit(
            "ERROR: yfinance가 설치되어 있지 않습니다. `pip install -r requirements.txt` 실행 후 다시 시도하세요."
        ) from e

    conditions = [
        yf.EquityQuery("eq", ["region", region]),
        yf.EquityQuery("btwn", ["intradaymarketcap", market_cap_min, market_cap_max]),
    ]
    if sectors:
        sector_conditions = [yf.EquityQuery("eq", ["sector", s]) for s in sectors]
        conditions.append(
            sector_conditions[0] if len(sector_conditions) == 1 else yf.EquityQuery("or", sector_conditions)
        )
    return yf, yf.EquityQuery("and", conditions)


def run_screen(yf, query, limit):
    try:
        response = yf.screen(query, sortField="intradaymarketcap", sortAsc=False, size=min(max(limit * 2, 25), 250))
    except SystemExit:
        raise
    except Exception as e:  # yfinance는 연결/HTTP/파싱 오류를 다양한 예외 타입으로 던짐
        raise SystemExit(f"ERROR: 스크리너 조회에 실패했습니다 ({e}). 네트워크 상태나 조건 값을 확인하세요.")
    return response.get("quotes", [])


def filter_raw_tickers(raw_tickers: str, exclude_recent: set, exclude_watchlist: set, limit: int) -> list:
    """--tickers 로 받은 콤마 구분 티커 문자열에 로컬 제외 필터만 적용해 남는 티커 목록을 반환."""
    seen = set()
    results = []
    for raw in raw_tickers.split(","):
        ticker = raw.strip().upper()
        if not ticker or ticker in seen or ticker in exclude_recent or ticker in exclude_watchlist:
            continue
        seen.add(ticker)
        results.append(ticker)
        if len(results) >= limit:
            break
    return results


def main() -> int:
    args = parse_args(sys.argv[1:])
    exclude_recent = recently_analyzed_tickers(args.exclude_recent_months)
    exclude_watchlist = load_watchlist_tickers()

    if args.tickers:
        results = filter_raw_tickers(args.tickers, exclude_recent, exclude_watchlist, args.limit)
        if not results:
            print("조건에 맞는 신규 후보 티커가 없습니다 (제외 조건을 완화해 보세요).")
            return 0
        for ticker in results:
            print(ticker)
        return 0

    sectors = [s.strip() for s in args.sectors.split(",") if s.strip()]
    yf, query = build_query(sectors, args.market_cap_min, args.market_cap_max, args.region)
    quotes = run_screen(yf, query, args.limit)

    results = []
    for q in quotes:
        ticker = (q.get("symbol") or "").upper()
        if not ticker or ticker in exclude_recent or ticker in exclude_watchlist:
            continue
        results.append(q)
        if len(results) >= args.limit:
            break

    if not results:
        print("조건에 맞는 신규 후보 티커가 없습니다 (필터 조건을 완화해 보세요).")
        return 0

    print(f"{'TICKER':<8} {'시가총액':>15} {'섹터':<22} 종목명")
    for q in results:
        cap = q.get("marketCap") or q.get("intradaymarketcap") or 0
        print(f"{q.get('symbol', ''):<8} {cap:>15,.0f} {q.get('sector', '-') or '-':<22} {q.get('shortName', '-')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
