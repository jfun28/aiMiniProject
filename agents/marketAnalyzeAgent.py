"""
Market Agent - 시장 현황 분석 (langraph 기반)
글로벌(북미, 유럽, 아시아) 및 한국 시장별 판매량, 시장 점유율, 가격 트렌드 분석

langraph + tavily tool 기반 구현 예시.
"""

import sys
import os

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.insert(0, project_root)

from typing import Dict, List, Optional
from datetime import datetime

# state, prompts는 프로젝트 구조에 맞게 import
from state import AgentResult
from prompts.marketAnalyze_prompt import MARKET_ANALYZE_PROMPT

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# langraph imports
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

# Tavily Tool
from langchain_community.tools.tavily_search import TavilySearchResults


# ---- State Definition for langraph ----
class MarketState(TypedDict, total=False):
    query_params: dict
    search_queries: List[str]
    search_results: List[dict]
    llm_response: str
    sources_count: int
    summary: str
    data: dict


def build_search_queries(query_params: Dict) -> list:
    """글로벌(북미, 유럽, 아시아) + 한국 시장 쿼리 생성"""
    period = query_params.get("period", "2024")
    companies = query_params.get("companies", [])

    regions = [
        ("글로벌", "global"),
        ("북미", "North America"),
        ("유럽", "Europe"),
        ("아시아", "Asia"),
        ("한국", "Korea"),
    ]

    queries = []
    for name, region in regions:
        # 영문 쿼리로 변경하여 더 많은 데이터 확보
        queries.append(f"electric vehicle market sales volume {region} {period}")
        queries.append(f"EV market share by manufacturer {region} {period}")
        queries.append(f"electric vehicle price trends {region} {period}")
        queries.append(f"EV market growth rate {region} {period}")
        
        if companies and len(queries) < 30:  # 쿼리 수 제한
            for company in companies[:2]:
                queries.append(f"{company} electric vehicle sales {region} {period}")

    return queries[:25]  # 최대 25개 쿼리로 제한


def format_search_results(results: list) -> str:
    """Tavily 검색 결과를 LLM이 분석하기 좋은 형태로 포맷팅"""
    if not results:
        return "검색 결과 없음"

    formatted = []
    for idx, result in enumerate(results[:30], 1):
        if isinstance(result, dict):
            title = result.get('title', 'N/A')
            content = result.get('content', result.get('snippet', 'N/A'))
            url = result.get('url', 'N/A')
            score = result.get('score', 'N/A')  # Tavily relevance score

            formatted.append(f"""
[출처 {idx}]
제목: {title}
URL: {url}
관련도: {score}
내용: {content}
{'='*80}""")
        elif isinstance(result, str):
            # 문자열인 경우
            formatted.append(f"""
[출처 {idx}]
내용: {result}
{'='*80}""")

    return "\n".join(formatted) if formatted else "검색 결과 없음"


def search_with_tavily(state: MarketState) -> MarketState:
    """langraph 노드: Tavily로 쿼리들 검색"""
    queries = state.get('search_queries', [])
    
    # max_results를 3으로 줄여서 API 호출 최적화
    tavily = TavilySearchResults(max_results=3)
    search_results = []
    
    for query in queries[:15]:  # 최대 15개 쿼리만 실행
        print(f"  [검색] Tavily: {query}")
        try:
            results = tavily.invoke(query)
            if isinstance(results, list):
                search_results.extend(results)
            else:
                search_results.append(results)
        except Exception as e:
            print(f"    [경고] 검색 실패: {str(e)}")
            continue
    
    return {
        **state,
        "search_results": search_results,
    }


def llm_analyze_node(state: MarketState, llm=None, prompt_template=None) -> MarketState:
    """langraph 노드: LLM을 통한 분석"""
    formatted_results = format_search_results(state.get("search_results", []))
    sources_count = len(state.get('search_results', []))
    
    # 프롬프트에 sources_count 추가
    full_prompt = prompt_template.replace("{sources_count}", str(sources_count))
    prompt = ChatPromptTemplate.from_template(full_prompt)
    chain = prompt | llm
    
    try:
        print(f"  [LLM] 분석 중... ({sources_count}개 자료 기반)")
        response = chain.invoke({
            "query_params": str(state.get("query_params", {})),
            "search_results": formatted_results
        })
        
        print(f"  [완료] LLM 분석 완료 (응답 길이: {len(response.content)} 자)")
        
        return {
            **state,
            "llm_response": response.content,
            "sources_count": sources_count,
        }
    except Exception as e:
        print(f"    [오류] LLM 분석 실패: {str(e)}")
        return {
            **state,
            "llm_response": f"# 분석 오류\n\n분석 중 오류 발생: {str(e)}",
            "sources_count": sources_count,
        }


def structure_result_node(state: MarketState) -> MarketState:
    """langraph 노드: 결과 구조화 및 섹션 추출"""
    llm_response = state.get("llm_response", "분석 결과 없음")
    
    # LLM 응답에서 주요 섹션 추출 시도
    def extract_section(content: str, section_marker: str) -> str:
        """Markdown에서 특정 섹션 추출"""
        try:
            if section_marker in content:
                start_idx = content.find(section_marker)
                # 다음 ## 또는 # 까지 추출
                next_section = content.find("\n## ", start_idx + len(section_marker))
                if next_section == -1:
                    next_section = content.find("\n# ", start_idx + len(section_marker))
                
                if next_section != -1:
                    return content[start_idx:next_section].strip()
                else:
                    return content[start_idx:].strip()
        except:
            pass
        return f"{section_marker}\n데이터 추출 실패"
    
    # 각 섹션 추출
    executive_summary = extract_section(llm_response, "## 📊 Executive Summary")
    global_analysis = extract_section(llm_response, "## 🌍 글로벌 시장 상세 분석")
    korea_analysis = extract_section(llm_response, "## 🇰🇷 한국 시장 상세 분석")
    investment_insights = extract_section(llm_response, "## 💡 비교 분석 및 투자 시사점")
    
    return {
        **state,
        "data": {
            "executive_summary": executive_summary,
            "global_analysis": global_analysis,
            "korea_analysis": korea_analysis,
            "investment_insights": investment_insights,
            "sources_count": state.get("sources_count", 0),
            "search_queries_count": len(state.get("search_queries", [])),
            "full_report": llm_response,
        },
        "summary": llm_response,  # 전체 리포트를 summary로 반환
        "search_results": state.get("search_results", []),  # 검색 결과 유지
    }


