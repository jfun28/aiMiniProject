# 시스템 아키텍처 문서

## 🎯 전체 시스템 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                         사용자 실행                              │
│                      python main.py                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                              │
│                   (조율자 & 조정자)                              │
│                                                                  │
│  역할: 4개 전문 에이전트를 Fan-Out/Fan-In 패턴으로 조율         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Fan-Out (병렬 실행)                         │
│                ThreadPoolExecutor로 동시 실행                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬──────────────────┐
        │                  │                  │                  │
        ▼                  ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Survey     │  │   Market     │  │   Policy     │  │   Company    │
│   Agent      │  │   Agent      │  │   Agent      │  │   Agent      │
│              │  │              │  │              │  │              │
│ 여론조사분석  │  │ 시장현황분석  │  │ 정책규제분석  │  │ 기업경쟁분석  │
│              │  │              │  │              │  │              │
│ • 네이버뉴스 │  │ • 글로벌시장 │  │ • 보조금정책 │  │ • Tesla      │
│ • 유튜브댓글 │  │ • 지역별분석 │  │ • 내연기관   │  │ • 현대차     │
│ • 트위터     │  │ • 판매량추이 │  │   규제       │  │ • BYD        │
│              │  │ • 가격트렌드 │  │ • 충전인프라 │  │ • 시장점유율 │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       │                 │                 │                 │
       └─────────────────┴─────────────────┴─────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Fan-In (결과 수집)                          │
│                      4개 AgentResult 통합                        │
│                                                                  │
│  • survey_result   : AgentResult (status, data, summary)        │
│  • market_result   : AgentResult (status, data, summary)        │
│  • policy_result   : AgentResult (status, data, summary)        │
│  • company_result  : AgentResult (status, data, summary)        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Supervisor Agent (검증 & 반환)                      │
│                  SupervisedState 반환                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               Report Generator Agent                             │
│                 (최종 보고서 생성)                                │
│                                                                  │
│  1. 4개 에이전트 결과 추출 및 포맷팅                             │
│  2. LLM을 통한 종합 분석 및 보고서 작성                          │
│  3. Markdown 보고서 생성 및 저장                                 │
│  4. PDF 보고서 생성 (PDFGenerator 사용)                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      최종 리포트 생성                            │
│                                                                  │
│  📄 ev_market_report_YYYYMMDD_HHMMSS.md                         │
│  📄 ev_market_report_YYYYMMDD_HHMMSS.pdf                        │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 상세 데이터 플로우

### 1. 초기화 단계
```
main.py
  ├─ LLM 초기화 (ChatOpenAI)
  ├─ Search Tool 초기화 (TavilySearchResults)
  └─ Query Parameters 설정
      ├─ region: "한국"
      ├─ period: "2024"
      ├─ companies: ["Tesla", "현대차", "BYD"]
      └─ keywords: ["전기차", "전기자동차", "EV"]
```

### 2. Supervisor Agent 실행
```
SupervisorAgent.coordinate(query_params)
  │
  ├─ 4개 전문 에이전트 초기화
  │   ├─ survey_agent = create_survey_agent(llm, search_tool)
  │   ├─ market_agent = create_market_agent(llm)
  │   ├─ policy_agent = create_policy_agent(llm)
  │   └─ company_agent = create_company_agent(llm, search_tool)
  │
  ├─ LangGraph Workflow 구축
  │   ├─ add_node("fan_out", self._fan_out_node)
  │   ├─ add_node("fan_in", self._fan_in_node)
  │   └─ set_entry_point("fan_out") → "fan_in" → END
  │
  └─ Workflow 실행
      └─ 반환: SupervisedState
```

### 3. Fan-Out 노드 (병렬 실행)
```
_fan_out_node(state)
  │
  ├─ ThreadPoolExecutor(max_workers=4) 생성
  │
  ├─ 병렬 작업 제출
  │   ├─ future1 = executor.submit(survey_agent.analyze, query_params)
  │   ├─ future2 = executor.submit(market_agent.analyze, query_params)
  │   ├─ future3 = executor.submit(policy_agent.analyze, query_params)
  │   └─ future4 = executor.submit(company_agent.analyze, query_params)
  │
  └─ 결과 수집 (as_completed)
      ├─ survey_result: AgentResult
      ├─ market_result: AgentResult
      ├─ policy_result: AgentResult
      └─ company_result: AgentResult
```

### 4. 각 에이전트 내부 동작

