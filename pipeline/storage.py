import sqlite3
import json
from datetime import datetime
from model import AnalyzedResource

DB_PATH = "skill_atlas.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyzed_resources (
            url TEXT NOT NULL,
            topic TEXT NOT NULL,
            title TEXT,
            score REAL,
            relevance_score REAL,
            reasoning TEXT,
            topics_covered TEXT,
            difficulty_level TEXT,
            ai_summary TEXT,
            prerequisites TEXT,
            resource_type TEXT,
            price_type TEXT,
            skills_taught TEXT,
            created_at TEXT,
            PRIMARY KEY (url, topic)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_resources (
            username TEXT NOT NULL,
            url TEXT NOT NULL,
            topic TEXT NOT NULL,
            saved_at TEXT,
            PRIMARY KEY (username, url)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            username TEXT NOT NULL,
            topic TEXT NOT NULL,
            result_count INTEGER,
            searched_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_cached_result(url: str, topic: str) -> AnalyzedResource | None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM analyzed_resources WHERE url = ? AND topic = ?",
        (url, topic)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return AnalyzedResource(
        url=row[0],
        title=row[2],
        score=row[3],
        relevance_score=row[4],
        reasoning=row[5],
        topics_covered=json.loads(row[6]),
        difficulty_level=row[7],
        ai_summary=row[8],
        prerequisites=json.loads(row[9]),
        resource_type=row[10],
        price_type=row[11],
        skills_taught=json.loads(row[12]),
    )


def save_result(resource: AnalyzedResource, topic: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO analyzed_resources
        (url, topic, title, score, relevance_score, reasoning, topics_covered,
         difficulty_level, ai_summary, prerequisites, resource_type, price_type,
         skills_taught, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        resource.url, topic, resource.title, resource.score, resource.relevance_score,
        resource.reasoning, json.dumps(resource.topics_covered), resource.difficulty_level,
        resource.ai_summary, json.dumps(resource.prerequisites), resource.resource_type,
        resource.price_type, json.dumps(resource.skills_taught), datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
def save_resource_for_user(username: str, url: str, topic: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO saved_resources (username, url, topic, saved_at)
        VALUES (?, ?, ?, ?)
    """, (username, url, topic, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_saved_resources_for_user(username: str) -> list[AnalyzedResource]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ar.* FROM analyzed_resources ar
        JOIN saved_resources sr ON ar.url = sr.url AND ar.topic = sr.topic
        WHERE sr.username = ?
        ORDER BY sr.saved_at DESC
    """, (username,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append(AnalyzedResource(
            url=row[0], title=row[2], score=row[3], relevance_score=row[4],
            reasoning=row[5], topics_covered=json.loads(row[6]),
            difficulty_level=row[7], ai_summary=row[8],
            prerequisites=json.loads(row[9]), resource_type=row[10],
            price_type=row[11], skills_taught=json.loads(row[12]),
        ))
    return results


def is_saved(username: str, url: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM saved_resources WHERE username = ? AND url = ?", (username, url))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def log_search(username: str, topic: str, result_count: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO search_history (username, topic, result_count, searched_at)
        VALUES (?, ?, ?, ?)
    """, (username, topic, result_count, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_search_history_for_user(username: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT topic, result_count, searched_at FROM search_history
        WHERE username = ? ORDER BY searched_at DESC
    """, (username,))
    rows = cursor.fetchall()
    conn.close()
    return [{"topic": r[0], "result_count": r[1], "time": r[2]} for r in rows]
if __name__ == "__main__":
    from model import AnalyzedResource

    init_db()

    test_resource = AnalyzedResource(
        url="https://example.com/test-course",
        title="Test Course",
        score=9.0,
        relevance_score=8.5,
        reasoning="This is a test entry.",
        topics_covered=["Testing", "SQLite"],
        difficulty_level="Beginner",
        ai_summary="A fake resource used to test the storage layer.",
        prerequisites=["None"],
        resource_type="Course",
        price_type="Free",
        skills_taught=["Database basics", "Testing"],
    )

    print("Saving test resource...")
    save_result(test_resource, topic="testing sqlite")

    print("Retrieving it back...")
    retrieved = get_cached_result("https://example.com/test-course", "testing sqlite")

    if retrieved:
        print("✅ Successfully retrieved from database:")
        print(retrieved)
    else:
        print("❌ Something went — nothing was retrieved.")