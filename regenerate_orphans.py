"""
One-off script: regenerates the video file for every lesson whose
video_path no longer points to a real file on disk, and updates the DB
to point at the new file.

Run from the project root:
    python regenerate_orphans.py
"""
from pipeline.storage import find_orphaned_lessons, update_lesson_video
from pipeline.video_generator import create_lesson_video
import uuid

orphans = find_orphaned_lessons()

if not orphans:
    print("✅ No orphaned lessons — nothing to regenerate.")
else:
    print(f"Found {len(orphans)} orphaned lesson(s). Regenerating...\n")

    succeeded = 0
    failed = []

    for o in orphans:
        lesson_id = o["lesson_id"]
        title = o["title"]
        content_text = o["content_text"]

        print(f"[{lesson_id}] Regenerating '{title}'...")
        try:
            new_id = f"regen_{lesson_id}_{str(uuid.uuid4())[:6]}"
            new_path = create_lesson_video(title, content_text, new_id)
            update_lesson_video(lesson_id, new_path)
            print(f"    -> saved to {new_path}")
            succeeded += 1
        except Exception as e:
            print(f"    ❌ failed: {e}")
            failed.append((lesson_id, title, str(e)))

    print(f"\nDone. {succeeded}/{len(orphans)} regenerated successfully.")
    if failed:
        print(f"{len(failed)} failed:")
        for lesson_id, title, err in failed:
            print(f"  [{lesson_id}] '{title}': {err}")