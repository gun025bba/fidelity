# 🎯 피터 린치 AI 투자 분석 시스템

Claude Code 기반 멀티 에이전트 투자 분석 시스템입니다.  
피터 린치의 투자 철학을 기반으로 6개의 전문 AI 에이전트가 병렬로 종목을 분석합니다.

## 아키텍처

```
analyze.sh → Claude Code (메인 에이전트, Opus)
                    ↓ 병렬 디스패치
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Financial│ │ Business │ │  Growth  │
│ Analyst  │ │ Analyst  │ │ Analyst  │
│ (Sonnet) │ │ (Sonnet) │ │ (Sonnet) │
└──────────┘ └──────────┘ └──────────┘
    ↓               ↓               ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Industry │ │Sentiment │ │Valuation │
│ Analyst  │ │ Analyst  │ │ Analyst  │
│ (Sonnet) │ │ (Sonnet) │ │ (Sonnet) │
└──────────┘ └──────────┘ └──────────┘
                    ↓
          메인 에이전트 종합
                    ↓
        reports/{TICKER}_{DATE}.md
```

## 사전 요구사항

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 설치
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
- Anthropic API 키 설정 또는 Claude Max 플랜

## 사용법

### 기본 사용
```bash
./analyze.sh AAPL      # Apple 분석
./analyze.sh NVDA      # NVIDIA 분석
./analyze.sh MSFT      # Microsoft 분석
```

### Claude Code 내부에서 사용
```
/analyze AAPL
```

### 보고서 확인
```bash
ls reports/                     # 보고서 목록
cat reports/AAPL_20260219.md    # 보고서 열기
```

## 서브 에이전트 구성

| 에이전트 | 역할 | 핵심 분석 |
|---------|------|----------|
| `financial-analyst` | 재무제표 분석 | PL, BS, CF, ROE, 부채비율, FCF |
| `business-analyst` | 사업 모델 분석 | 수익 구조, Moat, 경영진, 30초 테스트 |
| `growth-analyst` | 성장성 분석 | TAM, 성장 동력, R&D, 텐배거 가능성 |
| `industry-analyst` | 산업/경쟁 분석 | Porter's 5 Forces, 경쟁사 비교, 시장 포지션 |
| `sentiment-analyst` | 센티먼트 분석 | 뉴스, 애널리스트 의견, 내부자 거래 |
| `valuation-analyst` | 밸류에이션 분석 | PEG, DCF, 상대/절대 가치, 적정 주가 |

## 커스터마이즈

### 투자 철학 수정
`CLAUDE.md`의 "나의 투자 철학" 섹션을 자신의 투자 성향에 맞게 수정하세요.

### 에이전트 튜닝
`.claude/agents/` 디렉토리의 각 에이전트 파일을 수정하여 분석 기준을 조정할 수 있습니다.

## 프로젝트 구조

```
peter-lynch-analyst/
├── CLAUDE.md                        # 메인 에이전트 설정 + 투자 철학
├── analyze.sh                       # 실행 스크립트
├── README.md                        # 이 파일
├── .claude/
│   ├── agents/
│   │   ├── financial-analyst.md     # 재무제표 분석가
│   │   ├── business-analyst.md      # 사업 모델 분석가
│   │   ├── growth-analyst.md        # 성장성 분석가
│   │   ├── industry-analyst.md      # 산업/경쟁 분석가
│   │   ├── sentiment-analyst.md     # 센티먼트 분석가
│   │   └── valuation-analyst.md     # 밸류에이션 분석가
│   └── commands/
│       └── analyze.md               # /analyze 슬래시 커맨드
├── reports/                         # 분석 보고서 출력
└── data/                            # 캐시/임시 데이터
```

## Phase 2 계획 (향후)
- [ ] MCP 서버 연동 (실시간 시세 데이터)
- [ ] 포트폴리오 트래커 연동
- [ ] 자동 스케줄링 (주기적 재분석)
- [ ] 비교 분석 모드 (2개 이상 종목 비교)
- [ ] 한국 주식 (KRX) 지원
