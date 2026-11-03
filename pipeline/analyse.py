# # import json
# # from groq import Groq
# # import os
# # from dotenv import load_dotenv
# # from model import CrawledPage, AnalyzedResource

# # load_dotenv()
# # client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# # PROMPT_TEMPLATE = """You are evaluating a learning resource for quality.

# # Page URL: {url}
# # Page Content (Markdown):
# # {content}

# # Analyze this resource and respond with ONLY valid JSON, no other text, in this exact format:
# # {{
# #     "title": "short title of the resource",
# #     "score": <float between 0 and 10>,
# #     "reasoning": "1-2 sentence explanation of the score",
# #     "topics_covered": ["topic1", "topic2"],
# #     "difficulty_level": "Beginner" or "Intermediate" or "Advanced",
# #     "ai_summary": "2-3 sentence summary of what this resource actually teaches",
# #     "prerequisites": ["prerequisite1", "prerequisite2"],
# #     "resource_type": "Course" or "Documentation" or "Video" or "Article" or "Repository",
# #     "price_type": "Free" or "Paid" or "Unknown"
# # }}

# # If there are no clear prerequisites, return an empty list for prerequisites.
# # """


# # def extract_relevant_section(markdown: str, keywords: list[str], window: int = 500) -> str:
# #     lower_md = markdown.lower()
# #     for keyword in keywords:
# #         idx = lower_md.find(keyword)
# #         if idx != -1:
# #             return markdown[max(0, idx - 100): idx + window]
# #     return ""


# # def analyze_page(page: CrawledPage) -> AnalyzedResource | None:
# #     prerequisite_section = extract_relevant_section(
# #         page.markdown,
# #         keywords=["prerequisite", "requirement", "before you start", "before starting", "you'll need", "you should know"]
# #     )

# #     combined_content = page.markdown[:8000]
# #     if prerequisite_section and prerequisite_section not in combined_content:
# #         combined_content += f"\n\n--- Additional relevant section ---\n{prerequisite_section}"

# #     prompt = PROMPT_TEMPLATE.format(url=page.url, content=combined_content)

# #     response = client.chat.completions.create(
# #         model="llama-3.3-70b-versatile",
# #         messages=[{"role": "user", "content": prompt}],
# #     )

# #     raw_text = response.choices[0].message.content

# #     try:
# #         data = json.loads(raw_text)
# #         return AnalyzedResource(
# #             url=page.url,
# #             title=data["title"],
# #             score=data["score"],
# #             reasoning=data["reasoning"],
# #             topics_covered=data["topics_covered"],
# #             difficulty_level=data["difficulty_level"],
# #             ai_summary=data["ai_summary"],
# #             prerequisites=data["prerequisites"],
# #             resource_type=data["resource_type"],
# #             price_type=data["price_type"],
# #         )
# #     except Exception as e:
# #         print(f"Skipping {page.url}: could not parse LLM response ({e})")
# #         return None


# # if __name__ == "__main__":
# #     import asyncio
# #     from pipeline.search import search_web
# #     from pipeline.crawl import crawl_page

# #     topic = input("enter what you want to learn: ")
# #     candidates = search_web(topic)

# #     async def run_all():
# #         for candidate in candidates[:10]:
# #             page = await crawl_page(candidate)
# #             if page:
# #                 analyzed = analyze_page(page)
# #                 if analyzed:
# #                     print(f"""
# # 📚 {analyzed.title}
# # 🔗 {analyzed.url}
# # ⭐ Score: {analyzed.score}/10
# # 💰 {analyzed.price_type}
# # 📝 {analyzed.ai_summary}
# # 🎯 Level: {analyzed.difficulty_level}
# # 📋 Prerequisites: {', '.join(analyzed.prerequisites) if analyzed.prerequisites else 'None'}
# # """)

