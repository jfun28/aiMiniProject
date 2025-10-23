"""
전기차 시장 트렌드 분석 멀티 에이전트 시스템
메인 실행 파일

플로우:
1. Supervisor Agent가 4개의 전문 에이전트를 fan-out/fan-in으로 조율
2. Report Generator Agent가 결과를 종합하여 PDF 보고서 생성
"""

import os
import sys
from datetime import datetime
from typing import Dict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

# 프로젝트 모듈 import
from agents.supervisorAgent import create_supervisor_agent
from agents.reportGeneratorAgent import create_report_generator


def run_ev_market_analysis(
    region: str = "한국",
    period: str = "2024",
    companies: list = None,
    keywords: list = None,
    output_filename: Optional[str] = None
) -> Dict:
    
    # 기본값 설정
    if companies is None:
        companies = ["Tesla", "현대차", "BYD"]
    if keywords is None:
        keywords = ["전기차", "전기자동차", "EV"]
    
    # 실행 시간 측정 시작
    start_time = datetime.now()
    
    print("\n" + "="*80)
    print("🚗 전기차 시장 트렌드 종합 분석 시스템")
    print("="*80)
    print(f"📅 실행 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n📊 분석 파라미터:")
    print(f"   - 지역: {region}")
    print(f"   - 기간: {period}")
    print(f"   - 기업: {', '.join(companies)}")
    print(f"   - 키워드: {', '.join(keywords)}")
    print("="*80)
    
    try:
        # 1. LLM 및 도구 초기화
        print("\n[1/3] 🔧 시스템 초기화...")
        
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3
        )
        search_tool = TavilySearchResults(max_results=5)
        
        print("   ✓ OpenAI LLM 연결 완료")
        print("   ✓ Tavily Search 도구 연결 완료")
        
        # 2. Supervisor Agent 실행 (4개 에이전트 조율)
        print("\n[2/3] 🎯 Supervisor Agent 실행 (Multi-Agent 조율)...")
        print("   → 여론조사, 시장분석, 정책분석, 기업분석 에이전트 병렬 실행\n")
        
        supervisor = create_supervisor_agent(llm, search_tool)
        
        query_params = {
            "region": region,
            "period": period,
            "companies": companies,
            "keywords": keywords
        }
        
        # Fan-Out/Fan-In 실행
        final_state = supervisor.coordinate(query_params)
        
        # 결과 확인
        success_agents = []
        failed_agents = []
        
        for agent_key in ["survey_result", "market_result", "policy_result", "company_result"]:
            result = final_state.get(agent_key)
            agent_name = agent_key.replace("_result", "").title()
            if result and hasattr(result, 'status') and result.status == "success":
                success_agents.append(agent_name)
            else:
                failed_agents.append(agent_name)
        
        print(f"\n   ✅ 성공: {', '.join(success_agents)}")
        if failed_agents:
            print(f"   ⚠️  실패: {', '.join(failed_agents)}")
        
        # 3. Report Generator Agent 실행 (최종 보고서 생성)
        print("\n[3/3] 📝 Report Generator Agent 실행 (최종 보고서 생성)...")
        
        report_generator = create_report_generator(llm)
        report_result = report_generator.generate_report(
            state=final_state,
            output_filename=output_filename
        )
        
        # 실행 시간 계산
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # 최종 결과
        if report_result.get('status') == 'success':
            print("\n" + "="*80)
            print("✅ 전기차 시장 트렌드 분석 완료!")
            print("="*80)
            print(f"⏱️  총 실행 시간: {execution_time:.1f}초")
            print(f"\n📄 생성된 파일:")
            if report_result.get('markdown_path'):
                print(f"   - 마크다운: {report_result.get('markdown_path')}")
            else:
                print("   - 마크다운 파일이 생성되지 않았습니다.")
            if report_result.get('pdf_path'):
                print(f"   - PDF: {report_result.get('pdf_path')}")
            print("\n📊 분석 결과:")
            print(f"   - 성공한 에이전트: {len(success_agents)}/4")
            if report_result.get('report_markdown'):
                print(f"   - 보고서 길이: {len(report_result['report_markdown']):,}자")
            else:
                print("   - 보고서 결과가 없습니다.")
            print("="*80 + "\n")
            
            return {
                "status": "success",
                "pdf_path": report_result.get('pdf_path'),
                "markdown_path": report_result.get('markdown_path'),
                "report_markdown": report_result.get('report_markdown'),
                "execution_time": execution_time,
                "agents_success": len(success_agents),
                "agents_total": 4
            }
        else:
            print("\n" + "="*80)
            print("⚠️ 보고서 생성 실패")
            print("="*80)
            print(f"오류: {report_result.get('error_message')}")
            print("="*80 + "\n")
            
            return {
                "status": "failed",
                "error_message": report_result.get('error_message'),
                "execution_time": execution_time
            }
    
    except Exception as e:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print("\n" + "="*80)
        print("❌ 시스템 오류 발생")
        print("="*80)
        print(f"오류: {str(e)}")
        
        import traceback
        print("\n상세 오류:")
        traceback.print_exc()
        
        print("="*80 + "\n")
        
        return {
            "status": "failed",
            "error_message": str(e),
            "execution_time": execution_time
        }


# ============================================================================
# CLI 실행
# ============================================================================
def main():
    """커맨드라인 인터페이스"""
    load_dotenv()
    
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║     🚗 전기차 시장 트렌드 종합 분석 시스템 (Multi-Agent)            ║
║                                                                       ║
║     - 여론조사 분석 (Survey Agent)                                   ║
║     - 시장 현황 분석 (Market Agent)                                  ║
║     - 정책 규제 분석 (Policy Agent)                                  ║
║     - 기업 경쟁력 분석 (Company Agent)                               ║
║     - 종합 보고서 생성 (Report Generator)                            ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    # API 키 확인
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    if not openai_key:
        print("❌ 오류: OPENAI_API_KEY가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        sys.exit(1)
    
    if not tavily_key:
        print("⚠️  경고: TAVILY_API_KEY가 설정되지 않았습니다.")
        print("   일부 검색 기능이 제한될 수 있습니다.")
    
    # 분석 실행 - 모든 에이전트 실행 보장
    result = run_ev_market_analysis(
        region="한국",
        period="2024",
        companies=["Tesla", "현대차", "BYD", "기아"],  # Company Agent 트리거
        keywords=[
            # Survey Agent: 소비자 여론조사
            "전기차", "전기자동차", "EV", 
            "소비자 인식", "여론조사", "구매 트렌드",
            
            # Market Agent: 산업/시장 분석
            "시장 규모", "판매량", "시장 점유율", "가격 동향",
            
            # Policy Agent: 정책 분석  
            "정부 정책", "규제", "보조금", "충전 인프라",
            
            # Company Agent 추가 키워드
            "기업 전략", "재무 성과", "경쟁력"
        ],
        output_filename=None  # 자동 생성
    )
    
    # 결과 처리
    if result.get('status') == 'success':
        print("✅ 분석이 성공적으로 완료되었습니다!")
        if result.get('pdf_path'):
            print(f"\n📄 PDF 보고서를 확인하세요: {result.get('pdf_path')}")
        sys.exit(0)
    else:
        print("❌ 분석 중 오류가 발생했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
