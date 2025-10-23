"""
전기차 시장 트렌드 분석 Multi-Agent 시스템의 State 정의
"""
from typing import TypedDict, Dict, List, Optional, Annotated
from typing_extensions import TypedDict
from dataclasses import dataclass
from datetime import datetime
import operator


@dataclass
class AgentResult:
    """개별 에이전트의 분석 결과"""
    agent_name: str
    status: str  # "success", "failed", "in_progress"
    data: Dict
    summary: str
    timestamp: datetime
    error_message: Optional[str] = None
    sources: Optional[List[Dict]] = None  # 출처 정보: [{"title": "...", "url": "...", "snippet": "..."}]


class SupervisedState(TypedDict):
    """Multi-Agent 시스템의 전체 상태"""
    
    # 입력 파라미터 (읽기 전용, 업데이트 안 함)
    query_params: Dict  # 분석 기간, 대상 지역, 관심 기업 등
    
    # Supervisor 제어 필드
    selected_agents: List[str]               # 실행할 에이전트 목록
    retry_agents: List[str]                  # 재실행이 필요한 에이전트 목록
    should_continue: bool                    # 재실행 여부
    retry_count: int                         # 재시도 횟수 (무한 루프 방지)
    
    # 에이전트 분석 결과
    survey_result: Optional[AgentResult]     # 여론조사 분석 결과
    market_result: Optional[AgentResult]     # 시장 분석 결과
    policy_result: Optional[AgentResult]     # 정책 분석 결과
    company_result: Optional[AgentResult]    # 기업 분석 결과
    
    # 최종 결과물
    final_report: Optional[str]              # 종합 분석 리포트
    
    # 로그 (여러 노드에서 동시 업데이트 가능)
    messages: Annotated[List[str], operator.add]  # 실행 로그 (디버깅용)


def create_initial_state(query_params: Dict) -> SupervisedState:
    """초기 상태 생성 헬퍼 함수"""
    return SupervisedState(
        query_params=query_params,
        selected_agents=[],
        retry_agents=[],
        should_continue=False,
        retry_count=0,
        survey_result=None,
        market_result=None,
        policy_result=None,
        company_result=None,
        final_report=None,
        messages=[]
    )