# #     asyncio.run(run_all())
# from groq import Groq
# import json
# import boto3
# import os
# from dotenv import load_dotenv
# from model import CrawledPage, AnalyzedResource
# from pipeline.youtube import is_youtube_url, get_youtube_transcript
# from pipeline.rank import rank_resources

# load_dotenv()
# client = Groq(
#     api_key=os.environ.get("GROQ_API_KEY")
# )
# PROMPT_TEMPLATE = """You are evaluating a learning resource for quality AND relevance.

# The user is searching for: {topic}

# Page URL: {url}
# Page Content (Markdown):
# {content}

# Analyze this resource and respond with ONLY valid JSON, no other text, in this exact format:
# {{
#     "title": "short title of the resource",
#     "score": <float between 0 and 10, quality score>,
#     "relevance_score": <float between 0 and 10, how directly relevant this is to '{topic}' specifically>,
#     "reasoning": "1-2 sentence explanation of the score",
#     "topics_covered": ["topic1", "topic2"],
#     "difficulty_level": "Beginner" or "Intermediate" or "Advanced",
#     "ai_summary": "100 TO 300 WORDS  summary of what this resource actually teaches",
#     "prerequisites": ["prerequisite1", "prerequisite2"],
#     "resource_type": "Course" or "Documentation" or "Video" or "Article" or "Repository",
#     "price_type": "Free" or "Paid" or "Unknown",
#     "skills_taught": ["skill1", "skill2"],
#     "estimated_minutes": <integer, estimated time in minutes to complete this resource>
# }}

# If there are no clear prerequisites, return an empty list for prerequisites.
# """
# COURSE_STRUCTURE_PROMPT_TEMPLATE = """Create a short course outline for the topic: "{topic}"

# Respond with ONLY valid JSON, no other text, in this exact format:
# {{
#     "title": "course title",
#     "description": "2-3 sentence course description",
#     "lessons": [
#         {{
#             "title": "lesson title",
#             "content": "150-250 words of narration-ready teaching content, written in a clear, spoken teaching tone. This must actually TEACH the concept in depth: define it, explain how/why it works, and include at least one concrete example. Do not write a summary or overview of what the lesson will cover — write the full explanation itself, as if narrating the lesson to a student who has never seen this before."
#         }}
#     ]
# }}

# Generate exactly 3 lessons, ordered from foundational to more advanced.
# """


# def generate_course_structure(topic: str) -> dict | None:
#     prompt = COURSE_STRUCTURE_PROMPT_TEMPLATE.format(topic=topic)
#     response = bedrock.converse(
#         modelId="amazon.nova-lite-v1:0",
#         messages=[{"role": "user", "content": [{"text": prompt}]}],
#     )
#     raw_text = response["output"]["message"]["content"][0]["text"]
#     try:
#         return json.loads(raw_text)
#     except Exception as e:
#         print(f"Could not generate course structure: {e}")
#         return None
# from datetime import datetime, timezone

# def compute_freshness_score(published_date: str | None) -> float:
#     if not published_date:
#         return 5.0  # neutral when unknown
#     try:
#         parsed = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
#         if parsed.tzinfo is None:
#             parsed = parsed.replace(tzinfo=timezone.utc)
#         age_days = (datetime.now(timezone.utc) - parsed).days
#         if age_days < 180:
#             return 10.0
#         elif age_days < 365:
#             return 8.0
#         elif age_days < 730:
#             return 6.0
#         elif age_days < 1460:
#             return 4.0
#         else:
#             return 2.0
#     except Exception:
#         return 5.0

# def extract_relevant_section(markdown: str, keywords: list[str], window: int = 500) -> str:
#     lower_md = markdown.lower()
#     for keyword in keywords:
#         idx = lower_md.find(keyword)
#         if idx != -1:
#             return markdown[max(0, idx - 100): idx + window]
#     return ""


