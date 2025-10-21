# 전기차 시장 트렌드 분석 Multi-Agent 시스템

본 프로젝트는 전기차 시장을 다각도로 분석하는 Multi-Agent 시스템을 설계하고 구현한 실습 프로젝트입니다.

## Overview

- **Objective**: 전기차 시장의 여론, 시장 현황, 정책, 기업 펀더멘탈, 주가를 종합 분석하여 투자 인사이트 제공
- **Methods**: Fan-out/Fan-in Pattern, Sequential Processing, LLM-based Analysis
- **Tools**: LangGraph, tavily, Financial Data APIs, News Aggregation

## Features

- **멀티 에이전트 병렬 처리**: 여론조사, 시장, 정책, 기업 분석을 동시 실행하여 효율성 극대화
- **순차적 의존성 관리**: 기업 펀더멘탈 분석 결과를 기반으로 주가 밸류에이션 분석 수행
- **종합 리포트 생성**: 5개 에이전트의 분석 결과를 통합하여 실행 가능한 투자 인사이트 도출

## Tech Stack

| Category   | Details                      |
|------------|------------------------------|
| Framework  | LangGraph, LangChain, Python |
| LLM        | GPT-4o-mini via OpenAI API   |
| Data Source| tavily, duckduckgo           |
| Financial  | yfinance, csv  |
| Visualization | Matplotlib, Plotly       |

## Agents

### Phase 1: 병렬 실행 에이전트

- **Survey Agent**: 소비자 여론 및 구매 의향 조사 (소셜미디어, 설문조사 데이터 분석)
- **Market Agent**: 판매량, 시장 점유율, 가격 트렌드 분석 (공식 통계, 산업 리포트 수집)
- **Policy Agent**: 정책 변화, 보조금, 규제 분석 (정부 공시, 법안 추적)
- **Company Agent**: 기업 재무제표, R&D 투자, 생산 능력 분석 (재무제표, 공시자료 분석)

### Phase 2: 순차 실행 에이전트

- **Stock Agent**: 주가 분석 및 밸류에이션 평가 (기업 분석 결과 + 주가 데이터 결합)

## State

```python
class SupervisedState(TypedDict):
    # 입력 파라미터
    query_params: Dict  # 분석 기간, 대상 지역, 관심 기업 등
    
    # Phase 1 에이전트 결과
    survey_result: AgentResult | None     # 여론조사 분석 결과
    market_result: AgentResult | None     # 시장 분석 결과
    policy_result: AgentResult | None     # 정책 분석 결과
    company_result: AgentResult | None    # 기업 분석 결과
    
    # Phase 2 에이전트 결과
    stock_result: AgentResult | None      # 주가 분석 결과
    
    # 최종 결과물
    final_report: str | None              # 종합 분석 리포트
    
    # 로그
    messages: List[str]                   # 실행 로그 (디버깅용)
```

## Architecture

![alt text](<전기차 flow_v0.1.png>)

### Workflow 설명

1. **Supervisor**: 전체 워크플로우 시작 및 Phase 1 에이전트 호출
2. **Phase 1 Fan-out**: 4개 에이전트가 병렬로 독립적 분석 수행
3. **Phase 1 Aggregator**: 4개 에이전트 결과 수집 및 검증
4. **Phase 2**: 기업 분석 결과를 활용하여 주가 밸류에이션 분석
5. **Final Aggregator**: 전체 결과 통합
6. **Report Generator**: LLM 기반 종합 리포트 작성

## Directory Structure

```
ev-market-analysis/
├── data/                       # 데이터 저장소
│   ├── raw/                   # 원본 데이터 (CSV, JSON)
│   └── processed/             # 전처리된 데이터
├── agents/                     # 에이전트 모듈
│   ├── survey_agent.py        # 여론조사 분석
│   ├── market_agent.py        # 시장 분석
│   ├── policy_agent.py        # 정책 분석
│   ├── company_agent.py       # 기업 분석
│   └── stock_agent.py         # 주가 분석
├── prompts/                    # 프롬프트 템플릿
│   ├── survey_prompt.txt
│   ├── market_prompt.txt
│   ├── policy_prompt.txt
│   ├── company_prompt.txt
│   ├── stock_prompt.txt
│   └── report_prompt.txt
├── utils/                      # 유틸리티 함수
│   ├── data_fetcher.py        # 데이터 수집
│   ├── web_scraper.py         # 웹 스크래핑
│   └── api_client.py          # 외부 API 클라이언트
├── outputs/                    # 분석 결과 저장
│   ├── reports/               # 생성된 리포트
│   └── logs/                  # 실행 로그
├── config/                     # 설정 파일
│   └── config.yaml            # API 키, 파라미터 설정
├── graph.py                    # LangGraph 워크플로우 정의
├── state.py                    # State 정의
├── app.py                      # 메인 실행 스크립트
├── requirements.txt            # Python 의존성
└── README.md
```


## Contributors

- **정재미** - Prompt Engineering, Agent Design, Graph Architecture


