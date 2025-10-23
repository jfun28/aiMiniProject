"""
Policy Agent - 정책 및 규제 분석
전기차 관련 정부 정책, 보조금, 규제 분석
"""

import sys
import os

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.insert(0, project_root)

from typing import Dict, List, Union
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from prompts.policyAgent_prompt import POLICY_ANALYZE_PROMPT
from state import AgentResult

# 실제 TavilySearchResults tool 사용
from langchain_community.tools.tavily_search import TavilySearchResults

class PolicyAgent:
    """정책 분석 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.agent_name = "Policy Agent"
        self.prompt_template = POLICY_ANALYZE_PROMPT
        # Tavily API를 활용한 검색툴 인스턴스 생성
        self.search_tool = TavilySearchResults(max_results=3)

    def analyze(self, query_params: Dict) -> AgentResult:
        """
        정책 분석 실행 - Tavily API 활용
        """
        try:
            print(f"[{self.agent_name}] 정책 분석 시작...")

            # 검색 쿼리 생성
            search_queries = self._build_search_queries(query_params)
            all_search_results = []

            # 실제 Tavily로 최대 15개 쿼리만 실행
            for query in search_queries[:15]:
                print(f"  🔍 검색 중: {query}")
                try:
                    # TavilySearchResults의 invoke는 리스트 반환
                    results = self.search_tool.invoke(query)
                    if isinstance(results, list):
                        all_search_results.extend(results)
                    else:
                        all_search_results.append(results)
                except Exception as e:
                    print(f"  ⚠️ 검색 실패: {query} - {str(e)}")

            # 검색 결과 포맷팅
            formatted_results = self._format_search_results(all_search_results)
            print(f"  ✓ {len(all_search_results)}개 검색 결과 수집 완료")

            # LLM 프롬프트 및 결과 추출
            prompt = ChatPromptTemplate.from_template(self.prompt_template)
            chain = prompt | self.llm

            response = chain.invoke({
                "query_params": str(query_params),
                "search_results": formatted_results
            })

            # 결과 구조화
            result_data = {
                "policies": "분석됨",
                "subsidies": "분석됨",
                "regulations": "분석됨",
                "market_impact": "분석됨",
                "sources_count": len(all_search_results),
                "search_queries": search_queries
            }

            # 출처 정보 추출 (개선)
            sources = []
            for idx, result in enumerate(all_search_results, 1):
                if isinstance(result, dict):
                    title = result.get("title", "제목 없음")
                    url = result.get("url", "")
                    content = result.get("content", result.get("snippet", ""))
                    score = result.get("score", None)

                    source_entry = {
                        "id": idx,
                        "title": title,
                        "url": url,
                        "snippet": content[:300] if content else "",
                    }

                    if score is not None:
                        source_entry["relevance_score"] = score

                    sources.append(source_entry)

            print(f"[{self.agent_name}] 분석 완료 ✓ (출처: {len(sources)}개)")

            return AgentResult(
                agent_name=self.agent_name,
                status="success",
                data=result_data,
                summary=response.content,
                timestamp=datetime.now(),
                sources=sources
            )

        except Exception as e:
            print(f"[{self.agent_name}] 오류 발생: {str(e)}")
            return AgentResult(
                agent_name=self.agent_name,
                status="failed",
                data={},
                summary="",
                timestamp=datetime.now(),
                error_message=str(e)
            )

    def _build_search_queries(self, query_params: Dict) -> List[str]:
        """다중 검색 쿼리 생성 - 한국/미국/유럽 등 여러 지역 동시 지원"""
        raw_regions = query_params.get("region", ["한국"])
        if isinstance(raw_regions, str):
            regions = [raw_regions]
        elif isinstance(raw_regions, list):
            regions = list(set(raw_regions))
        else:
            regions = ["한국"]

        period = query_params.get("period", "2024")

        queries = []
        for region in regions:
            queries.extend([
                f"{region} 전기차 정부 정책 {period}",
                f"{region} 전기차 보조금 {period} 현황",
                f"{region} 전기차 규제 {period} 배출가스",
                f"{region} 전기차 충전 인프라 정책 {period}",
            ])
        return queries

    def _format_search_results(self, results: list) -> str:
        """Tavily 검색 결과 포맷팅 (최대 15개)"""
        if not results:
            return "검색 결과 없음"

        formatted = []
        for idx, result in enumerate(results[:15], 1):
            if isinstance(result, dict):
                title = result.get('title', 'N/A')
                content = result.get('content', result.get('snippet', 'N/A'))
                url = result.get('url', 'N/A')
                score = result.get('score', 'N/A')

                formatted.append(f"""
[출처 {idx}]
제목: {title}
URL: {url}
관련도: {score}
내용: {content}
{'='*80}""")
            elif isinstance(result, str):
                formatted.append(f"""
[출처 {idx}]
내용: {result}
{'='*80}""")
        return "\n".join(formatted) if formatted else "검색 결과 없음"


def create_policy_agent(llm: ChatOpenAI) -> PolicyAgent:
    """Policy Agent 생성 팩토리 함수 (Tavily tool 내장)"""
    return PolicyAgent(llm)

# ======= 단독 실행을 위한 main 함수 =======
if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    print("\n" + "="*70)
    print("Policy Agent(langraph + tavily) 단독 테스트")
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
        import sys
        sys.exit(1)

    # 실제 TavilySearchResults tool 사용, PolicyAgent는 내부적으로 사용하므로 search_tool 인자 불필요
    agent = create_policy_agent(llm)

    query_params = {
        "region": ["한국", "미국","유럽"],
        "period": "2024"
    }

    print(f"\n[설정] 분석 파라미터:")
    print(f"   - 지역: {', '.join(query_params['region']) if isinstance(query_params['region'], list) else query_params['region']}")
    print(f"   - 기간: {query_params['period']}")
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
        print(f"검색 쿼리: {len(result.data.get('search_queries', []))}개")
    else:
        print(f"\n오류: {result.error_message}")
    
    print("\n" + "="*70)
    print("테스트 완료!")
    print("="*70)
