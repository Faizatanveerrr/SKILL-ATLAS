import os
import uuid
import streamlit as st

from shared import apply_custom_css
from pipeline.storage import (
    init_db,
    create_course,
    get_courses_for_user,
    add_lesson,
    get_lessons_for_course,
    update_lesson_video,
    mark_lesson_completed,
    get_completed_lessons,
)
from pipeline.video_generator import create_lesson_video
from pipeline.analyse import generate_course_structure
from pipeline.image_generator import create_course_cover

init_db()
apply_custom_css()

st.markdown('<p class="main-title">🎬 Auto-Generate a Course</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Type a topic — everything else is generated for you.</p>', unsafe_allow_html=True)

username = st.session_state.get("username")

topic = st.text_input("What do you want a course on?", placeholder="e.g. Python basics")

if st.button("🚀 Generate Full Course") and topic.strip():
    with st.spinner("Designing course structure..."):
        structure = generate_course_structure(topic.strip())

    if not structure:
        st.error("Could not generate a course structure. Try a different topic.")
    else:
        with st.spinner("🎨 Creating course cover..."):
            try:
                cover_path = create_course_cover(
                    structure["title"],
                    structure["description"],
                )
            except Exception as e:
                st.warning(f"Couldn't generate a cover image, continuing without one: {e}")
                cover_path = None

        course_id = create_course(
            username,
            structure["title"],
            structure["description"],
            cover_path,
        )

        total = len(structure["lessons"])
        progress = st.progress(0, text="Starting...")

        for i, lesson in enumerate(structure["lessons"]):
            progress.progress(i / total, text=f"Generating video for: {lesson['title']}")
            lesson_id = str(uuid.uuid4())[:8]
            try:
                video_path = create_lesson_video(lesson["title"], lesson["content"], lesson_id)
                add_lesson(course_id, lesson["title"], lesson["content"], video_path)
            except Exception as e:
                st.error(f"Failed to generate video for '{lesson['title']}': {e}")
                continue

        progress.progress(1.0, text="Done!")
        st.success(f"Course '{structure['title']}' generated!")
        st.rerun()

st.divider()
courses = get_courses_for_user(username)

if courses:

    st.subheader("Your Courses")

    course_titles = {c["title"]: c["course_id"] for c in courses}

    selected_title = st.selectbox(
        "View a course",
        list(course_titles.keys())
    )

    selected_id = course_titles[selected_title]

    selected_course = next(
        c for c in courses
        if c["course_id"] == selected_id
    )

    if (
        selected_course["cover_image"]
        and os.path.exists(selected_course["cover_image"])
    ):
        st.image(
            selected_course["cover_image"],
            use_container_width=True
        )

    st.markdown(f"# 📚 {selected_course['title']}")
    st.write(selected_course["description"])

    lessons = get_lessons_for_course(selected_id)
    completed = get_completed_lessons(selected_id)
    total_lessons = len(lessons)
    course_progress = 0 if total_lessons == 0 else completed / total_lessons

    st.progress(course_progress)
    col1, col2, col3 = st.columns(3)
    col1.metric("Lessons", total_lessons)
    col2.metric("Completed", completed)
    col3.metric("Progress", f"{int(course_progress * 100)}%")

    for lesson in lessons:
        with st.expander(
            f"📖 Lesson {lesson['lesson_number']} : {lesson['title']}",
            expanded=False,
        ):
            st.markdown("### 🎥 Lesson Video")

            video_path = lesson["video_path"]

            if video_path and os.path.exists(video_path):
                st.video(video_path)
            else:
                st.warning("Video missing.")

                if st.button(
                    "🔄 Regenerate Video",
                    key=f"regen_{lesson['lesson_id']}",
                ):
                    with st.spinner("Generating..."):
                        try:
                            new_path = create_lesson_video(
                                lesson["title"],
                                lesson["content_text"],
                                f"regen_{lesson['lesson_id']}_{uuid.uuid4().hex[:6]}"
                            )
                            update_lesson_video(
                                lesson["lesson_id"],
                                new_path,
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(e)

            st.markdown("---")
            st.markdown("### 📖 Lesson Notes")
            st.write(lesson["content_text"])
            st.markdown("---")

            if lesson["completed"]:
                st.success("✅ Lesson Completed")
            else:
                if st.button(
                    "✅ Mark Lesson Complete",
                    key=f"complete_{lesson['lesson_id']}",
                ):
                    mark_lesson_completed(lesson["lesson_id"])
                    st.rerun()
else:
    st.info("No courses yet — generate one above to get started.")