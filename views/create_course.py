import os
import streamlit as st
from shared import apply_custom_css
from pipeline.storage import (
    init_db,
    create_course,
    get_courses_for_user,
    add_lesson,
    get_lessons_for_course,
    update_lesson_video,
)
from pipeline.video_generator import create_lesson_video
from pipeline.analyse import generate_course_structure
import uuid

init_db()
apply_custom_css()

st.markdown('<p class="main-title">🎬 Micro-Lessons</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Type a topic — get a set of short, auto-generated video lessons.</p>', unsafe_allow_html=True)

username = st.session_state.get("username")

topic = st.text_input("What do you want a set of micro-lessons on?", placeholder="e.g. Python basics")

if st.button("🚀 Generate Micro-Lessons") and topic.strip():
    with st.spinner("Designing your micro-lessons..."):
        structure = generate_course_structure(topic.strip())

    if not structure:
        st.error("Could not generate micro-lessons. Try a different topic.")
    else:
        course_id = create_course(username, structure["title"], structure["description"])

        progress = st.progress(0, text="Starting...")
        total = len(structure["lessons"])
        for i, lesson in enumerate(structure["lessons"]):
            progress.progress((i) / total, text=f"Generating video for: {lesson['title']}")
            lesson_id = str(uuid.uuid4())[:8]
            try:
                video_path = create_lesson_video(lesson["title"], lesson["content"], lesson_id)
                add_lesson(course_id, lesson["title"], lesson["content"], video_path)
            except Exception as e:
                st.error(f"Failed to generate video for '{lesson['title']}': {e}")
                continue

st.divider()

courses = get_courses_for_user(username)
if courses:
    st.subheader("Your Micro-Lessons")
    course_titles = {c["title"]: c["course_id"] for c in courses}
    selected_title = st.selectbox("View a set of micro-lessons", list(course_titles.keys()))
    selected_id = course_titles[selected_title]

    lessons = get_lessons_for_course(selected_id)
    for lesson in lessons:
        st.write(f"**Lesson {lesson['lesson_number']}: {lesson['title']}**")

        video_path = lesson["video_path"]
        if video_path and os.path.exists(video_path):
            st.video(video_path)
        else:
            st.warning("⚠️ Video file for this lesson is missing (it may have been moved, deleted, or generated on a different machine).")
            if st.button("🔄 Regenerate this lesson's video", key=f"regen_{lesson['lesson_id']}"):
                with st.spinner("Regenerating video..."):
                    try:
                        new_path = create_lesson_video(
                            lesson["title"], lesson["content_text"], f"regen_{lesson['lesson_id']}_{str(uuid.uuid4())[:6]}"
                        )
                        update_lesson_video(lesson["lesson_id"], new_path)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Regeneration failed: {e}")

        st.divider()