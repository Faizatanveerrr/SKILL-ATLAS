import streamlit as st
from shared import apply_custom_css, render_grid_card, render_result_detail
from pipeline.graph import build_roadmap
import html
apply_custom_css()

roadmap = st.session_state.get("roadmap")

# --- Detail view branch (handles the "About" button click) ---
selected_url = st.session_state.get("selected_resource_url")
if selected_url and roadmap:
    selected_resource = None
    for stage in roadmap["stages"]:
        if stage["resource"] and stage["resource"].url == selected_url:
            selected_resource = stage["resource"]
            break

    if selected_resource:
        render_result_detail(selected_resource, topic=roadmap.get("goal"))
        st.stop()  # prevent falling through to the list view below
    else:
        # stale/invalid selection, clear it and continue to the list view
        st.session_state["selected_resource_url"] = None

# --- Roadmap input + list view ---
st.markdown('<p class="main-title">🗺️ Learning Roadmap</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Get a step-by-step path toward a bigger learning goal.</p>', unsafe_allow_html=True)

goal = st.text_input("What do you want to achieve?", placeholder="e.g. become a backend developer")

if st.button("🗺️ Generate Roadmap") and goal.strip():
    with st.spinner("Designing your roadmap — this involves multiple searches, please wait..."):
        roadmap = build_roadmap(goal.strip())
        st.session_state["roadmap"] = roadmap

if roadmap and roadmap["stages"]:
    st.success(f"Roadmap for: {roadmap['goal']}")
    for stage in roadmap["stages"]:
        st.subheader(f"Stage {stage['stage_number']}: {stage['title']}")
        st.write(stage["description"])
        if stage["resource"]:
            render_grid_card(stage["resource"], context=f"roadmap_{stage['stage_number']}")
        else:
            st.warning("No resource found for this stage.")
        st.divider()