# def analyze_page(page: CrawledPage, topic: str,published_date:str|None=None) -> AnalyzedResource | None:
#     if is_youtube_url(page.url):
#         transcript = get_youtube_transcript(page.url)
#         from pipeline.youtube import get_youtube_thumbnail
#         thumbnail_url = get_youtube_thumbnail(page.url)
#         if transcript:
#             print(f"✅ Using real transcript for {page.url} ({len(transcript)} chars)")
#             content_source = transcript
#         else:
#             print(f"⚠️ No transcript available, falling back to page content for {page.url}")
#             content_source = page.markdown
#     else:
#         content_source = page.markdown
#         thumbnail_url = page.thumbnail_url

#     prerequisite_section = extract_relevant_section(
#         content_source,
#         keywords=["prerequisite", "requirement", "before you start", "before starting", "you'll need", "you should know"]
#     )
#     freshness = compute_freshness_score(published_date)
#     combined_content = content_source[:8000]
#     prompt = PROMPT_TEMPLATE.format(url=page.url, content=combined_content,topic=topic)

    
#     response = client.chat.completions.create(
#     model="llama-3.3-70b-versatile",
#     messages=[
#         {
#             "role": "user",
#             "content": prompt
#         }
#     ],
# )

#     raw_text = response["output"]["message"]["content"][0]["text"]

#     try:
#         data = json.loads(raw_text)
#         return AnalyzedResource(
#             url=page.url,
#             title=data["title"],
#             score=data["score"],
#             reasoning=data["reasoning"],
#             topics_covered=data["topics_covered"],
#              published_date=published_date,
#             freshness_score=freshness,
#             difficulty_level=data["difficulty_level"],
#             ai_summary=data["ai_summary"],
#             prerequisites=data["prerequisites"],
#             resource_type=data["resource_type"],
#             price_type=data["price_type"],
#             skills_taught=data.get("skills_taught", []),
#             relevance_score=data.get("relevance_score", 5.0),
#             estimated_minutes=data["estimated_minutes"],
            
#         )
#     except Exception as e:
#         print(f"Skipping {page.url}: could not parse LLM response ({e})")
#         return None
# QUIZ_PROMPT_TEMPLATE = """Based on the following learning resource summary, generate a short quiz to test understanding.

# Resource Title: {title}
# Resource Summary: {summary}
# Topics Covered: {topics}

# Generate exactly 3 multiple-choice questions. Respond with ONLY valid JSON, no other text, in this exact format:
# {{
#     "questions": [
#         {{
#             "question": "question text",
#             "options": ["option A", "option B", "option C", "option D"],
#             "correct_answer_index": <integer 0-3>
#         }}
#     ]
# }}
# """


# def generate_quiz(title: str, summary: str, topics: list[str]) -> dict | None:
#     prompt = QUIZ_PROMPT_TEMPLATE.format(
#         title=title, summary=summary, topics=", ".join(topics)
#     )

#     response = bedrock.converse(
#         modelId="amazon.nova-lite-v1:0",
#         messages=[{"role": "user", "content": [{"text": prompt}]}],
#     )

#     raw_text = response["output"]["message"]["content"][0]["text"]

#     try:
#         data = json.loads(raw_text)
#         return data
#     except Exception as e:
#         print(f"Could not generate quiz: {e}")
#         return None
# PROJECT_PROMPT_TEMPLATE = """Based on the following learning resource, suggest hands-on project ideas 
# to help the learner practice what they would learn.

# Resource Title: {title}
# Resource Summary: {summary}
# Skills Taught: {skills}
# Difficulty Level: {difficulty}

# Generate exactly 3 project ideas, appropriate for someone at the {difficulty} level. 
# Respond with ONLY valid JSON, no other text, in this exact format:
# {{
#     "projects": [
#         {{
#             "title": "short project title",
#             "description": "2-3 sentence description of what to build",
#             "estimated_hours": <integer, rough hours to complete>
#         }}
#     ]
# }}
# """
# SKILL_GAP_PROMPT_TEMPLATE = """A learner has described their current skills as: {user_skills}

# They are considering this learning resource:
# Title: {title}
# Skills Taught: {skills_taught}
# Difficulty Level: {difficulty}

