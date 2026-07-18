import asyncio 
from crawl4ai  import AsyncWebCrawler 
async def main():
    async with AsyncWebCrawler() as crawler:
        result=await crawler.arun(url="https://docs.langchain.com/langgraph")
        print(result.markdown[:1000])
if __name__=="__main__":
    asyncio.run(main())


