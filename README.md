# 전기차 시장 트렌드 분석 Multi-Agent 시스템

LangGraph 기반의 Fan-out/Fan-in 패턴을 사용한 전기차 시장 종합 분석 시스템입니다.

## 🏗️ 시스템 구조

```
시작
  ↓
Supervisor Agent (조정자)
  ↓
Fan-out (병렬 실행)
  ├─ 여론조사 Agent
  ├─ Market 분석 Agent  
  ├─ 정책 분석 Agent
  └─ 기업 분석 Agent
  ↓
Fan-in (결과 수집)
  ↓
Supervisor Agent (통합)
  ↓
Report Generator Agent
  ↓
최종 리포트 생성 (PDF)
```

## 📊 에이전트 구성

### 1. Survey Agent (여론조사 분석)
- **기능**: 소비자 인식 및 여론 분석
- **데이터 소스**: 네이버 뉴스, YouTube 댓글, Twitter 댓글 
- **분석 내용**:
  - 구매 의향 및 브랜드 선호도
  - 구매 결정 요인
  - 소비자 우려 요소 (주행거리, 충전, 비용, 배터리 수명)

### 2. Market Agent (시장 현황 분석)
- **기능**: 글로벌 및 지역별 시장 현황 분석
- **분석 지역**: 글로벌, 북미, 유럽, 아시아, 한국
- **분석 내용**:
  - 시장 규모 및 성장률
  - 지역별 판매량 및 점유율
  - 가격 트렌드

### 3. Policy Agent (정책 및 규제 분석)
- **기능**: 각국 정책 및 규제 환경 분석
- **분석 내용**:
  - 보조금 정책
  - 내연기관 규제
  - 충전 인프라 정책
  - 세제 혜택

### 4. Company Agent (기업 분석)
- **기능**: 주요 제조사 및 배터리 공급사 분석
- **분석 대상**:
  - 전기차 제조사: Tesla, GM, Ford 등
  - 배터리 공급사: CATL, LG에너지솔루션, TSMC 등
- **분석 내용**:
  - 기업별 시장 점유율 및 전략
  - 공급망 구조
  - 재무 현황 및 전망

### 5. Report Generator Agent (보고서 생성)
- **기능**: 4개 에이전트 결과 통합 및 종합 보고서 생성
- **출력 형식**: Markdown, PDF
- **보고서 구성**:
  - Executive Summary
  - 글로벌 시장 현황
  - 산업 주요 트렌드
  - 소비자 인식 분석
  - 주요 기업 및 공급망 분석
  - 정책 및 규제 환경
  - 시장 전망 및 투자 시사점
  - 결론 및 제언


## 📁 프로젝트 구조

```
aiMiniProject2/
├── main.py                         # 🎯 메인 실행 파일 (진입점)
├── state.py                        # 상태 관리 (SupervisedState, AgentResult)
├── requirements.txt                # 패키지 의존성
├── README.md                       # 프로젝트 문서
│
├── agents/                         # 🤖 에이전트 모듈
│   ├── supervisorAgent.py         # Supervisor Agent (조율자)
│   ├── reportGeneratorAgent.py    # Report Generator Agent
│   ├── surveyAgent.py             # 여론조사 에이전트
│   ├── marketAnalyzeAgent.py      # 시장 분석 에이전트
│   ├── policyAgent.py             # 정책 분석 에이전트
│   └── companyAgent.py            # 기업 분석 에이전트
│
├── prompts/                        # 📝 프롬프트 템플릿
│   ├── surveyAgent_prompt.py
│   ├── marketAnalyze_prompt.py
│   ├── policyAgent_prompt.py
│   ├── companyAgent_prompt.py
│   └── report_prompt.py           # 보고서 생성 프롬프트
│
├── utils/                          # 🔧 유틸리티
│   ├── pdf_generator.py           # PDF 생성
│   └── web_scraper.py
│
└── outputs/                        # 📂 출력 디렉토리
    ├── reports/                    # 생성된 보고서 (PDF, MD)
    └── logs/                       # 실행 로그
```
## Architecture

![alt text](<전기차 flow_v2.0.png>)


## Contributors 
- 정재민 : Agent 설계