class MarketAgent:
    """시장 분석 에이전트(langraph & tavily 기반)"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.agent_name = "Market Agent"
        self.prompt_template = MARKET_ANALYZE_PROMPT

        # langraph StateGraph 생성
        self.graph = StateGraph(MarketState)

        # 노드 정의
        def build_query_node(state: MarketState) -> MarketState:
            queries = build_search_queries(state.get("query_params", {}))
            return {
                **state,
                "search_queries": queries
            }

        self.graph.add_node("query_builder", build_query_node)
        self.graph.add_node("tavily_search", search_with_tavily)
        
        # LLM 분석 노드 (클로저 사용)
        def llm_node_wrapper(state: MarketState) -> MarketState:
            return llm_analyze_node(state, llm=self.llm, prompt_template=self.prompt_template)
        
        self.graph.add_node("llm_analyze", llm_node_wrapper)
        self.graph.add_node("struct_result", structure_result_node)

        # 시작점 설정
        self.graph.set_entry_point("query_builder")

        # 엣지 연결
        self.graph.add_edge("query_builder", "tavily_search")
        self.graph.add_edge("tavily_search", "llm_analyze")
        self.graph.add_edge("llm_analyze", "struct_result")
        self.graph.add_edge("struct_result", END)

        # 그래프 컴파일
        self.compiled = self.graph.compile()

    def analyze(self, query_params: Dict) -> AgentResult:
        """langraph 기반 분석 실행"""
        print(f"\n[{self.agent_name}] 글로벌/한국 시장 분석 시작(langraph + tavily)...")
        try:
            # langraph 실행
            result_dict = self.compiled.invoke({"query_params": query_params})

            result_data = result_dict.get("data", {})
            summary = result_dict.get("summary", "분석 결과 없음")

            # 출처 정보 추출
            search_results = result_dict.get("search_results", [])

            sources = []
            for idx, result in enumerate(search_results, 1):
                if isinstance(result, dict):
                    title = result.get("title", "제목 없음")
                    url = result.get("url", "")
                    content = result.get("content", result.get("snippet", ""))
                    score = result.get("score", None)

                    # 출처 정보 저장
                    source_entry = {
                        "id": idx,
                        "title": title,
                        "url": url,
                        "snippet": content[:300] if content else "",  # 더 긴 발췌문
                    }

                    # Tavily relevance score가 있으면 추가
                    if score is not None:
                        source_entry["relevance_score"] = score

                    sources.append(source_entry)

            print(f"[{self.agent_name}] 분석 완료 ✓ (출처: {len(sources)}개)")

            return AgentResult(
                agent_name=self.agent_name,
                status="success",
                data=result_data,
                summary=summary,
                timestamp=datetime.now(),
                sources=sources
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


def create_market_agent(llm: ChatOpenAI) -> MarketAgent:
    """Market Agent 생성 (langraph + tavily tool)"""
    return MarketAgent(llm)


# ======= 단독 실행을 위한 main 함수 =======
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    print("\n" + "="*70)
    print("Market Agent(langraph + tavily) 단독 테스트")
    print("="*70)

    # ChatOpenAI 인스턴스 준비
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # 더 안정적인 모델로 변경
            temperature=0.2,
        )
        print("[OK] OpenAI API 연결 성공")
    except Exception as e:
        print(f"[ERROR] OpenAI API 연동 실패: {e}")
        sys.exit(1)

    # Agent 생성
    agent = create_market_agent(llm)

    query_params = {
        "region": "한국",
        "period": f"{datetime.now().year}",
        "companies": ["Tesla", "Hyundai", "BYD"],
        "focus_areas": ["시장 점유율", "가격", "성장률"]
    }

    print(f"\n[설정] 분석 파라미터:")
    print(f"   - 지역: {query_params['region']}")
    print(f"   - 기간: {query_params['period']}")
    print(f"   - 기업: {', '.join(query_params['companies'])}")
    print()

    # 분석 실행
    result = agent.analyze(query_params)

    # 결과 출력
    print("\n" + "="*70)
    print("분석 결과")
    print("="*70)
    print(f"\n상태: {result.status}")
    print(f"타임스탬프: {result.timestamp}")
    
    if result.status == "success":
        # 전체 리포트 출력
        print("\n" + "="*70)
        print("전체 리포트")
        print("="*70)
        print(result.summary)
        
        print("\n" + "="*70)
        print("구조화된 데이터")
        print("="*70)
        print(f"데이터 소스: {result.data.get('sources_count', 0)}개")
        print(f"검색 쿼리: {result.data.get('search_queries_count', 0)}개")
        
        # 섹션별 미리보기
        if 'executive_summary' in result.data:
            print(f"\nExecutive Summary 미리보기:")
            preview = result.data['executive_summary'][:200]
            print(f"{preview}...")
    else:
        print(f"\n오류: {result.error_message}")
    
    print("\n" + "="*70)
    print("테스트 완료!")
    print("="*70)