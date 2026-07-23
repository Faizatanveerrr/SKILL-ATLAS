from pydantic import BaseModel 
from typing import Optional
class  CandidateURL(BaseModel):
    url:str
    title:str
    snippet:str
    published_date:Optional[str]=None
    source_query:str
    
class CrawledPage(BaseModel):
    url:str
    markdown:str
    thumbnail_url: Optional[str] = None
class AnalyzedResource(BaseModel):
    url: str
    title: str
    score: float
    reasoning: str
    topics_covered: list[str]
    difficulty_level: str
    ai_summary: str
    prerequisites: list[str]
    resource_type: str
    price_type: str
    skills_taught: list[str]
    relevance_score: float
    thumbnail_url: Optional[str] = None
    published_date: Optional[str] = None
    freshness_score: float=0.0
    estimated_minutes: int=0
if __name__ == "__main__":
    test_result = CandidateURL(
        url="https://docs.langchain.com/langgraph",
        title="LangGraph Documentation",
        snippet="Official docs for LangGraph...",
        source_query="LangGraph official documentation"
    )
    print(test_result)

    bad_result = CandidateURL(
        title="Missing URL Example",
        snippet="This should fail",
        source_query="test"
    )
    print(bad_result)
