"""
Company Analysis Agent using LangGraph and Tavily API
전기차/배터리 산업 기업 분석 에이전트
"""

import os
import sys
from typing import TypedDict, Annotated, Sequence, Dict
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.insert(0, project_root)

from state import AgentResult
from prompts.companyAgent_prompt import COMPANY_ANALYZE_PROMPT


# State 정의
class CompanyState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    company_name: str
    query_params: Dict
    search_results: list
    final_report: str


class CompanyAgent:
    """기업 분석 에이전트"""
    
    def __init__(self, llm: ChatOpenAI, search_tool: TavilySearchResults):
        self.llm = llm
        self.search_tool = search_tool
        self.agent_name = "Company Agent"
        
    def _build_search_queries(self, company_name: str, query_params: Dict) -> list:
        """검색 쿼리 생성"""
        period = query_params.get("period", "2024")
        
        queries = [
            f"{company_name} {period} 실적 매출 영업이익",
            f"{company_name} electric vehicle battery market share {period}",
            f"{company_name} 최신 뉴스 전략 {period}",
            f"{company_name} stock price valuation {period}",
            f"{company_name} 전기차 배터리 생산량 {period}",
        ]
        
        return queries
    
    def analyze(self, query_params: Dict) -> AgentResult:
        """
        기업 분석 실행

        Args:
            query_params: 분석 파라미터 (companies 리스트 포함)

        Returns:
            AgentResult: 분석 결과
        """
        try:
            print(f"\n[{self.agent_name}] 기업 분석 시작...")

            companies = query_params.get("companies", ["Tesla"])
            all_company_reports = []
            all_sources = []  # 모든 기업의 출처 정보 저장

            for company_name in companies:
                print(f"  🔍 {company_name} 분석 중...")
                
                # 검색 쿼리 생성 및 실행
                search_queries = self._build_search_queries(company_name, query_params)
                search_results = []
                
                for query in search_queries[:5]:  # 최대 5개 쿼리
                    try:
                        results = self.search_tool.invoke(query)  # 문자열 직접 전달 (수정)
                        if isinstance(results, list):
                            search_results.extend(results)
                        else:
                            search_results.append(results)
                    except Exception as e:
                        print(f"    ⚠ 검색 실패: {query[:50]}... - {str(e)}")
                
                print(f"    ✓ {len(search_results)}개 검색 결과 수집")
                
                # 검색 결과 포맷팅 (개선 - URL, 제목, 관련도 포함)
                formatted_results = []
                for i, r in enumerate(search_results[:10]):
                    if isinstance(r, dict):
                        title = r.get('title', 'N/A')
                        url = r.get('url', 'N/A')
                        content = r.get('content', r.get('snippet', r.get('text', 'N/A')))
                        score = r.get('score', 'N/A')

                        formatted_results.append(f"""
[출처 {i+1}]
제목: {title}
URL: {url}
관련도: {score}
내용: {content}
{'='*80}""")
                    elif isinstance(r, str):
                        formatted_results.append(f"""
[출처 {i+1}]
내용: {r}
{'='*80}""")
                    else:
                        formatted_results.append(f"""
[출처 {i+1}]
내용: {str(r)}
{'='*80}""")
                
                company_data = "\n\n".join(formatted_results)
                
                # 프롬프트 생성 및 LLM 호출
                analysis_prompt = COMPANY_ANALYZE_PROMPT.format(
                    query_params=str(query_params),
                    company_data=company_data if company_data else "데이터 없음",
                    company_name=company_name
                )
                
                response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
                all_company_reports.append(f"## {company_name}\n\n{response.content}")

                # 출처 정보 저장 (개선)
                for result in search_results[:10]:
                    if isinstance(result, dict):
                        title = result.get("title", "제목 없음")
                        url = result.get("url", "")
                        content = result.get("content", result.get("snippet", ""))
                        score = result.get("score", None)

                        source_entry = {
                            "id": len(all_sources) + 1,
                            "company": company_name,
                            "title": title,
                            "url": url,
                            "snippet": content[:300] if content else "",
                        }

                        if score is not None:
                            source_entry["relevance_score"] = score

                        all_sources.append(source_entry)

                print(f"    ✅ {company_name} 분석 완료")

            # 전체 리포트 생성
            final_report = "\n\n---\n\n".join(all_company_reports)

            print(f"[{self.agent_name}] 분석 완료 ✓ (출처: {len(all_sources)}개)")

            return AgentResult(
                agent_name=self.agent_name,
                status="success",
                data={
                    "companies": companies,
                    "reports_count": len(all_company_reports),
                    "full_report": final_report
                },
                summary=final_report[:500] + "..." if len(final_report) > 500 else final_report,
                timestamp=datetime.now(),
                sources=all_sources
            )
            
        except Exception as e:
            print(f"[{self.agent_name}] 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return AgentResult(
                agent_name=self.agent_name,
                status="failed",
                data={},
                summary="",
                timestamp=datetime.now(),
                error_message=str(e)
            )


def create_company_agent(llm: ChatOpenAI, search_tool: TavilySearchResults) -> CompanyAgent:
    """Company Agent 생성 팩토리 함수"""
    return CompanyAgent(llm, search_tool)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # 테스트 실행
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    search_tool = TavilySearchResults(max_results=5)
    
    agent = create_company_agent(llm, search_tool)
    
    query_params = {
        "region": "한국",
        "period": "2024",
        "companies": ["Tesla", "현대차"],
        "focus_areas": ["시장 점유율", "재무 성과"]
    }
    
    result = agent.analyze(query_params)
    
    print("\n" + "="*70)
    print("분석 결과")
    print("="*70)
    print(f"상태: {result.status}")
    print(f"\n요약:\n{result.summary}")

