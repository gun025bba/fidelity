#!/bin/bash
#
# 디스패처: watchlist.txt에서 오늘 아직 분석하지 않은 다음 티커를 골라 analyze.sh에 넘긴다.
# launchd로 스케줄링 (~/Library/LaunchAgents/com.fidelity.analyze.plist)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WATCHLIST="${SCRIPT_DIR}/data/watchlist.txt"
REPORTS_DIR="${SCRIPT_DIR}/reports"
TODAY=$(date +"%Y%m%d")
LOG_PREFIX="[$(date '+%Y-%m-%d %H:%M:%S')]"

# PATH 설정 (launchd 환경에서 claude, jq 등을 찾기 위함)
export PATH="$HOME/.local/bin:/usr/local/bin:/opt/homebrew/bin:$HOME/.npm-global/bin:$HOME/.claude/local:$PATH"

echo "${LOG_PREFIX} === 디스패치 시작 ==="

# watchlist 존재 확인
if [[ ! -f "${WATCHLIST}" ]]; then
    echo "${LOG_PREFIX} ERROR: watchlist 파일 없음: ${WATCHLIST}"
    exit 1
fi

# 오늘 아직 분석 안 한 첫 번째 티커 찾기
NEXT_TICKER=""
while IFS= read -r line; do
    # 주석, 빈줄 건너뛰기
    line=$(echo "$line" | sed 's/#.*//' | xargs)
    [[ -z "$line" ]] && continue

    TICKER=$(echo "$line" | tr '[:lower:]' '[:upper:]')
    REPORT="${REPORTS_DIR}/${TICKER}/${TICKER}_${TODAY}.md"

    if [[ ! -f "${REPORT}" ]]; then
        NEXT_TICKER="${TICKER}"
        break
    fi
done < "${WATCHLIST}"

# 분석할 티커가 없으면 종료
if [[ -z "${NEXT_TICKER}" ]]; then
    echo "${LOG_PREFIX} 오늘의 모든 티커 분석 완료. 건너뜁니다."
    exit 0
fi

echo "${LOG_PREFIX} 분석 대상: ${NEXT_TICKER}"

# analyze.sh 실행
"${SCRIPT_DIR}/analyze.sh" "${NEXT_TICKER}"
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    echo "${LOG_PREFIX} ${NEXT_TICKER} 분석 성공"
elif [[ $EXIT_CODE -eq 2 ]]; then
    echo "${LOG_PREFIX} ${NEXT_TICKER} 토큰 한도 초과로 중단"
else
    echo "${LOG_PREFIX} ${NEXT_TICKER} 분석 실패 (exit: ${EXIT_CODE})"
fi

echo "${LOG_PREFIX} === 디스패치 종료 ==="
