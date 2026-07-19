# import json
# from groq import Groq
# import os
# from dotenv import load_dotenv
# from model import CrawledPage, AnalyzedResource

# load_dotenv()
# client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# PROMPT_TEMPLATE = """You are evaluating a learning resource for quality.

# Page URL: {url}
# Page Content (Markdown):
# {content}

# Analyze this resource and respond with ONLY valid JSON, no other text, in this exact format:
# {{
#     "title": "short title of the resource",
#     "score": <float between 0 and 10>,
#     "reasoning": "1-2 sentence explanation of the score",
#     "topics_covered": ["topic1", "topic2"],
#     "difficulty_level": "Beginner" or "Intermediate" or "Advanced",
#     "ai_summary": "2-3 sentence summary of what this resource actually teaches",
#     "prerequisites": ["prerequisite1", "prerequisite2"],
#     "resource_type": "Course" or "Documentation" or "Video" or "Article" or "Repository",
#     "price_type": "Free" or "Paid" or "Unknown"
# }}

# If there are no clear prerequisites, return an empty list for prerequisites.
# """


# def extract_relevant_section(markdown: str, keywords: list[str], window: int = 500) -> str:
#     lower_md = markdown.lower()
#     for keyword in keywords:
#         idx = lower_md.find(keyword)
#         if idx != -1:
#             return markdown[max(0, idx - 100): idx + window]
#     return ""


# def analyze_page(page: CrawledPage) -> AnalyzedResource | None:
#     prerequisite_section = extract_relevant_section(
#         page.markdown,
#         keywords=["prerequisite", "requirement", "before you start", "before starting", "you'll need", "you should know"]
#     )

#     combined_content = page.markdown[:8000]
#     if prerequisite_section and prerequisite_section not in combined_content:
#         combined_content += f"\n\n--- Additional relevant section ---\n{prerequisite_section}"

#     prompt = PROMPT_TEMPLATE.format(url=page.url, content=combined_content)

#     response = client.chat.completions.create(
#         model="llama-3.3-70b-versatile",
#         messages=[{"role": "user", "content": prompt}],
#     )

#     raw_text = response.choices[0].message.content

#     try:
#         data = json.loads(raw_text)
#         return AnalyzedResource(
#             url=page.url,
#             title=data["title"],
#             score=data["score"],
#             reasoning=data["reasoning"],
#             topics_covered=data["topics_covered"],
#             difficulty_level=data["difficulty_level"],
#             ai_summary=data["ai_summary"],
#             prerequisites=data["prerequisites"],
#             resource_type=data["resource_type"],
#             price_type=data["price_type"],
#         )
#     except Exception as e:
#         print(f"Skipping {page.url}: could not parse LLM response ({e})")
#         return None


# if __name__ == "__main__":
#     import asyncio
#     from pipeline.search import search_web
#     from pipeline.crawl import crawl_page

#     topic = input("enter what you want to learn: ")
#     candidates = search_web(topic)

#     async def run_all():
#         for candidate in candidates[:10]:
#             page = await crawl_page(candidate)
#             if page:
#                 analyzed = analyze_page(page)
#                 if analyzed:
#                     print(f"""
# 📚 {analyzed.title}
# 🔗 {analyzed.url}
# ⭐ Score: {analyzed.score}/10
# 💰 {analyzed.price_type}
# 📝 {analyzed.ai_summary}
# 🎯 Level: {analyzed.difficulty_level}
# 📋 Prerequisites: {', '.join(analyzed.prerequisites) if analyzed.prerequisites else 'None'}
# """)

#     asyncio.run(run_all())
import json
import boto3
import os
from dotenv import load_dotenv
from model import CrawledPage, AnalyzedResource
from pipeline.youtube import is_youtube_url, get_youtube_transcript

load_dotenv()

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_REGION"),
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)

PROMPT_TEMPLATE = """You are evaluating a learning resource for quality.

Page URL: {url}
Page Content (Markdown):
{content}

Analyze this resource and respond with ONLY valid JSON, no other text, in this exact format:
{{
    "title": "short title of the resource",
    "score": <float between 0 and 10>,
    "reasoning": "1-2 sentence explanation of the score",
    "topics_covered": ["topic1", "topic2"],
    "difficulty_level": "Beginner" or "Intermediate" or "Advanced",
    "ai_summary": "2-3 sentence summary of what this resource actually teaches",
    "prerequisites": ["prerequisite1", "prerequisite2"],
    "resource_type": "Course" or "Documentation" or "Video" or "Article" or "Repository",
    "price_type": "Free" or "Paid" or "Unknown",
    "skills_taught": ["skill1", "skill2"]
}}

If there are no clear prerequisites, return an empty list for prerequisites.
"""


def extract_relevant_section(markdown: str, keywords: list[str], window: int = 500) -> str:
    lower_md = markdown.lower()
    for keyword in keywords:
        idx = lower_md.find(keyword)
        if idx != -1:
            return markdown[max(0, idx - 100): idx + window]
    return ""


def analyze_page(page: CrawledPage) -> AnalyzedResource | None:
    if is_youtube_url(page.url):
        transcript = get_youtube_transcript(page.url)
        content_source = transcript if transcript else page.markdown
    else:
        content_source = page.markdown

    prerequisite_section = extract_relevant_section(
        content_source,
        keywords=["prerequisite", "requirement", "before you start", "before starting", "you'll need", "you should know"]
    )

    combined_content = content_source[:8000]
    prompt = PROMPT_TEMPLATE.format(url=page.url, content=combined_content)

    print(f"--- Content sent to LLM ---\n{combined_content[:2000]}...\n--- END ---")

    response = bedrock.converse(
        modelId="amazon.nova-lite-v1:0",
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
    )

    raw_text = response["output"]["message"]["content"][0]["text"]

    try:
        data = json.loads(raw_text)
        return AnalyzedResource(
            url=page.url,
            title=data["title"],
            score=data["score"],
            reasoning=data["reasoning"],
            topics_covered=data["topics_covered"],
            difficulty_level=data["difficulty_level"],
            ai_summary=data["ai_summary"],
            prerequisites=data["prerequisites"],
            resource_type=data["resource_type"],
            price_type=data["price_type"],
            skills_taught=data["skills_taught"],
        )
    except Exception as e:
        print(f"Skipping {page.url}: could not parse LLM response ({e})")
        return None

if __name__ == "__main__":
    import asyncio
    from pipeline.search import search_web
    from pipeline.crawl import crawl_page

    topic = input("enter what you want to learn: ").strip()

    if not topic:
        print("You didn't enter anything. Please provide a topic to search for.")
    else:
        candidates = search_web(topic)

        async def run_all():
            for candidate in candidates[:2]:
                page = await crawl_page(candidate)
                if page:
                    analyzed = analyze_page(page)
                    if analyzed:
                        print(f"""
📚 {analyzed.title}
🔗 {analyzed.url}
⭐ Score: {analyzed.score}/10
💰 {analyzed.price_type}
📝 {analyzed.ai_summary}
🎯 Level: {analyzed.difficulty_level}
📋 Prerequisites: {', '.join(analyzed.prerequisites) if analyzed.prerequisites else 'None'}
🧠 Skills Taught: {', '.join(analyzed.skills_taught) if analyzed.skills_taught else 'None'}
""")

        asyncio.run(run_all())