from dotenv import load_dotenv
from tavily import TavilyClient
import os

load_dotenv()
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

response = client.search(query="Learn LangGraph", max_results=3)
print(response)