"""
Supervisor Agent - Multi-Agent 시스템 조율자
4개의 에이전트(Survey, Market, Policy, Company)를 fan-out/fan-in 방식으로 조율합니다.
"""

import os
import sys
from typing import Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프로젝트 루트 경로 설정
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.insert(0, project_root)

from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
import json
import re

from state import SupervisedState, AgentResult
from agents.surveyAgent import create_survey_agent
from agents.marketAnalyzeAgent import create_market_agent
from agents.policyAgent import create_policy_agent
from agents.companyAgent import create_company_agent


class SupervisorAgent:
    """멀티 에이전트 시스템의 Supervisor"""
    
    def __init__(self, llm: ChatOpenAI, search_tool: TavilySearchResults):
        self.llm = llm
        self.search_tool = search_tool
        self.agent_name = "Supervisor Agent"
        
        # 4개의 전문 에이전트 초기화
        print(f"\n[{self.agent_name}] 전문 에이전트 초기화 중...")
        self.survey_agent = create_survey_agent(llm, search_tool)
        self.market_agent = create_market_agent(llm)
        self.policy_agent = create_policy_agent(llm)
        self.company_agent = create_company_agent(llm, search_tool)
        print(f"[{self.agent_name}] 모든 에이전트 초기화 완료 ✓")
        
        # LangGraph 워크플로우 구축
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 구성 - 지능형 라우팅 포함"""
        workflow = StateGraph(SupervisedState)
        
        # 노드 정의
        workflow.add_node("decision", self._supervisor_decision_node)
        workflow.add_node("fan_out", self._fan_out_node)
        workflow.add_node("quality_check", self._quality_check_node)
        workflow.add_node("fan_in", self._fan_in_node)
        
        # 워크플로우 설정
        workflow.set_entry_point("decision")
        workflow.add_edge("decision", "fan_out")
        workflow.add_edge("fan_out", "quality_check")
        
        # 조건부 엣지: quality_check 후 재시도 또는 완료
        workflow.add_conditional_edges(
            "quality_check",
            self._should_continue,
            {
                "retry": "fan_out",     # 재시도 필요
                "complete": "fan_in"    # 완료
            }
        )
        workflow.add_edge("fan_in", END)
        
        return workflow.compile()
    
    def _supervisor_decision_node(self, state: SupervisedState) -> SupervisedState:
        """Supervisor가 쿼리를 분석하여 필요한 에이전트를 지능적으로 선택"""
        print("\n" + "="*80)
        print(f"[{self.agent_name}] Decision: 필요한 에이전트 선택")
        print("="*80)
        
        query_params = state["query_params"]
        retry_agents = state.get("retry_agents", [])
        
        # 재시도 모드인 경우
        if retry_agents:
            selected_agents = retry_agents
            print(f"   🔄 재시도 모드: {', '.join(selected_agents)}")
        else:
            # 새로운 쿼리 분석
            prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 멀티 에이전트 시스템의 조율자입니다.
사용자의 쿼리를 분석하여 어떤 에이전트가 필요한지 판단하세요.

사용 가능한 에이전트:
- survey: 여론조사, 소비자 인식, 트렌드 조사
- market: 시장 규모, 판매량, 가격 동향, 시장 점유율
- policy: 정부 정책, 규제, 보조금, 법률
- company: 특정 기업 분석, 전략, 재무, 제품

다음 형식으로 응답하세요:
{{"agents": ["agent1", "agent2", ...]}}

필요한 에이전트만 선택하세요. 모든 에이전트가 필요하지 않을 수 있습니다."""),
                ("user", """쿼리 파라미터:
- 지역: {region}
- 기간: {period}
- 기업: {companies}
- 키워드: {keywords}

이 쿼리를 처리하기 위해 필요한 에이전트를 선택하세요.""")
            ])
            
            response = self.llm.invoke(
                prompt.format_messages(
                    region=query_params.get("region", "N/A"),
                    period=query_params.get("period", "N/A"),
                    companies=query_params.get("companies", "N/A"),
                    keywords=query_params.get("keywords", "N/A")
                )
            )
            
            # JSON 파싱
            try:
                content = response.content
                # JSON 추출 (```json ... ``` 형태도 처리)
                json_match = re.search(r'\{.*?\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    selected_agents = result.get("agents", [])
                else:
                    # 파싱 실패 시 모든 에이전트 실행
                    selected_agents = ["survey", "market", "policy", "company"]
            except:
                # 에러 발생 시 안전하게 모든 에이전트 실행
                selected_agents = ["survey", "market", "policy", "company"]
            
            print(f"   🤖 선택된 에이전트: {', '.join(selected_agents)}")
            
            # 기업이 지정된 경우 company 에이전트 자동 추가
            if query_params.get("companies") and "company" not in selected_agents:
                selected_agents.append("company")
                print(f"   ➕ 기업 파라미터 감지: company 에이전트 추가")
        
        return {
            **state,
            "selected_agents": selected_agents,
            "messages": state.get("messages", []) + [
                f"[{datetime.now().isoformat()}] 선택된 에이전트: {', '.join(selected_agents)}"
            ]
        }
    
    def _fan_out_node(self, state: SupervisedState) -> SupervisedState:
        """Fan-Out: 선택된 에이전트만 병렬 실행"""
        selected_agents = state["selected_agents"]
        retry_count = state.get("retry_count", 0)
        
        print("\n" + "="*80)
        print(f"[{self.agent_name}] Fan-Out: {len(selected_agents)}개 에이전트 병렬 실행")
        if retry_count > 0:
            print(f"   (재시도 횟수: {retry_count})")
        print("="*80)
        
        query_params = state["query_params"]
        
        # 에이전트 매핑
        agent_map = {
            "survey": (self.survey_agent, "여론조사"),
            "market": (self.market_agent, "시장분석"),
            "policy": (self.policy_agent, "정책분석"),
            "company": (self.company_agent, "기업분석"),
        }
        
        # 선택된 에이전트만 실행
        agent_tasks = [
            (name, agent_map[name][0], agent_map[name][1])
            for name in selected_agents
            if name in agent_map
        ]
        
        results = {}
        
        # ThreadPoolExecutor로 병렬 실행
        with ThreadPoolExecutor(max_workers=len(agent_tasks)) as executor:
            # 각 에이전트의 작업 제출
            future_to_agent = {
                executor.submit(agent.analyze, query_params): (name, display_name)
                for name, agent, display_name in agent_tasks
            }
            
            # 완료된 작업 수집
            for future in as_completed(future_to_agent):
                agent_name, display_name = future_to_agent[future]
                try:
                    result = future.result()
                    results[agent_name] = result
                    status_emoji = "✅" if result.status == "success" else "❌"
                    print(f"   {status_emoji} {display_name} 완료")
                except Exception as e:
                    print(f"   ❌ {display_name} 오류: {str(e)}")
                    results[agent_name] = AgentResult(
                        agent_name=display_name,
                        status="failed",
                        data={},
                        summary="",
                        timestamp=datetime.now(),
                        error_message=str(e)
                    )
        
        print(f"\n[{self.agent_name}] Fan-Out 완료")
        
        # State 업데이트 (기존 결과 유지하면서 새 결과 병합)
        updated_state = {**state}
        for agent_name in ["survey", "market", "policy", "company"]:
            if agent_name in results:
                updated_state[f"{agent_name}_result"] = results[agent_name]
        
        updated_state["messages"] = state.get("messages", []) + [
            f"[{datetime.now().isoformat()}] Fan-Out 완료: {len(selected_agents)}개 에이전트 실행"
        ]
        
        return updated_state
    
    def _quality_check_node(self, state: SupervisedState) -> SupervisedState:
        """결과 품질 검증 및 재실행 결정"""
        print("\n" + "="*80)
        print(f"[{self.agent_name}] Quality Check: 결과 품질 검증")
        print("="*80)
        
        selected_agents = state["selected_agents"]
        retry_count = state.get("retry_count", 0)
        max_retry = 2  # 최대 재시도 횟수
        
        # 품질 기준
        MIN_SUMMARY_LENGTH = 100  # 최소 요약 길이
        MIN_DATA_SIZE = 50        # 최소 데이터 크기
        
        needs_retry = []
        quality_report = []
        
        # 각 에이전트 결과 품질 검증
        agent_map = {
            "survey": ("survey_result", "여론조사"),
            "market": ("market_result", "시장분석"),
            "policy": ("policy_result", "정책분석"),
            "company": ("company_result", "기업분석"),
        }
        
        for agent_name in selected_agents:
            if agent_name not in agent_map:
                continue
                
            result_key, display_name = agent_map[agent_name]
            result = state.get(result_key)
            
            if not result:
                quality_report.append(f"   ❌ {display_name}: 결과 없음")
                needs_retry.append(agent_name)
                continue
            
            # 품질 검증
            issues = []
            
            if result.status != "success":
                issues.append("실패 상태")
            
            if len(result.summary) < MIN_SUMMARY_LENGTH:
                issues.append(f"요약 너무 짧음 ({len(result.summary)}자)")
            
            data_size = len(str(result.data))
            if data_size < MIN_DATA_SIZE:
                issues.append(f"데이터 부족 ({data_size}자)")
            
            if result.error_message:
                issues.append(f"에러: {result.error_message}")
            
            # 결과 판정
            if issues:
                quality_report.append(f"   ⚠️  {display_name}: {', '.join(issues)}")
                needs_retry.append(agent_name)
            else:
                quality_report.append(f"   ✅ {display_name}: 품질 양호 (요약 {len(result.summary)}자, 데이터 {data_size}자)")
        
        # 품질 리포트 출력
        for line in quality_report:
            print(line)
        
        # 재시도 결정
        should_continue = False
        if needs_retry and retry_count < max_retry:
            should_continue = True
            print(f"\n   🔄 재시도 필요: {', '.join(needs_retry)} (시도 {retry_count + 1}/{max_retry})")
        elif needs_retry and retry_count >= max_retry:
            print(f"\n   ⛔ 최대 재시도 횟수 도달. 현재 결과로 진행합니다.")
        else:
            print(f"\n   ✨ 모든 결과 품질 검증 통과!")
        
        return {
            **state,
            "retry_agents": needs_retry if should_continue else [],
            "should_continue": should_continue,
            "retry_count": retry_count + 1 if should_continue else retry_count,
            "messages": state.get("messages", []) + [
                f"[{datetime.now().isoformat()}] Quality Check: {len(needs_retry)}개 에이전트 재시도 필요" if should_continue else
                f"[{datetime.now().isoformat()}] Quality Check: 모든 결과 양호"
            ]
        }
    
    def _should_continue(self, state: SupervisedState) -> str:
        """조건부 라우팅: 재시도 또는 완료"""
        should_continue = state.get("should_continue", False)
        
        if should_continue:
            return "retry"
        else:
            return "complete"
    
    def _fan_in_node(self, state: SupervisedState) -> SupervisedState:
        """Fan-In: 최종 결과 통합"""
        print("\n" + "="*80)
        print(f"[{self.agent_name}] Fan-In: 최종 결과 통합")
        print("="*80)
        
        selected_agents = state["selected_agents"]
        
        # 각 에이전트 결과 확인
        results_summary = []
        
        agent_map = {
            "survey": ("survey_result", "여론조사"),
            "market": ("market_result", "시장분석"),
            "policy": ("policy_result", "정책분석"),
            "company": ("company_result", "기업분석"),
        }
        
        success_count = 0
        total_count = len(selected_agents)
        
        for agent_name in selected_agents:
            if agent_name not in agent_map:
                continue
                
            result_key, display_name = agent_map[agent_name]
            result = state.get(result_key)
            
            if result and result.status == "success":
                data_size = len(str(result.data))
                summary_size = len(result.summary)
                print(f"   ✅ {display_name}: 데이터 {data_size}자, 요약 {summary_size}자")
                results_summary.append(f"{display_name} 성공")
                success_count += 1
            else:
                error_msg = result.error_message if result else "결과 없음"
                print(f"   ⚠️  {display_name}: {error_msg}")
                results_summary.append(f"{display_name} 부분성공")
        
        print(f"\n[{self.agent_name}] Fan-In 완료: {success_count}/{total_count} 성공")
        
        return {
            **state,
            "messages": state.get("messages", []) + [
                f"[{datetime.now().isoformat()}] Fan-In 완료: {', '.join(results_summary)}"
            ]
        }
    
    def coordinate(self, query_params: Dict) -> SupervisedState:
        """
        멀티 에이전트 시스템 실행
        
        Args:
            query_params: 분석 파라미터
                - region: 대상 지역 (예: "한국", ["한국", "미국"])
                - period: 분석 기간 (예: "2024")
                - companies: 분석 대상 기업 리스트 (예: ["Tesla", "현대차"])
                - keywords: 여론조사 키워드 (예: ["전기차", "EV"])
        
        Returns:
            SupervisedState: 모든 에이전트의 결과가 담긴 상태
        """
        print("\n" + "="*80)
        print(f"[{self.agent_name}] 멀티 에이전트 시스템 시작")
        print("="*80)
        print(f"분석 파라미터:")
        print(f"  - 지역: {query_params.get('region', 'N/A')}")
        print(f"  - 기간: {query_params.get('period', 'N/A')}")
        print(f"  - 기업: {query_params.get('companies', 'N/A')}")
        print(f"  - 키워드: {query_params.get('keywords', 'N/A')}")
        print("="*80)
        
        # 초기 상태 생성
        from state import create_initial_state
        initial_state = create_initial_state(query_params)
        
        # LangGraph 워크플로우 실행
        start_time = datetime.now()
        final_state = self.workflow.invoke(initial_state)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print("\n" + "="*80)
        print(f"[{self.agent_name}] 멀티 에이전트 시스템 완료 (소요시간: {elapsed:.1f}초)")
        print("="*80)
        
        return final_state


def create_supervisor_agent(llm: ChatOpenAI, search_tool: TavilySearchResults) -> SupervisorAgent:
    """Supervisor Agent 생성 팩토리 함수"""
    return SupervisorAgent(llm, search_tool)


# ============================================================================
# 단독 테스트
# ============================================================================
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\n" + "="*80)
    print("Supervisor Agent 단독 테스트")
    print("="*80)
    
    # LLM 및 도구 초기화
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    search_tool = TavilySearchResults(max_results=5)
    
    # Supervisor Agent 생성
    supervisor = create_supervisor_agent(llm, search_tool)
    
    # 테스트 파라미터
    query_params = {
        "region": "한국",
        "period": "2024",
        "companies": ["Tesla", "현대차", "BYD"],
        "keywords": ["전기차", "전기자동차"]
    }
    
    # 실행
    final_state = supervisor.coordinate(query_params)
    
    # 결과 출력
    print("\n" + "="*80)
    print("최종 결과")
    print("="*80)
    
    for agent_name in ["survey_result", "market_result", "policy_result", "company_result"]:
        result = final_state.get(agent_name)
        if result:
            print(f"\n{agent_name}:")
            print(f"  상태: {result.status}")
            print(f"  요약: {result.summary[:200]}...")
    
    print("\n" + "="*80)
    print("테스트 완료!")
    print("="*80)

