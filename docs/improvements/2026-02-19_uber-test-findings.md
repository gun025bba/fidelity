# UBER 분석 테스트 결과 개선 사항

**테스트 일자**: 2026-02-19
**분석 대상**: UBER (Uber Technologies, Inc.)
**테스트 유형**: 전체 파이프라인 실행 (6개 서브 에이전트 병렬)

---

## 발견된 문제점

### 1. WebFetch 403/404 에러로 인한 에이전트 지연
**심각도**: 높음

서브 에이전트들이 WebFetch로 재무 데이터 사이트에 접근할 때 대부분 403/404 에러가 발생했다.
에이전트들이 실패한 소스를 반복적으로 재시도하면서 tool call 횟수가 90회 이상으로 증가.

**영향받은 에이전트**:
- business-analyst: 91 tool calls
- industry-analyst: 93 tool calls
- sentiment-analyst: 92 tool calls

**접근 실패한 사이트들**:
- Motley Fool (403)
- Finviz (403)
- SEC EDGAR (일부 404)
- Macrotrends (403)
- MarketBeat (403)
- WSJ (403)
- TheVerge (403)
- Axios (403)

### 2. TaskOutput 첫 번째 수집 시 타임아웃
**심각도**: 중간

일부 에이전트(business, industry, sentiment)가 300초 타임아웃 내에 완료되지 않았다.
두 번째 TaskOutput 호출로 결과를 수집할 수 있었지만, 대기 시간이 길었다.

### 3. reports/ 디렉토리 미존재
**심각도**: 낮음

보고서 작성 시 reports/ 디렉토리가 없어서 별도로 생성해야 했다.

---

## 개선 방안

### 개선 1: WebSearch 우선 가이드라인 추가
**적용 대상**: 모든 서브 에이전트 프롬프트

각 에이전트의 `.md` 파일에 다음 지침 추가:
```
## 데이터 수집 규칙
1. **WebSearch를 최우선 수단으로 사용**하여 정보를 수집하라
2. WebFetch는 WebSearch로 찾은 확실히 접근 가능한 URL에만 사용
3. WebFetch에서 403/404 에러 발생 시 즉시 해당 소스를 포기하고 WebSearch로 전환
4. 동일 소스에 대한 재시도는 최대 1회로 제한
```

### 개선 2: 접근 가능한 데이터 소스 화이트리스트
**적용 대상**: 에이전트 프롬프트 또는 CLAUDE.md

WebFetch로 접근이 확인된 사이트 목록 제공:
```
## 접근 가능한 데이터 소스 (WebFetch 화이트리스트)
- Yahoo Finance (일부 페이지)
- StockAnalysis.com
- Wikipedia
- 공식 기업 IR 페이지 (일부)

## 접근 불가능한 사이트 (블랙리스트)
- Motley Fool, Finviz, MarketBeat, WSJ, Macrotrends
→ 이 사이트들은 WebSearch로만 정보 검색
```

### 개선 3: max_turns 설정으로 무한 루프 방지
**적용 대상**: 메인 에이전트의 Task 호출 시

```
Task(
  subagent_type: "financial-analyst",
  max_turns: 30,  # 에이전트 당 최대 30턴 제한
  ...
)
```

30턴이면 충분한 분석이 가능하면서도 무한 재시도를 방지할 수 있다.

### 개선 4: reports/ 디렉토리 사전 생성
**적용 대상**: 프로젝트 초기 설정 또는 analyze.sh

analyze.sh에 이미 `mkdir -p` 명령이 있지만, `/analyze` 슬래시 커맨드로 실행할 때도
메인 에이전트가 보고서 작성 전에 디렉토리를 확인/생성하도록 지침 추가.

### 개선 5: 에이전트에 WebSearch 도구 추가
**적용 대상**: 모든 서브 에이전트의 tools 목록

현재 에이전트 도구 목록에 WebSearch가 없음. 추가 필요:
```yaml
tools:
  - WebFetch
  - WebSearch  # 추가
  - Read
  - Write
  - Grep
```

---

## 성공 사항

- 6개 에이전트 병렬 실행 자체는 정상 동작
- 모든 에이전트가 최종적으로 분석 결과를 반환
- 보고서 통합 및 생성 프로세스 정상 작동
- 피터 린치 프레임워크 적용이 각 에이전트에서 잘 반영됨
- 최종 보고서(reports/UBER_20260219.md) 11개 섹션 모두 생성 완료

---

## 다음 단계

1. [ ] 위 개선 방안을 에이전트 프롬프트에 적용
2. [ ] 개선 후 UBER 또는 다른 티커로 재테스트
3. [ ] 실행 시간 및 tool call 횟수 비교 측정
