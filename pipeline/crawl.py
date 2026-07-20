import asyncio
from crawl4ai import AsyncWebCrawler
from model import CandidateURL, CrawledPage


async def crawl_page(candidate: CandidateURL, crawler: AsyncWebCrawler) -> CrawledPage | None:
    result = await crawler.arun(url=candidate.url)
    if not result.success:
        print(f"Failed to crawl {candidate.url}")
        return None
    return CrawledPage(url=candidate.url, markdown=result.markdown)