# Analyze the gap between what they already know and what this resource teaches. 
# Respond with ONLY valid JSON, no other text, in this exact format:
# {{
#     "already_known": ["skill1", "skill2"],
#     "new_skills": ["skill1", "skill2"],
#     "gap_summary": "2-3 sentence honest assessment of whether this resource is a good fit given their current skills",
#     "fit_score": <float 0-10, how well this resource matches their current skill gap>
# }}
# """
# ROADMAP_PROMPT_TEMPLATE = """A learner wants to achieve this goal: {goal}

# Break this down into 4 to 5 ordered learning stages, from foundational to advanced. 
# Each stage should be a specific, searchable subtopic.

# Respond with ONLY valid JSON, no other text, in this exact format:
# {{
#     "stages": [
#         {{
#             "stage_number": 1,
#             "title": "short stage title",
#             "search_query": "a specific, searchable topic for this stage",
#             "description": "1-2 sentence description of what this stage covers and why it comes at this point"
#         }}
#     ]
# }}
# """


# def generate_roadmap_stages(goal: str) -> dict | None:
#     prompt = ROADMAP_PROMPT_TEMPLATE.format(goal=goal)
#     response = bedrock.converse(
#         modelId="amazon.nova-lite-v1:0",
#         messages=[{"role": "user", "content": [{"text": prompt}]}],
#     )
#     raw_text = response["output"]["message"]["content"][0]["text"]
#     try:
#         return json.loads(raw_text)
#     except Exception as e:
#         print(f"Could not generate roadmap stages: {e}")

# def analyze_skill_gap(user_skills: str, title: str, skills_taught: list[str], difficulty: str) -> dict | None:
#     prompt = SKILL_GAP_PROMPT_TEMPLATE.format(
#         user_skills=user_skills, title=title, skills_taught=", ".join(skills_taught), difficulty=difficulty
#     )

#     response = bedrock.converse(
#         modelId="amazon.nova-lite-v1:0",
#         messages=[{"role": "user", "content": [{"text": prompt}]}],
#     )

#     raw_text = response["output"]["message"]["content"][0]["text"]

#     try:
#         return json.loads(raw_text)
#     except Exception as e:
#         print(f"Could not analyze skill gap: {e}")
#         return None


# def generate_project_ideas(title: str, summary: str, skills: list[str], difficulty: str) -> dict | None:
#     prompt = PROJECT_PROMPT_TEMPLATE.format(
#         title=title, summary=summary, skills=", ".join(skills), difficulty=difficulty
#     )

#     response = bedrock.converse(
#         modelId="amazon.nova-lite-v1:0",
#         messages=[{"role": "user", "content": [{"text": prompt}]}],
#     )

#     raw_text = response["output"]["message"]["content"][0]["text"]

#     try:
#         data = json.loads(raw_text)
#         return data
#     except Exception as e:
#         print(f"Could not generate project ideas: {e}")
#         return None

# if __name__ == "__main__":
#     import asyncio
#     from pipeline.search import search_web
#     from pipeline.crawl import crawl_page

#     topic = input("enter what you want to learn: ").strip()

#     if not topic:
#         print("You didn't enter anything. Please provide a topic to search for.")
#     else:
#         candidates = search_web(topic)

#         async def run_all():
#             all_results = []
#             for candidate in candidates[:5]:
#                 page = await crawl_page(candidate)
#                 if page:
#                     analyzed = analyze_page(page, topic)

#                     if analyzed:
#                         all_results.append(analyzed)

#             ranked = rank_resources(all_results)

#             print(f"\n=== TOP RESULTS FOR '{topic}' ===\n")
#             for r in ranked:
#                 print(f"""
# 📚 {r.title}
# 🔗 {r.url}
# ⭐ Score: {r.score}/10
# 💰 {r.price_type}
# 📝 {r.ai_summary}
# 🎯 Level: {r.difficulty_level}
# 📋 Prerequisites: {', '.join(r.prerequisites) if r.prerequisites else 'None'}
# 🧠 Skills Taught: {', '.join(r.skills_taught) if r.skills_taught else 'None'}
# """)

