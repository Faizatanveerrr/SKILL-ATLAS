import streamlit as st
from shared import render_grid_card, apply_custom_css
from pipeline.storage import (
    get_playlists_for_user, create_playlist, get_playlist_items,
    get_saved_resources_for_user, add_to_playlist, delete_playlist
)

apply_custom_css()

st.markdown('<p class="main-title">🎵 Playlists</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Organize saved resources into a learning sequence.</p>', unsafe_allow_html=True)

username = st.session_state.get("username")

with st.expander("➕ Create a new playlist"):
    new_name = st.text_input("Playlist name")
    if st.button("Create") and new_name.strip():
        create_playlist(username, new_name.strip())
        st.success(f"Created playlist '{new_name.strip()}'")
        st.rerun()

playlists = get_playlists_for_user(username)

if not playlists:
    st.info("No playlists yet. Create one above.")
else:
    playlist_names = {p["name"]: p["playlist_id"] for p in playlists}
    selected_name = st.selectbox("Select a playlist", list(playlist_names.keys()))
    selected_id = playlist_names[selected_name]

    items = get_playlist_items(selected_id)

    with st.expander("➕ Add a saved resource to this playlist"):
        saved = get_saved_resources_for_user(username)
        available = [r for r in saved if r.url not in [i.url for i in items]]
        if available:
            titles = {r.title: r for r in available}
            pick = st.selectbox("Choose a resource", list(titles.keys()))
            if st.button("Add to Playlist"):
                r = titles[pick]
                add_to_playlist(selected_id, r.url, r.topics_covered[0] if r.topics_covered else "")
                st.rerun()
        else:
            st.caption("All saved resources are already in this playlist, or you have none saved yet.")

    if st.button("🗑️ Delete this playlist"):
        delete_playlist(selected_id)
        st.rerun()

    st.divider()
    st.subheader(f"{selected_name} ({len(items)} resources)")

    if not items:
        st.info("This playlist is empty.")
    else:
        for i, r in enumerate(items, start=1):
            st.write(f"**Step {i}**")
            render_grid_card(r, context=f"playlist_{selected_id}")