#### Survey Agent
```
analyze(query_params)
  ├─ LangGraph 워크플로우 실행
  │   ├─ agent_collect: 네이버뉴스, 유튜브, 트위터 데이터 수집
  │   ├─ agent_classify: 이슈 분류 (LLM)
  │   ├─ agent_sentiment: 감정 분석 (LLM)
  │   ├─ agent_trend: 트렌드 해석 (LLM)
  │   └─ agent_report: 보고서 생성 및 PDF 저장
  │
  └─ 반환: AgentResult
      ├─ agent_name: "Survey Agent"
      ├─ status: "success"
      ├─ data: { trend_report }
      └─ summary: "여론조사 결과 요약..."
```

#### Market Agent
```
analyze(query_params)
  ├─ LangGraph 워크플로우 실행
  │   ├─ query_builder: 검색 쿼리 생성 (글로벌, 북미, 유럽, 아시아, 한국)
  │   ├─ tavily_search: Tavily API로 검색 (최대 25개 쿼리)
  │   ├─ llm_analyze: LLM 분석
  │   └─ struct_result: 결과 구조화
  │
  └─ 반환: AgentResult
      ├─ agent_name: "Market Agent"
      ├─ status: "success"
      ├─ data: { executive_summary, global_analysis, korea_analysis, ... }
      └─ summary: "시장 분석 전문..."
```

#### Policy Agent
```
analyze(query_params)
  ├─ 검색 쿼리 생성 (다중 지역 지원)
  ├─ Tavily 검색 (최대 15개 쿼리)
  ├─ LLM 분석 (POLICY_ANALYZE_PROMPT)
  └─ 반환: AgentResult
      ├─ agent_name: "Policy Agent"
      ├─ status: "success"
      ├─ data: { policies, subsidies, regulations, market_impact }
      └─ summary: "정책 분석 전문..."
```

#### Company Agent
```
analyze(query_params)
  ├─ 각 기업별 반복
  │   ├─ 검색 쿼리 생성 (실적, 시장점유율, 뉴스, 주가, 생산량)
  │   ├─ Tavily 검색 (쿼리당 최대 5개 결과)
  │   └─ LLM 분석 (COMPANY_ANALYZE_PROMPT)
  │
  └─ 반환: AgentResult
      ├─ agent_name: "Company Agent"
      ├─ status: "success"
      ├─ data: { companies, reports_count, full_report }
      └─ summary: "기업 분석 요약..."
```

### 5. Fan-In 노드 (결과 통합)
```
_fan_in_node(state)
  ├─ 각 에이전트 결과 검증
  │   ├─ survey_result.status == "success" ? ✅ : ❌
  │   ├─ market_result.status == "success" ? ✅ : ❌
  │   ├─ policy_result.status == "success" ? ✅ : ❌
  │   └─ company_result.status == "success" ? ✅ : ❌
  │
  └─ SupervisedState 업데이트
      ├─ survey_result
      ├─ market_result
      ├─ policy_result
      ├─ company_result
      └─ messages: ["Fan-In 완료: ..."]
```

### 6. Report Generator Agent 실행
```
generate_report(state, output_filename)
  │
  ├─ 1단계: 에이전트 결과 추출 및 포맷팅
  │   ├─ survey_result → survey_text (요약 또는 데이터)
  │   ├─ market_result → market_text
  │   ├─ policy_result → policy_text
  │   └─ company_result → company_text
  │
  ├─ 2단계: LLM 종합 분석 (REPORT_GENERATOR_PROMPT)
  │   ├─ 입력: 4개 에이전트 결과
  │   ├─ LLM 호출: ChatOpenAI + ChatPromptTemplate
  │   └─ 출력: report_markdown (전문 보고서)
  │
  ├─ 3단계: Markdown 파일 저장
  │   └─ outputs/reports/ev_market_report_YYYYMMDD_HHMMSS.md
  │
  ├─ 4단계: PDF 생성 (PDFGenerator)
  │   ├─ markdown_to_pdf(report_markdown, filename, title)
  │   ├─ Markdown 파싱 (헤딩, 리스트, 텍스트)
  │   ├─ ReportLab으로 PDF 빌드
  │   └─ outputs/reports/ev_market_report_YYYYMMDD_HHMMSS.pdf
  │
  └─ 반환: Dict
      ├─ status: "success"
      ├─ report_markdown: "전체 보고서..."
      ├─ markdown_path: "파일 경로"
      └─ pdf_path: "PDF 경로"
```

## 📊 상태 관리 (State)