#         asyncio.run(run_all())



import json
import os
import re
from datetime import datetime, timezone

import boto3
import groq
from dotenv import load_dotenv
from groq import Groq

from model import CrawledPage, AnalyzedResource
from pipeline.youtube import is_youtube_url, get_youtube_transcript, get_youtube_thumbnail
from pipeline.rank import rank_resources

load_dotenv()


# ---------- config / secrets ----------

def _get_secret(name: str) -> str | None:
    """Read from env (.env locally) first, then Streamlit secrets (cloud)."""
    value = os.environ.get(name)
    if value:
        return value.strip().strip('"').strip("'")
    try:
        import streamlit as st
        value = st.secrets.get(name)
        return str(value).strip() if value else None
    except Exception:
        return None


GROQ_API_KEY = _get_secret("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set (use .env locally or Streamlit Cloud -> Settings -> Secrets)"
    )

client = Groq(api_key=GROQ_API_KEY)

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=_get_secret("AWS_REGION") or "us-east-1",
    aws_access_key_id=_get_secret("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=_get_secret("AWS_SECRET_ACCESS_KEY"),
)

NOVA_MODEL_ID = _get_secret("NOVA_MODEL") or "amazon.nova-lite-v1:0"
GROQ_MODEL_ID = _get_secret("GROQ_MODEL") or "llama-3.3-70b-versatile"
MIN_RELEVANCE = float(_get_secret("MIN_RELEVANCE") or 4.0)


# ---------- prompts ----------

PROMPT_TEMPLATE = """You are evaluating a learning resource for quality AND relevance.

The user is searching for: {topic}

Page URL: {url}
Page Content (Markdown):
{content}

Analyze this resource and respond with ONLY valid JSON, no other text, in this exact format:
{{
    "title": "short title of the resource",
    "score": <float between 0 and 10, quality score>,
    "relevance_score": <float between 0 and 10, how directly relevant this is to '{topic}' specifically>,
    "reasoning": "1-2 sentence explanation of the score",
    "topics_covered": ["topic1", "topic2"],
    "difficulty_level": "Beginner" or "Intermediate" or "Advanced",
    "ai_summary": "100 TO 300 WORDS summary of what this resource actually teaches",
    "prerequisites": ["prerequisite1", "prerequisite2"],
    "resource_type": "Course" or "Documentation" or "Video" or "Article" or "Repository",
    "price_type": "Free" or "Paid" or "Unknown",
    "skills_taught": ["skill1", "skill2"],
    "estimated_minutes": <integer, estimated time in minutes to complete this resource>
}}

If there are no clear prerequisites, return an empty list for prerequisites.
"""

COURSE_STRUCTURE_PROMPT_TEMPLATE = """Create a short course outline for the topic: "{topic}"

Respond with ONLY valid JSON, no other text, in this exact format:
{{
    "title": "course title",
    "description": "2-3 sentence course description",
    "lessons": [
        {{
            "title": "lesson title",
            "content": "150-250 words of narration-ready teaching content, written in a clear, spoken teaching tone. This must actually TEACH the concept in depth: define it, explain how/why it works, and include at least one concrete example. Do not write a summary or overview of what the lesson will cover — write the full explanation itself, as if narrating the lesson to a student who has never seen this before."
        }}
    ]
}}

Generate exactly 3 lessons, ordered from foundational to more advanced.
"""

QUIZ_PROMPT_TEMPLATE = """Based on the following learning resource summary, generate a short quiz to test understanding.

Resource Title: {title}
Resource Summary: {summary}
Topics Covered: {topics}

Generate exactly 3 multiple-choice questions. Respond with ONLY valid JSON, no other text, in this exact format:
{{
    "questions": [
        {{
            "question": "question text",
            "options": ["option A", "option B", "option C", "option D"],
            "correct_answer_index": <integer 0-3>
        }}
    ]
}}
"""

