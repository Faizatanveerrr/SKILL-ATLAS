from dotenv import load_dotenv
from tavily import TavilyClient
import os 
from model import CandidateURL
load_dotenv()
# To install: pip install tavily-python

client = TavilyClient("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")

def search_web(topic: str, max_result: int = 10) -> list[CandidateURL]:
    course_query = f"{topic} course tutorial for beginners"
    response = client.search(query=course_query, max_results=max_result)
    raw_results = response.get("results", [])
    candidates = []
    for item in raw_results:
        try:
            candidate = CandidateURL(
                url=item["url"],
                title=item["title"],
                snippet=item["content"],
                published_date=item.get("published_date"),
                source_query=course_query
            )
            candidates.append(candidate)
        except Exception as e:
            print(f"skipping bad result {e}")
            continue
    return candidates
if __name__=="__main__":
        user_input=input("enter what you want to learn")
        results=search_web(user_input)
        for r in results:
            print(r)
    