from pipeline.video_generator import create_lesson_video

path = create_lesson_video(
    "Introduction",
    "Welcome to this course. In this lesson, we will cover the basics of the topic.",
    "test_lesson_1"
)
print(f"Video created at: {path}")