PROJECT_PROMPT_TEMPLATE = """Based on the following learning resource, suggest hands-on project ideas
to help the learner practice what they would learn.

Resource Title: {title}
Resource Summary: {summary}
Skills Taught: {skills}
Difficulty Level: {difficulty}

Generate exactly 3 project ideas, appropriate for someone at the {difficulty} level.
Respond with ONLY valid JSON, no other text, in this exact format:
{{
    "projects": [
        {{
            "title": "short project title",
            "description": "2-3 sentence description of what to build",
            "estimated_hours": <integer, rough hours to complete>
        }}
    ]
}}
"""

SKILL_GAP_PROMPT_TEMPLATE = """A learner has described their current skills as: {user_skills}

They are considering this learning resource:
Title: {title}
Skills Taught: {skills_taught}
Difficulty Level: {difficulty}

Analyze the gap between what they already know and what this resource teaches.
Respond with ONLY valid JSON, no other text, in this exact format:
{{
    "already_known": ["skill1", "skill2"],
    "new_skills": ["skill1", "skill2"],
    "gap_summary": "2-3 sentence honest assessment of whether this resource is a good fit given their current skills",
    "fit_score": <float 0-10, how well this resource matches their current skill gap>
}}
"""

ROADMAP_PROMPT_TEMPLATE = """A learner wants to achieve this goal: {goal}

Break this down into 4 to 5 ordered learning stages, from foundational to advanced.
Each stage should be a specific, searchable subtopic.

Respond with ONLY valid JSON, no other text, in this exact format:
{{
    "stages": [
        {{
            "stage_number": 1,
            "title": "short stage title",
            "search_query": "a specific, searchable topic for this stage",
            "description": "1-2 sentence description of what this stage covers and why it comes at this point"
        }}
    ]
}}
"""


# ---------- helpers ----------

