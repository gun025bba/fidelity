#!/usr/bin/env python3
"""
분석 기록 인덱스 관리 (이슈 #5)

reports/ 디렉토리를 매번 전수 스캔하지 않고도 "기 분석 티커 + 최근 분석일"을
빠르게 조회하기 위한 경량 인덱스를 관리한다.

인덱스 파일: data/analysis_index.txt
형식 (한 줄에 하나, 티커 알파벳순 정렬):
    TICKER: YYYY-MM-DD

사용법:
    analysis_index.py update <TICKER> [YYYYMMDD|YYYY-MM-DD]   # 단건 upsert (날짜 생략 시 오늘)
    analysis_index.py backfill                                # reports/ 전체 스캔하여 인덱스 재생성
    analysis_index.py get <TICKER>                            # 해당 티커 최근 분석일 출력 (없으면 빈 출력)
    analysis_index.py list                                    # 전체 인덱스 출력

분석 플로우 마지막 단계(analyze.sh / /analyze)에서 `update`를 호출하여
인덱스를 갱신한다. 그러면 다음 티커 선정 시 reports/ 스캔이 불필요해진다.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"
INDEX_FILE = DATA_DIR / "analysis_index.txt"

# reports 파일명에서 날짜 추출: TICKER_YYYYMMDD.md
REPORT_DATE_RE = re.compile(r"_(\d{8})\.md$")
# 인덱스 한 줄 파싱: "TICKER: YYYY-MM-DD"
INDEX_LINE_RE = re.compile(r"^([A-Za-z0-9.\-]+)\s*:\s*(\d{4}-\d{2}-\d{2})\s*$")


def parse_date(s: str) -> str:
    """YYYYMMDD 또는 YYYY-MM-DD 입력을 정규화된 YYYY-MM-DD 문자열로 변환."""
    s = s.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"날짜 형식이 올바르지 않습니다 (YYYYMMDD 또는 YYYY-MM-DD): {s!r}")


def load_index() -> dict:
    """인덱스 파일을 {TICKER: 'YYYY-MM-DD'} 딕셔너리로 로드."""
    index = {}
    if not INDEX_FILE.exists():
        return index
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = INDEX_LINE_RE.match(line)
            if m:
                index[m.group(1).upper()] = m.group(2)
    return index


def save_index(index: dict) -> None:
    """딕셔너리를 티커 알파벳순으로 정렬하여 인덱스 파일에 저장."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"{ticker}: {index[ticker]}" for ticker in sorted(index)]
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write("# 분석 기록 인덱스 (이슈 #5) — TICKER: 최근분석일(YYYY-MM-DD)\n")
        f.write("# analysis_index.py 로 자동 갱신됨. 직접 편집하지 마세요.\n")
        for line in lines:
            f.write(line + "\n")


def scan_reports() -> dict:
    """reports/ 디렉토리를 스캔하여 티커별 최근 분석일을 수집."""
    index = {}
    if not REPORTS_DIR.exists():
        return index
    for ticker_dir in REPORTS_DIR.iterdir():
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name.upper()
        latest = None
        for report in ticker_dir.glob(f"{ticker_dir.name}_*.md"):
            m = REPORT_DATE_RE.search(report.name)
            if not m:
                continue
            try:
                d = datetime.strptime(m.group(1), "%Y%m%d")
            except ValueError:
                continue
            if latest is None or d > latest:
                latest = d
        if latest is not None:
            index[ticker] = latest.strftime("%Y-%m-%d")
    return index


def cmd_update(args) -> int:
    if not args:
        print("ERROR: update 에는 티커가 필요합니다.", file=sys.stderr)
        return 1
    ticker = args[0].upper()
    date_str = parse_date(args[1]) if len(args) > 1 else datetime.now().strftime("%Y-%m-%d")

    index = load_index()
    # 더 최신 날짜만 반영 (이전 보고서 재실행이 최근 분석일을 되돌리지 않도록)
    existing = index.get(ticker)
    if existing is None or date_str > existing:
        index[ticker] = date_str
    save_index(index)
    print(f"{ticker}: {index[ticker]}")
    return 0


def cmd_backfill(_args) -> int:
    scanned = scan_reports()
    save_index(scanned)
    print(f"백필 완료: {len(scanned)}개 티커가 인덱스에 기록되었습니다 → {INDEX_FILE}")
    return 0


def cmd_get(args) -> int:
    if not args:
        print("ERROR: get 에는 티커가 필요합니다.", file=sys.stderr)
        return 1
    index = load_index()
    date_str = index.get(args[0].upper())
    if date_str:
        print(date_str)
        return 0
    return 0  # 없으면 빈 출력, 정상 종료


def cmd_list(_args) -> int:
    index = load_index()
    for ticker in sorted(index):
        print(f"{ticker}: {index[ticker]}")
    return 0


COMMANDS = {
    "update": cmd_update,
    "backfill": cmd_backfill,
    "get": cmd_get,
    "list": cmd_list,
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        return 1
    return COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
