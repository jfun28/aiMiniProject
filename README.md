# 전기차 시장 트렌드 분석 Multi-Agent 시스템

LangGraph 기반의 Fan-out/Fan-in 패턴을 사용한 전기차 시장 종합 분석 시스템입니다.


## 시스템 개요

4개의 전문 에이전트가 병렬로 실행되어 전기차 시장을 다각도로 분석하고 통합 보고서를 생성합니다.

### 주요 기능
- ✅ 병렬 처리를 통한 빠른 분석
- ✅ 실시간 웹 데이터 수집 (Tavily API)
- ✅ 다각도 분석 (시장/정책/기업/여론)
- ✅ 전문 보고서 생성 (PDF/Markdown)
- ✅ 출처 추적 및 참고자료 제공

## Overview

- Method : AI Agent + Supervisor agent
- Tools : Youtube API, Twitter API, Tavily web api


## 🏗️ 아키텍처

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
## 에이전트 구성

### 1. 🗳️ Survey Agent (여론조사)
**기능**: 소비자 인식 및 여론 분석

**데이터 소스**:
- 네이버 뉴스/댓글->Webcrawler 미구현으로 LLM 생성
- YouTube 댓글 ->API 할당량 초과시 LLM 생성
- Twitter 댓글 ->API 할당량 초과시 LLM 생성

**분석 항목**:
- 구매 의향 및 브랜드 선호도
- 주요 우려사항 (배터리/충전/가격)

### 2. 📈 Market Agent (시장 분석)
**기능**: 글로벌/지역별 시장 현황 분석

**분석 지역**:
- 글로벌, 북미, 유럽, 아시아, 한국

**분석 항목**:
- 시장 규모 및 성장률
- 제조사별 점유율
- 가격 트렌드

### 3. ⚖️ Policy Agent (정책 분석)
**기능**: 정부 정책 및 규제 환경 분석

**분석 항목**:
- 보조금 정책
- 내연기관 규제
- 충전 인프라 계획
- 세제 혜택

### 4. 🏭 Company Agent (기업 분석)
**기능**: 제조사 및 배터리 공급망 분석

**분석 대상**:
- 제조사: Tesla, Hyundai, BYD 등
- 배터리: CATL, LG에너지솔루션 등

**분석 항목**:
- 재무 지표 및 생산 능력
- 기술 경쟁력 및 시장 전략

### 5. 📝 Report Generator
**기능**: 통합 보고서 생성

**출력 형식**:
- PDF (전문 포맷)
- Markdown

**보고서 구성**:
- Executive Summary
- 시장 현황 및 트렌드
- 소비자 인식 분석
- 기업 및 공급망 분석
- 정책 환경
- 투자 시사점
## 에이전트 구성

### 1. 🗳️ Survey Agent (여론조사)
**기능**: 소비자 인식 및 여론 분석

**데이터 소스**:
- 네이버 뉴스/댓글 -> LLM 생성 webcrawler 구현 못함
- YouTube 댓글 -> API 할당량 초과시 LLM 생성
- Twitter(X)  -> API 할당량 초과시 LLM 생성

**분석 항목**:
- 구매 의향 및 브랜드 선호도
- 주요 우려사항 (배터리/충전/가격)

### 2. 📈 Market Agent (시장 분석)
**기능**: 글로벌/지역별 시장 현황 분석

**분석 지역**:
- 글로벌, 북미, 유럽, 아시아, 한국

**분석 항목**:
- 시장 규모 및 성장률
- 제조사별 점유율
- 가격 트렌드

### 3. ⚖️ Policy Agent (정책 분석)
**기능**: 정부 정책 및 규제 환경 분석

**분석 항목**:
- 보조금 정책
- 내연기관 규제
- 충전 인프라 계획
- 세제 혜택

### 4. 🏭 Company Agent (기업 분석)
**기능**: 제조사 및 배터리 공급망 분석

**분석 대상**:
- 제조사: Tesla, Hyundai, BYD 등
- 배터리: CATL, LG에너지솔루션 등

**분석 항목**:
- 재무 지표 및 생산 능력
- 기술 경쟁력 및 시장 전략

### 5. 📝 Report Generator
**기능**: 통합 보고서 생성

**출력 형식**:
- PDF (전문 포맷)
- Markdown

**보고서 구성**:
- Executive Summary
- 시장 현황 및 트렌드
- 소비자 인식 분석
- 기업 및 공급망 분석
- 정책 환경
- 투자 시사점

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