def parse_llm_json(raw_text: str) -> dict:
    """Parse JSON from an LLM reply, tolerating ```json fences and surrounding text."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


def call_nova(prompt: str) -> str:
    response = bedrock.converse(
        modelId=NOVA_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    return response["output"]["message"]["content"][0]["text"]


def call_nova_json(prompt: str, label: str) -> dict | None:
    try:
        return parse_llm_json(call_nova(prompt))
    except Exception as e:
        print(f"Could not generate {label}: {e}")
        return None


def compute_freshness_score(published_date: str | None) -> float:
    if not published_date:
        return 5.0  # neutral when unknown
    try:
        parsed = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - parsed).days
        if age_days < 180:
            return 10.0
        elif age_days < 365:
            return 8.0
        elif age_days < 730:
            return 6.0
        elif age_days < 1460:
            return 4.0
        else:
            return 2.0
    except Exception:
        return 5.0


def extract_relevant_section(markdown: str, keywords: list[str], window: int = 500) -> str:
    lower_md = markdown.lower()
    for keyword in keywords:
        idx = lower_md.find(keyword)
        if idx != -1:
            return markdown[max(0, idx - 100): idx + window]
    return ""


# ---------- Groq: resource analysis ----------

def analyze_page(page: CrawledPage, topic: str, published_date: str | None = None) -> AnalyzedResource | None:
    if is_youtube_url(page.url):
        transcript = get_youtube_transcript(page.url)
        thumbnail_url = get_youtube_thumbnail(page.url)  # not stored; add a field to AnalyzedResource if needed
        if transcript:
            print(f"✅ Using real transcript for {page.url} ({len(transcript)} chars)")
            content_source = transcript
        else:
            print(f"⚠️ No transcript available, falling back to page content for {page.url}")
            content_source = page.markdown
    else:
        content_source = page.markdown
        thumbnail_url = page.thumbnail_url

    prerequisite_section = extract_relevant_section(
        content_source,
        keywords=["prerequisite", "requirement", "before you start", "before starting", "you'll need", "you should know"],
    )
    freshness = compute_freshness_score(published_date)

    combined_content = content_source[:8000]
    if prerequisite_section and prerequisite_section not in combined_content:
        combined_content += f"\n\n--- Additional relevant section ---\n{prerequisite_section}"

    prompt = PROMPT_TEMPLATE.format(url=page.url, content=combined_content, topic=topic)

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        data = parse_llm_json(response.choices[0].message.content)

        relevance = float(data.get("relevance_score", 5.0))
        if relevance < MIN_RELEVANCE:
            print(f"Dropping {page.url}: relevance {relevance} < {MIN_RELEVANCE}")
            return None

        return AnalyzedResource(
            url=page.url,
            title=data["title"],
            score=data["score"],
            reasoning=data["reasoning"],
            topics_covered=data["topics_covered"],
            published_date=published_date,
            freshness_score=freshness,
            difficulty_level=data["difficulty_level"],
            ai_summary=data["ai_summary"],
            prerequisites=data.get("prerequisites", []),
            resource_type=data["resource_type"],
            price_type=data["price_type"],
            skills_taught=data.get("skills_taught", []),
            relevance_score=relevance,
            estimated_minutes=data.get("estimated_minutes", 0),
        )
    except (groq.AuthenticationError, groq.NotFoundError) as e:
        # Config problems (bad key / bad model id): fail loudly instead of skipping every page.
        raise RuntimeError(
            f"Groq rejected the request (model='{GROQ_MODEL_ID}'): {e}. "
            "Check GROQ_API_KEY and GROQ_MODEL in secrets."
        ) from e
    except Exception as e:
        print(f"Skipping {page.url}: could not analyze ({e})")
        return None


# ---------- Bedrock Nova: generators ----------

def generate_course_structure(topic: str) -> dict | None:
    return call_nova_json(COURSE_STRUCTURE_PROMPT_TEMPLATE.format(topic=topic), "course structure")


def generate_quiz(title: str, summary: str, topics: list[str]) -> dict | None:
    prompt = QUIZ_PROMPT_TEMPLATE.format(title=title, summary=summary, topics=", ".join(topics))
    return call_nova_json(prompt, "quiz")


def generate_roadmap_stages(goal: str) -> dict | None:
    return call_nova_json(ROADMAP_PROMPT_TEMPLATE.format(goal=goal), "roadmap stages")


def analyze_skill_gap(user_skills: str, title: str, skills_taught: list[str], difficulty: str) -> dict | None:
    prompt = SKILL_GAP_PROMPT_TEMPLATE.format(
        user_skills=user_skills,
        title=title,
        skills_taught=", ".join(skills_taught),
        difficulty=difficulty,
    )
    return call_nova_json(prompt, "skill gap analysis")


def generate_project_ideas(title: str, summary: str, skills: list[str], difficulty: str) -> dict | None:
    prompt = PROJECT_PROMPT_TEMPLATE.format(
        title=title, summary=summary, skills=", ".join(skills), difficulty=difficulty
    )
    return call_nova_json(prompt, "project ideas")


# ---------- CLI ----------

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
            all_results = []
            for candidate in candidates[:5]:
                page = await crawl_page(candidate)
                if page:
                    analyzed = analyze_page(page, topic)
                    if analyzed:
                        all_results.append(analyzed)

            ranked = rank_resources(all_results)

            print(f"\n=== TOP RESULTS FOR '{topic}' ===\n")
            for r in ranked:
                print(f"""
📚 {r.title}
🔗 {r.url}
⭐ Score: {r.score}/10
💰 {r.price_type}
📝 {r.ai_summary}
🎯 Level: {r.difficulty_level}
📋 Prerequisites: {', '.join(r.prerequisites) if r.prerequisites else 'None'}
🧠 Skills Taught: {', '.join(r.skills_taught) if r.skills_taught else 'None'}
""")

        asyncio.run(run_all())