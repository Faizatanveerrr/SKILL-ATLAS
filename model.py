from pydantic import BaseModel 
from typing import Optional
class  CandidateURL(BaseModel):
    url:str
    title:str
    snippet:str
    published_date:Optional[str]=None
    source_query:str
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