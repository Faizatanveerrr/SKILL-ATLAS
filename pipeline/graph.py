from typing import TypedDict, Callable, Optional
from model import CandidateURL, AnalyzedResource
from pipeline.search import search_web
from pipeline.crawl import crawl_page
from pipeline.analyse import analyze_page
from pipeline.rank import rank_resources, dedupe_resources
from langgraph.graph import StateGraph, START, END
import asyncio
from crawl4ai import AsyncWebCrawler
from pipeline.storage import init_db, get_cached_result, save_result

# How many unique analyzed resources we want to end up with per topic,
# and how hard we're willing to try to get there.
TARGET_RESULT_COUNT = 5
MAX_SEARCH_ATTEMPTS = 3
SEARCH_BATCH_SIZE = 8  # candidates requested per search attempt


class PipelineState(TypedDict):
    topic: str
    resource_type: str | None
    price_type: str | None
    difficulty_level: str | None
    candidates: list[CandidateURL]
    analyzed_results: list[AnalyzedResource]
    ranked_results: list[AnalyzedResource]


def search_node(state: PipelineState) -> dict:
    candidates = search_web(state["topic"], max_result=SEARCH_BATCH_SIZE)
    return {"candidates": candidates}


def crawl_and_analyze_node(state: PipelineState) -> dict:

    async def analyze_batch(candidates: list[CandidateURL], crawler: AsyncWebCrawler) -> list[AnalyzedResource]:
        async def crawl_and_analyze_one(candidate: CandidateURL):
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

        tasks = [crawl_and_analyze_one(c) for c in candidates]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def process_all() -> list[AnalyzedResource]:
        seen_urls: set[str] = set()
        all_analyzed: list[AnalyzedResource] = []

        async with AsyncWebCrawler() as crawler:
            candidates = state["candidates"][:SEARCH_BATCH_SIZE]

            for attempt in range(1, MAX_SEARCH_ATTEMPTS + 1):
                new_candidates = [c for c in candidates if c.url.rstrip("/").lower() not in seen_urls]

                if new_candidates:
                    batch = await analyze_batch(new_candidates, crawler)
                    all_analyzed.extend(batch)
                    for c in new_candidates:
                        seen_urls.add(c.url.rstrip("/").lower())

                unique_count = len(dedupe_resources(all_analyzed))
                print(f"🔎 Attempt {attempt}: {unique_count} unique resources so far (target {TARGET_RESULT_COUNT})")

                if unique_count >= TARGET_RESULT_COUNT:
                    break

                if attempt == MAX_SEARCH_ATTEMPTS:
                    print("⚠️ Reached max search attempts, returning what we have.")
                    break

                print(f"♻️ Only {unique_count} unique results, searching for more candidates...")
                extra_query = f"{state['topic']} guide" if attempt == 1 else f"{state['topic']} resources"
                more_candidates = search_web(extra_query, max_result=SEARCH_BATCH_SIZE)
                candidates = [c for c in more_candidates if c.url.rstrip("/").lower() not in seen_urls]

        return all_analyzed

    analyzed_results = asyncio.run(process_all())
    return {"analyzed_results": analyzed_results}


def rank_node(state: PipelineState) -> dict:
    ranked = rank_resources(
        state["analyzed_results"],
        resource_type=state.get("resource_type"),
        price_type=state.get("price_type"),
        difficulty_level=state.get("difficulty_level"),
        top_n=TARGET_RESULT_COUNT,
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


def run_pipeline_streaming(
    topic: str,
    resource_type: Optional[str] = None,
    price_type: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    on_result: Optional[Callable[[AnalyzedResource], None]] = None,
) -> dict:
    """
    Same search -> crawl -> analyze -> rank pipeline as build_graph(), but calls
    on_result(resource) the moment EACH resource finishes analysis, instead of
    blocking until the entire batch completes like app.invoke() does.

    This exists specifically so a Streamlit view can render results as they
    arrive rather than sitting on a spinner until every candidate is done.
    Final deduped + ranked results are still returned at the end, in the same
    shape as build_graph()'s output, for persisting to session state / DB.
    """
    all_analyzed: list[AnalyzedResource] = []
    seen_urls: set[str] = set()

    async def crawl_and_analyze_one(candidate: CandidateURL, crawler: AsyncWebCrawler):
        cached = get_cached_result(candidate.url, topic)
        if cached:
            return cached
        page = await crawl_page(candidate, crawler)
        if page:
            analyzed = analyze_page(page, topic, published_date=candidate.published_date)
            if analyzed:
                save_result(analyzed, topic)
            return analyzed
        return None

    async def process_all():
        candidates = search_web(topic, max_result=SEARCH_BATCH_SIZE)

        async with AsyncWebCrawler() as crawler:
            for attempt in range(1, MAX_SEARCH_ATTEMPTS + 1):
                new_candidates = [c for c in candidates if c.url.rstrip("/").lower() not in seen_urls]

                if new_candidates:
                    tasks = [asyncio.create_task(crawl_and_analyze_one(c, crawler)) for c in new_candidates]
                    # as_completed yields each task the moment IT finishes,
                    # not when the whole batch finishes — this is the core of
                    # the fix: render as soon as one result is ready.
                    for coro in asyncio.as_completed(tasks):
                        result = await coro
                        if result is not None:
                            all_analyzed.append(result)
                            if on_result:
                                on_result(result)
                    for c in new_candidates:
                        seen_urls.add(c.url.rstrip("/").lower())

                unique_count = len(dedupe_resources(all_analyzed))
                if unique_count >= TARGET_RESULT_COUNT:
                    break
                if attempt == MAX_SEARCH_ATTEMPTS:
                    break

                extra_query = f"{topic} guide" if attempt == 1 else f"{topic} resources"
                more_candidates = search_web(extra_query, max_result=SEARCH_BATCH_SIZE)
                candidates = [c for c in more_candidates if c.url.rstrip("/").lower() not in seen_urls]

    asyncio.run(process_all())

    ranked = rank_resources(
        all_analyzed,
        resource_type=resource_type,
        price_type=price_type,
        difficulty_level=difficulty_level,
        top_n=TARGET_RESULT_COUNT,
    )
    return {"analyzed_results": all_analyzed, "ranked_results": ranked}


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