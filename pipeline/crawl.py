import asyncio
from crawl4ai import AsyncWebCrawler
from model import CandidateURL ,CrawledPage
async def crawl_page(candidate:CandidateURL)-> CrawledPage|None:
    async with AsyncWebCrawler() as crawler:
        result=await crawler.arun(url=candidate.url)
        if not result.success:
            print("Failed to crawl {candidate.url}")
            return None
        return  CrawledPage(url=candidate.url,markdown=result.markdown)
if __name__ == "__main__":
    from pipeline.search import search_web

    topic = input("enter what you want to learn: ")
    candidates = search_web(topic)

    async def run_all():
        for candidate in candidates[:2]:  # just test first 2 for now
            page = await crawl_page(candidate)
            if page:
                print(page.url)
                print(page.markdown[:300])
                print("---")

    asyncio.run(run_all())   