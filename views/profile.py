import streamlit as st
import plotly.graph_objects as go
from pipeline.storage import get_user_stats, get_resource_type_breakdown, get_most_searched_topic, get_search_history_for_user

st.markdown('<p class="main-title">👤 Profile</p>', unsafe_allow_html=True)

username = st.session_state.get("username")
name = st.session_state.get("name")

stats = get_user_stats(username)
most_searched = get_most_searched_topic(username)

st.markdown(f"""
<div class="resource-card">
    <div class="resource-title">{name}</div>
    <div class="meta-text">Username: {username}</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
metric_style = """
<div class="resource-card" style="text-align:center;">
    <div class="meta-text" style="font-size:0.85rem;">{label}</div>
    <div style="font-size:2rem; font-weight:800; color:#ffffff; margin-top:0.3rem;">{value}</div>
</div>
"""
with col1:
    st.markdown(metric_style.format(label="Total Searches", value=stats["search_count"]), unsafe_allow_html=True)
with col2:
    st.markdown(metric_style.format(label="Saved Resources", value=stats["saved_count"]), unsafe_allow_html=True)
with col3:
    st.markdown(metric_style.format(label="Most Searched Topic", value=most_searched or "—"), unsafe_allow_html=True)

st.write("")
st.subheader("Saved Resources by Type")

breakdown = get_resource_type_breakdown(username)
if breakdown:
    fig = go.Figure(go.Bar(
        x=list(breakdown.values()),
        y=list(breakdown.keys()),
        orientation="h",
        marker=dict(color="#60a5fa", line=dict(width=0)),
        text=list(breakdown.values()),
        textposition="outside",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#d1d5db", family="Times New Roman"),
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False),
        margin=dict(l=10, r=10, t=10, b=10),
        height=max(200, 60 * len(breakdown)),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Save some resources to see this breakdown.")

st.write("")
st.subheader("Recent Activity")

history = get_search_history_for_user(username)[:5]
if history:
    for entry in history:
        st.markdown(f"""
        <div class="resource-card" style="padding:0.8rem 1.2rem;">
            🔍 <b>{entry['topic']}</b> — {entry['result_count']} results
            <div class="meta-text">{entry['time']}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No searches yet.")