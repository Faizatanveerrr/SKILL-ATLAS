import sqlite3
import json
from datetime import datetime
from model import AnalyzedResource

DB_PATH = "skill_atlas.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS analyzed_resources (
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
    thumbnail_url TEXT,
    published_date TEXT,
    freshness_score REAL,
    estimated_minutes INTEGER,
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_items (
            playlist_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            topic TEXT NOT NULL,
            position INTEGER,
            FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id)
        )
    """)
    conn.commit()
    conn.close()

def create_playlist(username: str, name: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO playlists (username, name, created_at) VALUES (?, ?, ?)",
        (username, name, datetime.now().isoformat())
    )
    playlist_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return playlist_id


def get_playlists_for_user(username: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT playlist_id, name, created_at FROM playlists WHERE username = ? ORDER BY created_at DESC",
        (username,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"playlist_id": r[0], "name": r[1], "created_at": r[2]} for r in rows]


def add_to_playlist(playlist_id: int, url: str, topic: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM playlist_items WHERE playlist_id = ?", (playlist_id,))
    next_position = cursor.fetchone()[0]
    cursor.execute(
        "INSERT INTO playlist_items (playlist_id, url, topic, position) VALUES (?, ?, ?, ?)",
        (playlist_id, url, topic, next_position)
    )
    conn.commit()
    conn.close()


def get_playlist_items(playlist_id: int) -> list[AnalyzedResource]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ar.* FROM playlist_items pi
        JOIN analyzed_resources ar ON pi.url = ar.url AND pi.topic = ar.topic
        WHERE pi.playlist_id = ?
        ORDER BY pi.position
    """, (playlist_id,))
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
            thumbnail_url=row[13], published_date=row[14],
            freshness_score=row[15], estimated_minutes=row[16],
        ))
    return results


def delete_playlist(playlist_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM playlist_items WHERE playlist_id = ?", (playlist_id,))
    cursor.execute("DELETE FROM playlists WHERE playlist_id = ?", (playlist_id,))
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
        thumbnail_url=row[13],
        published_date=row[14],
        freshness_score=row[15],
        estimated_minutes=row[16],
    )

def save_result(resource: AnalyzedResource, topic: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO analyzed_resources
        (url, topic, title, score, relevance_score, reasoning, topics_covered,
         difficulty_level, ai_summary, prerequisites, resource_type, price_type,
         skills_taught, thumbnail_url, published_date, freshness_score, estimated_minutes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        resource.url, topic, resource.title, resource.score, resource.relevance_score,
        resource.reasoning, json.dumps(resource.topics_covered), resource.difficulty_level,
        resource.ai_summary, json.dumps(resource.prerequisites), resource.resource_type,
        resource.price_type, json.dumps(resource.skills_taught), resource.thumbnail_url,
        resource.published_date, resource.freshness_score, resource.estimated_minutes,
        datetime.now().isoformat()
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
def get_user_stats(username: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM search_history WHERE username = ?", (username,))
    search_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM saved_resources WHERE username = ?", (username,))
    saved_count = cursor.fetchone()[0]
    conn.close()
    return {"search_count": search_count, "saved_count": saved_count}
def get_resource_type_breakdown(username: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ar.resource_type, COUNT(*) FROM saved_resources sr
        JOIN analyzed_resources ar ON sr.url = ar.url AND sr.topic = ar.topic
        WHERE sr.username = ?
        GROUP BY ar.resource_type
    """, (username,))
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def get_most_searched_topic(username: str) -> str | None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT topic, COUNT(*) as cnt FROM search_history
        WHERE username = ? GROUP BY topic ORDER BY cnt DESC LIMIT 1
    """, (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

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