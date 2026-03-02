#!/bin/bash
#
# 피터 린치 AI 투자 분석 시스템
# Usage: ./analyze.sh <TICKER>
# Example: ./analyze.sh AAPL
#

set -euo pipefail

# ============================================================
# 설정
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="${SCRIPT_DIR}/reports"
DATA_DIR="${SCRIPT_DIR}/data"
TIMESTAMP=$(date +"%Y%m%d")

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================
# 유틸리티 함수
# ============================================================
print_banner() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║                                                       ║"
    echo "║   🎯 피터 린치 AI 투자 분석 시스템                    ║"
    echo "║   Peter Lynch AI Investment Analyst                   ║"
    echo "║                                                       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}


# ============================================================
# 사전 체크
# ============================================================
check_prerequisites() {
    # Claude Code 설치 확인
    if ! command -v claude &> /dev/null; then
        print_error "Claude Code가 설치되어 있지 않습니다."
        echo "설치: npm install -g @anthropic-ai/claude-code"
        exit 1
    fi

    # jq 설치 확인
    if ! command -v jq &> /dev/null; then
        print_error "jq가 설치되어 있지 않습니다."
        echo "설치: brew install jq"
        exit 1
    fi

    # 디렉토리 생성
    mkdir -p "${REPORTS_DIR}" "${DATA_DIR}"
}

# ============================================================
# 메인 로직
# ============================================================
main() {
    # 인자 체크
    if [ $# -eq 0 ]; then
        print_error "티커 심볼을 입력해주세요."
        echo ""
        echo "사용법: $0 <TICKER>"
        echo "예시:   $0 AAPL"
        echo "        $0 NVDA"
        echo "        $0 MSFT"
        echo ""
        echo "환경 변수:"
        echo "  WEEKLY_TOKEN_LIMIT=88000    주간 토큰 한도 (기본: 88000)"
        echo "  USAGE_THRESHOLD=70          실행 제한 임계값 % (기본: 70)"
        exit 1
    fi

    local TICKER
    TICKER=$(echo "$1" | tr '[:lower:]' '[:upper:]')  # 대문자 변환
    local TICKER_DIR="${REPORTS_DIR}/${TICKER}"
    local REPORT_FILE="${TICKER_DIR}/${TICKER}_${TIMESTAMP}.md"

    print_banner
    check_prerequisites

    print_info "분석 대상: ${TICKER}"
    print_info "보고서 출력: ${REPORT_FILE}"
    print_info "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # ============================================================
    # Claude Code 실행 - 메인 에이전트
    # ============================================================
    # 티커별 디렉토리 생성
    mkdir -p "${TICKER_DIR}"

    print_step "Claude Code 메인 에이전트를 시작합니다..."
    echo ""

    cd "${SCRIPT_DIR}"

    # Claude Code 실행
    claude --print \
        --model opus \
        --allowedTools "Task,WebFetch,Read,Write,Bash,Glob,Grep" \
        --verbose \
        "다음 티커를 분석해주세요: ${TICKER}

CLAUDE.md의 메인 에이전트 오케스트레이션 규칙을 정확히 따라주세요.

실행 단계:
1. 먼저 ${TICKER}의 기본 정보(회사명, 섹터, 현재 주가, 시가총액)를 웹 검색으로 확인
2. 6개 서브 에이전트를 병렬(parallel)로 실행하여 각 영역 분석 수행:
   - financial-analyst: 재무제표 분석
   - business-analyst: 사업 모델 분석
   - growth-analyst: 성장성/미래 비전 분석
   - industry-analyst: 산업/경쟁 분석
   - sentiment-analyst: 뉴스/센티먼트 분석
   - valuation-analyst: 밸류에이션 분석
3. 모든 서브 에이전트 결과를 종합
4. 피터 린치의 6가지 분류 중 해당 카테고리 결정
5. 나의 투자 철학과의 적합성 평가
6. 최종 투자 의견 및 종합 점수 도출
7. 보고서를 ${REPORT_FILE}에 마크다운 파일로 저장

보고서는 반드시 CLAUDE.md에 명시된 형식을 따라야 합니다."

    # ============================================================
    # 결과 확인
    # ============================================================
    echo ""
    if [ -f "${REPORT_FILE}" ]; then
        print_success "분석 완료!"
        print_success "보고서: ${REPORT_FILE}"
        print_info "완료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo -e "${GREEN}보고서 미리보기 (상위 30줄):${NC}"
        echo "────────────────────────────────────────"
        head -30 "${REPORT_FILE}"
        echo "────────────────────────────────────────"
        echo ""
        print_info "전체 보고서: cat ${REPORT_FILE}"
    else
        print_error "보고서 파일이 생성되지 않았습니다."
        print_info "Claude Code 로그를 확인해주세요."
        exit 1
    fi
}

# ============================================================
# 실행
# ============================================================
main "$@"