### SupervisedState
```python
{
    # 입력 파라미터
    "query_params": {
        "region": "한국",
        "period": "2024",
        "companies": ["Tesla", "현대차", "BYD"],
        "keywords": ["전기차", "전기자동차"]
    },
    
    # 에이전트 결과
    "survey_result": AgentResult(...),
    "market_result": AgentResult(...),
    "policy_result": AgentResult(...),
    "company_result": AgentResult(...),
    
    # 최종 결과
    "final_report": None,  # Report Generator가 채움
    
    # 로그
    "messages": [
        "[timestamp] Fan-Out 완료: 4개 에이전트 실행",
        "[timestamp] Fan-In 완료: Survey 성공, Market 성공, ..."
    ]
}
```

### AgentResult
```python
@dataclass
class AgentResult:
    agent_name: str           # "Survey Agent"
    status: str               # "success" | "failed" | "in_progress"
    data: Dict                # 구조화된 데이터
    summary: str              # 요약 (LLM이 생성한 전문)
    timestamp: datetime       # 실행 시간
    error_message: Optional[str] = None  # 오류 메시지
```

## 🔧 기술 스택 및 라이브러리

### 핵심 프레임워크
- **LangGraph**: 워크플로우 오케스트레이션 (StateGraph, 노드/엣지 관리)
- **LangChain**: LLM 통합 (ChatOpenAI, ChatPromptTemplate, Tools)

### LLM 및 도구
- **OpenAI GPT-4o-mini**: 자연어 분석, 생성, 분류, 감정 분석
- **Tavily API**: 실시간 웹 검색 (TavilySearchResults)

### 데이터 수집
- **YouTube API**: 댓글 수집 (googleapiclient)
- **Twitter API v2**: 트윗 수집 (tweepy)
- **LLM 데이터 생성**: API 실패 시 LLM이 현실적인 샘플 생성

### 보고서 생성
- **ReportLab**: PDF 생성 (SimpleDocTemplate, Paragraph, Table)
- **Markdown**: 중간 포맷 (텍스트 파일로도 저장)

### 병렬 처리
- **ThreadPoolExecutor**: 4개 에이전트 동시 실행 (concurrent.futures)

## 📈 성능 최적화

### 1. 병렬 실행
- Supervisor Agent가 4개 에이전트를 **동시에** 실행 (ThreadPoolExecutor)
- 예상 시간 단축: 직렬 실행 대비 **약 70% 감소**

### 2. API 호출 최적화
- 검색 쿼리 수 제한 (Survey: 15개, Market: 15개, Policy: 15개)
- Tavily API max_results 최적화 (3-5개)

### 3. 캐싱 및 재사용
- LLM 인스턴스 재사용 (초기화 1회)
- 검색 결과 중복 제거

## 🎓 핵심 디자인 패턴

### 1. Fan-Out/Fan-In 패턴
- **Fan-Out**: 하나의 작업을 여러 하위 작업으로 분산
- **Fan-In**: 여러 하위 작업의 결과를 하나로 통합
- **장점**: 병렬성 극대화, 각 에이전트 독립성 보장

### 2. Agent Factory 패턴
- 각 에이전트를 `create_xxx_agent()` 팩토리 함수로 생성
- 의존성 주입 (LLM, search_tool 전달)
- **장점**: 테스트 용이, 유연한 구성

### 3. State 관리 패턴
- 불변 상태 전달 (각 노드가 새로운 상태 반환)
- TypedDict 사용 (타입 안전성)
- **장점**: 디버깅 용이, 상태 추적 가능

### 4. Pipeline 패턴
- Survey Agent 내부: collect → classify → sentiment → trend → report
- Report Generator: extract → analyze → format → generate
- **장점**: 각 단계 독립적, 오류 격리

## 🚀 확장 가능성

### 추가 가능한 에이전트
- **Financial Agent**: 재무 분석 (주가, 투자 지표)
- **Technology Agent**: 기술 트렌드 분석 (배터리, 자율주행)
- **Supply Chain Agent**: 공급망 분석 (원자재, 물류)

### 추가 가능한 데이터 소스
- Reddit, LinkedIn, GitHub Issues
- 기업 공시, IR 자료
- 특허 데이터, 논문

### 고급 기능
- 실시간 스트리밍 (결과를 점진적으로 표시)
- 웹 대시보드 (Streamlit, Gradio)
- 이메일 자동 발송
- 정기 실행 (스케줄링)

## 🧪 테스트 전략

### 단위 테스트
- 각 에이전트 독립 실행 (`python agents/surveyAgent.py`)
- 팩토리 함수 테스트

### 통합 테스트
- Supervisor Agent 테스트 (4개 에이전트 조율)
- Report Generator 테스트 (더미 데이터 사용)

### 전체 시스템 테스트
- `python main.py` 실행
- 실제 API 호출 및 PDF 생성 확인

---

**작성일**: 2024-10-23
**버전**: 1.0

