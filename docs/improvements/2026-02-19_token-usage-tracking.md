# 토큰 사용량 추적 개선 사항

**작성일**: 2026-02-19
**최종 수정**: 2026-03-02
**현재 상태**: 로직 제거됨 — 비정상 동작으로 인해 `analyze.sh`에서 삭제
**관련 파일**: `analyze.sh`

---

## 현재 구현 방식

- 분석 완료 후 `data/usage_log.jsonl`에 토큰 사용량 기록
- 다음 실행 전 이번 주(월~일) 누적량 합산하여 체크
- 임계값(기본 70%) 초과 시 실행 차단
- `claude --output-format json`으로 토큰 수 파싱 시도, 실패 시 추정치(50k) 사용

## 한계점

1. **토큰 수 부정확**: JSON 출력에서 토큰 수를 정확히 파싱 못할 수 있어 추정치 대체
2. **분석 외 사용 미추적**: 일반 대화, 코딩 작업 등의 토큰 소비량은 추적 안 됨
3. **수동 한도 설정**: `WEEKLY_TOKEN_LIMIT`을 플랜에 맞게 직접 설정해야 함
4. **서브 에이전트 토큰 미집계**: 6개 서브 에이전트의 개별 토큰 사용량이 메인 에이전트 JSON에 포함되는지 미확인

## 개선 방안 (우선순위순)

### 1. Anthropic Admin API 연동
- `GET /v1/organizations/usage_report/messages`로 실제 사용량 조회
- 필요: Admin API 키 (`sk-ant-admin-...`)
- 장점: 가장 정확, 모든 사용량(분석 외 포함) 반영
- 단점: 조직 계정 필요, API 키 관리

### 2. `claude --output-format json` 파싱 정확도 개선
- JSON 응답 스키마를 정확히 파악하여 파싱 로직 보완
- `input_tokens`, `output_tokens` 필드 위치 확인
- 서브 에이전트 포함 여부 확인

### 3. OpenTelemetry 기반 모니터링
- `CLAUDE_CODE_ENABLE_TELEMETRY=1` 환경변수로 활성화
- `claude_code.token.usage` 메트릭 파싱
- 별도 collector 프로세스 필요 → 복잡도 높음

### 4. `/cost` 또는 `/stats` 세션 데이터 활용
- Claude Code 인터랙티브 모드에서만 사용 가능
- `--print` 모드에서는 사용 불가 → 스크립트 자동화에 부적합

## 제거 이력 (2026-03-02)

- `analyze.sh`의 `get_week_start()`, `check_weekly_usage()`, `enforce_usage_limit()`, `log_usage()` 함수 전체 제거
- 주간 토큰 한도 관련 환경변수(`WEEKLY_TOKEN_LIMIT`, `USAGE_THRESHOLD`) 제거
- `data/usage_log.jsonl` 기록 중단
- **제거 이유**: 추정치 기반으로 실제 사용량을 반영하지 못하고, 서브 에이전트 토큰 미집계 등으로 밸리데이션 자체가 의미 없다고 판단

## 비고

- 재구현 시 Anthropic Admin API 연동(우선순위 1번)이 유일하게 신뢰할 수 있는 방법
- 그 전까지는 claude.ai 웹에서 수동으로 사용량 확인
