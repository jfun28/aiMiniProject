# Supervisor Agent 업그레이드 가이드

## 🎯 주요 개선사항

기존의 단순한 Fan-Out/Fan-In 구조에서 **지능형 에이전트 선택 및 품질 검증** 기능이 추가되었습니다.

## 📊 아키텍처 비교

### 새 버전 (지능형 라우팅)
```
[시작] 
  ↓
[Decision: LLM이 필요한 에이전트 선택]
  ↓
[Fan-Out: 선택된 에이전트만 병렬 실행]
  ↓
[Quality Check: 결과 품질 검증]
  ↓
[품질 불충분?] → YES → [재시도] (최대 2회)
  ↓ NO
[Fan-In: 최종 결과 통합]
  ↓
[종료]
```

## 🚀 새로운 기능

### 1. 지능형 에이전트 선택 (`_supervisor_decision_node`)

**기능:**
- LLM이 쿼리 파라미터를 분석하여 필요한 에이전트만 선택
- 불필요한 에이전트 실행을 방지하여 비용 절감 및 속도 향상

**예시:**
```python
# 쿼리: "Tesla의 2024년 재무 상태 분석"
# 선택된 에이전트: ["company"]  # company만 실행

# 쿼리: "전기차 시장 전반 분석"
# 선택된 에이전트: ["survey", "market", "policy", "company"]  # 모두 실행
```

**동작 방식:**
```python
def _supervisor_decision_node(self, state):
    """
    쿼리 분석:
    - 지역: 한국
    - 기간: 2024
    - 기업: ["Tesla"]
    - 키워드: ["재무", "실적"]
    
    → LLM 판단: company 에이전트만 필요
    """
```

### 2. 품질 검증 및 자동 재시도 (`_quality_check_node`)

**검증 기준:**
- ✅ 상태가 "success"인가?
- ✅ 요약이 최소 100자 이상인가?
- ✅ 데이터가 최소 50자 이상인가?
- ✅ 에러 메시지가 없는가?

**재시도 로직:**
- 품질이 기준 미달인 에이전트만 재실행
- 최대 2회까지 재시도
- 재시도 횟수 초과 시 현재 결과로 진행

**예시 출력:**
```
[Supervisor Agent] Quality Check: 결과 품질 검증
================================================================================
   ✅ 여론조사: 품질 양호 (요약 450자, 데이터 1234자)
   ⚠️  시장분석: 요약 너무 짧음 (45자), 데이터 부족 (30자)
   ✅ 정책분석: 품질 양호 (요약 380자, 데이터 890자)
   ❌ 기업분석: 결과 없음

   🔄 재시도 필요: market, company (시도 1/2)
```

### 3. 조건부 라우팅 (`_should_continue`)

**기능:**
- Quality Check 결과에 따라 자동으로 경로 선택
- 재시도가 필요하면 `fan_out`으로 복귀
- 품질이 양호하면 `fan_in`으로 진행

## 📝 State 구조 변경

```python
class SupervisedState(TypedDict):
    # 기존 필드
    query_params: Dict
    survey_result: Optional[AgentResult]
    market_result: Optional[AgentResult]
    policy_result: Optional[AgentResult]
    company_result: Optional[AgentResult]
    final_report: Optional[str]
    messages: List[str]
    
    # 새로 추가된 제어 필드
    selected_agents: List[str]      # 실행할 에이전트 목록
    retry_agents: List[str]         # 재실행이 필요한 에이전트
    should_continue: bool           # 재실행 여부
    retry_count: int                # 재시도 횟수 (무한 루프 방지)
```

## 🎓 사용 예시

### 예시 1: 특정 기업 분석 (효율적 실행)
```python
query_params = {
    "region": "미국",
    "period": "2024",
    "companies": ["Tesla"],
    "keywords": ["재무", "실적"]
}

# 실행 결과:
# ✅ Decision: company 에이전트만 선택
# ✅ Fan-Out: 1개 에이전트 실행 (75% 비용 절감!)
# ✅ Quality Check: 품질 양호
# ✅ Fan-In: 완료
```

### 예시 2: 종합 시장 분석 (전체 실행)
```python
query_params = {
    "region": "한국",
    "period": "2024",
    "companies": ["Tesla", "현대차", "BYD"],
    "keywords": ["전기차", "전기자동차"]
}

# 실행 결과:
# ✅ Decision: 4개 에이전트 모두 선택
# ✅ Fan-Out: 4개 에이전트 병렬 실행
# ⚠️  Quality Check: market 에이전트 재시도 필요
# 🔄 Fan-Out: market 에이전트 재실행
# ✅ Quality Check: 모든 결과 양호
# ✅ Fan-In: 완료
```

## 🔧 커스터마이징

### 품질 기준 조정
```python
# agents/supervisorAgent.py 파일의 _quality_check_node 메서드

MIN_SUMMARY_LENGTH = 100  # 최소 요약 길이 (기본: 100자)
MIN_DATA_SIZE = 50        # 최소 데이터 크기 (기본: 50자)
max_retry = 2             # 최대 재시도 횟수 (기본: 2회)
```

### Decision 프롬프트 수정
```python
# agents/supervisorAgent.py 파일의 _supervisor_decision_node 메서드
# prompt 변수의 system 메시지를 수정하여 선택 로직 변경 가능
```

## 📈 성능 개선

| 항목 | 이전 | 개선 후 | 향상도 |
|------|------|---------|--------|
| 불필요한 에이전트 실행 | 항상 4개 실행 | 필요한 것만 실행 | 최대 75% 절감 |
| 품질 검증 | 없음 | 자동 검증 + 재시도 | 신뢰성 향상 |
| 실패 처리 | 수동 재실행 | 자동 재시도 | 안정성 향상 |
| 비용 효율성 | 낮음 | 높음 | API 호출 최적화 |



