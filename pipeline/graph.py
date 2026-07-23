from typing import TypedDict
from model import CandidateURL, AnalyzedResource
from pipeline.search import search_web
from pipeline.crawl import crawl_page
from pipeline.analyse import analyze_page
from pipeline.rank import rank_resources
from langgraph.graph import StateGraph, START, END
import asyncio
from crawl4ai import AsyncWebCrawler
from pipeline.storage import init_db, get_cached_result, save_result

class PipelineState(TypedDict):
    topic: str
    resource_type: str | None
    price_type: str | None
    difficulty_level: str | None
    candidates: list[CandidateURL]
    analyzed_results: list[AnalyzedResource]
    ranked_results: list[AnalyzedResource]


def search_node(state: PipelineState) -> dict:
    candidates = search_web(state["topic"])
    return {"candidates": candidates}

def crawl_and_analyze_node(state: PipelineState) -> dict:
    init_db()

    async def process_all():
        async with AsyncWebCrawler() as crawler:
            async def crawl_and_analyze_one(candidate):
                cached = get_cached_result(candidate.url, state["topic"])
                if cached:
                    print(f"💾 Using cached result for {candidate.url}")
                    return cached

                page = await crawl_page(candidate, crawler)
                if page:
                    analyzed = analyze_page(page, state["topic"], published_date=candidate.published_date)
                    if analyzed:
                        save_result(analyzed, state["topic"])
                    return analyzed
                return None

            tasks = [crawl_and_analyze_one(c) for c in state["candidates"][:5]]
            results = await asyncio.gather(*tasks)
            return [r for r in results if r is not None]

    analyzed_results = asyncio.run(process_all())
    return {"analyzed_results": analyzed_results}

    
async def crawl_and_analyze_one(candidate):
    cached = get_cached_result(candidate.url, state["topic"])
    if cached:
        return cached
    page = await crawl_page(candidate, crawler)
    if page:
        analyzed = analyze_page(page, state["topic"], published_date=candidate.published_date)
        if analyzed:
            save_result(analyzed, state["topic"])
        return analyzed
    return None


def rank_node(state: PipelineState) -> dict:
    ranked = rank_resources(
        state["analyzed_results"],
        resource_type=state.get("resource_type"),
        price_type=state.get("price_type"),
        difficulty_level=state.get("difficulty_level"),
    )
    return {"ranked_results": ranked}
def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("search", search_node)
    graph.add_node("crawl_and_analyze", crawl_and_analyze_node)
    graph.add_node("rank", rank_node)

    graph.add_edge(START, "search")
    graph.add_edge("search", "crawl_and_analyze")
    graph.add_edge("crawl_and_analyze", "rank")
    graph.add_edge("rank", END)

    return graph.compile()
def build_roadmap(goal: str) -> dict:
    from pipeline.analyse import generate_roadmap_stages

    stage_data = generate_roadmap_stages(goal)
    if not stage_data:
        return {"goal": goal, "stages": []}

    app = build_graph()
    roadmap_stages = []

    for stage in stage_data["stages"]:
        print(f"🗺️ Building stage {stage['stage_number']}: {stage['title']}")
        initial_state = {
            "topic": stage["search_query"],
            "resource_type": None,
            "price_type": None,
            "difficulty_level": None,
            "candidates": [],
            "analyzed_results": [],
            "ranked_results": []
        }
        final_state = app.invoke(initial_state)
        top_resource = final_state["ranked_results"][0] if final_state["ranked_results"] else None

        roadmap_stages.append({
            "stage_number": stage["stage_number"],
            "title": stage["title"],
            "description": stage["description"],
            "resource": top_resource
        })

    return {"goal": goal, "stages": roadmap_stages}

if __name__ == "__main__":
    app = build_graph()

    topic = input("enter what you want to learn: ").strip()

    if not topic:
        print("You didn't enter anything.")
    else:
        resource_type = input("Filter by resource type (Course/Documentation/Video/Article/Repository, or press Enter to skip): ").strip() or None
        price_type = input("Filter by price (Free/Paid, or press Enter to skip): ").strip() or None
        difficulty_level = input("Filter by difficulty (Beginner/Intermediate/Advanced, or press Enter to skip): ").strip() or None

        initial_state = {
            "topic": topic,
            "resource_type": resource_type,
            "price_type": price_type,
            "difficulty_level": difficulty_level,
            "candidates": [],
            "analyzed_results": [],
            "ranked_results": []
        }
        final_state = app.invoke(initial_state)

        print(f"\n=== TOP RESULTS FOR '{topic}' ===\n")
        print(f"DEBUG: candidates={len(final_state['candidates'])}, analyzed={len(final_state['analyzed_results'])}, ranked={len(final_state['ranked_results'])}")

        if not final_state["ranked_results"]:
            print("⚠️ No results made it through the pipeline.")

        for r in final_state["ranked_results"]:
            print(f"""
📚 {r.title}
⭐ Quality Score: {r.score}/10
🎯 Relevance Score: {r.relevance_score}/10
📅 Freshness: {r.freshness_score}/10 | ⏱️ Est. Time: {r.estimated_minutes} min
💰 {r.price_type}
📝 {r.ai_summary}
🔗 {r.url}
📋 Prerequisites: {', '.join(r.prerequisites) if r.prerequisites else 'None'}
🧠 Skills Taught: {', '.join(r.skills_taught) if r.skills_taught else 'None'}
""")