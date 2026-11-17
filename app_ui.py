"""
app_ui.py
=========
AI Lab Course Project: Study Guide & Revision Assistant
Author: Student Submission
Stack: Python, Streamlit, Extractive NLP, Google Gemini API
"""

import os
import streamlit as st
from assistant import StudyGuideAssistant
import ai_client

# Page configuration
st.set_page_config(
    page_title="CS Study Guide Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def get_assistant():
    return StudyGuideAssistant()

assistant = get_assistant()

# ----------------- Sidebar -----------------
st.sidebar.title("Project Controls")

# API Key management
saved_key = ai_client.get_api_key() or ""
user_key = st.sidebar.text_input(
    "Google Gemini API Key (Optional):",
    value=saved_key,
    type="password",
    help="Enter an API key to enable online LLM mode for any topic. Leave blank to run offline."
)

if user_key and user_key != saved_key:
    ai_client.set_api_key(user_key)
    st.sidebar.success("API Key updated successfully.")

# System Status indicator
if ai_client.is_ai_available():
    st.sidebar.success("System Status: Online (Gemini LLM Connected)")
else:
    st.sidebar.info("System Status: Offline Mode (Local Database)")

st.sidebar.markdown("---")

# Preloaded database reference
st.sidebar.subheader("Preloaded Topics (Offline)")
st.sidebar.caption("These topics are available with or without an internet connection:")
for topic in assistant.list_available_topics():
    st.sidebar.write(f"• {topic}")

# ----------------- Main Header -----------------
st.title("Study Guide & Revision Assistant")
st.caption("AI Lab Mini Project — Automated curriculum roadmaps, curated resources, and notes summarization.")

# Navigation Tabs (Clean student-style naming without emoji spam)
tab_roadmap, tab_resources, tab_summary, tab_notes, tab_full, tab_qa = st.tabs([
    "Learning Roadmap",
    "Learning Resources",
    "Topic Overview",
    "Notes Summarizer",
    "Complete Study Guide",
    "AI Doubt Solver (Q&A)"
])

# ----------------- Tab 1: Learning Roadmap -----------------
with tab_roadmap:
    st.subheader("Step-by-Step Learning Path")
    st.write("Generates a progressive learning roadmap from foundational concepts up to advanced topics.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        topic_input = st.text_input("Enter subject or topic name:", value="Machine Learning", key="rm_topic")
    with col2:
        level_input = st.selectbox("Current proficiency level:", ["Beginner", "Intermediate", "Advanced"], key="rm_level")

    if st.button("Generate Roadmap", type="primary", key="btn_rm"):
        with st.spinner("Generating roadmap..."):
            res = assistant.get_roadmap(topic_input, level=level_input.lower())
            md = assistant.format_roadmap_markdown(res)
            st.markdown(md)
            if res.get("success"):
                st.download_button(
                    "Download Roadmap (.md)",
                    data=md,
                    file_name=f"{topic_input}_{level_input.lower()}_roadmap.md",
                    mime="text/markdown"
                )

# ----------------- Tab 2: Learning Resources -----------------
with tab_resources:
    st.subheader("Curated Study Resources")
    st.write("Finds verified textbooks, video lectures, practice sites, and official documentation.")
    
    res_topic = st.text_input("Enter subject or topic name:", value="Data Structures & Algorithms", key="res_topic")

    if st.button("Fetch Resources", type="primary", key="btn_res"):
        with st.spinner("Fetching resources..."):
            res = assistant.get_resources(res_topic)
            md = assistant.format_resources_markdown(res)
            st.markdown(md)
            if res.get("success"):
                st.download_button(
                    "Download Resources (.md)",
                    data=md,
                    file_name=f"{res_topic}_resources.md",
                    mime="text/markdown"
                )

# ----------------- Tab 3: Topic Overview -----------------
with tab_summary:
    st.subheader("Conceptual Topic Summary")
    st.write("Provides a formal definition, core principles, real-world use cases, and common beginner mistakes.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        sum_topic = st.text_input("Enter topic to summarize:", value="Operating Systems", key="sum_topic")
    with col2:
        sum_length = st.selectbox("Detail level:", ["Short", "Medium", "Detailed"], index=1, key="sum_length")

    if st.button("Generate Summary", type="primary", key="btn_sum"):
        with st.spinner("Generating summary..."):
            res = assistant.summarize_topic(sum_topic, length=sum_length.lower())
            md = assistant.format_topic_summary_markdown(res)
            st.markdown(md)
            if res.get("success"):
                st.download_button(
                    "Download Summary (.md)",
                    data=md,
                    file_name=f"{sum_topic}_{sum_length.lower()}_summary.md",
                    mime="text/markdown"
                )

# ----------------- Tab 4: Notes Summarizer -----------------
with tab_notes:
    st.subheader("Lecture Notes Summarizer")
    st.write("Summarize long lecture notes using either the offline extractive word-frequency method or generative LLM.")

    col_input, col_engine = st.columns([1, 1])
    with col_input:
        input_type = st.radio("Input format:", ["Paste text directly", "Upload .txt file"], horizontal=True)
    with col_engine:
        engine_type = st.radio("Summarization method:", [
            "Extractive (Offline Word-Frequency Scoring)",
            "Generative (Gemini LLM Rewrite)"
        ], horizontal=True)

    notes_text = ""
    if input_type == "Upload .txt file":
        uploaded = st.file_uploader("Select .txt file containing notes", type=["txt"])
        if uploaded:
            notes_text = uploaded.read().decode("utf-8")
            st.info(f"Loaded {len(notes_text)} characters from {uploaded.name}")
    else:
        notes_text = st.text_area(
            "Paste your notes here:",
            height=180,
            placeholder="Paste raw lecture notes, textbook paragraphs, or revision notes..."
        )

    length_choice = st.selectbox("Summary output length:", ["Short", "Medium", "Detailed"], index=1, key="n_len")

    if st.button("Process Notes", type="primary", key="btn_notes"):
        if not notes_text.strip():
            st.warning("Please provide note text to summarize.")
        else:
            use_ai = "Generative" in engine_type
            with st.spinner("Analyzing and summarizing text..."):
                res = assistant.summarize_user_notes(notes_text, length=length_choice.lower(), use_ai=use_ai)
                if res.get("success"):
                    st.markdown(res["markdown"])
                    st.download_button(
                        "Download Notes Summary (.md)",
                        data=res["markdown"],
                        file_name="notes_summary.md",
                        mime="text/markdown"
                    )
                else:
                    st.error(res.get("error"))

# ----------------- Tab 5: Complete Study Guide -----------------
with tab_full:
    st.subheader("Complete Study Guide Generator")
    st.write("Generates all three sections (Overview, Roadmap, and Resources) into a single document.")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        fg_topic = st.text_input("Subject / Topic:", value="Python", key="fg_topic")
    with c2:
        fg_level = st.selectbox("Level:", ["Beginner", "Intermediate", "Advanced"], key="fg_lvl")
    with c3:
        fg_len = st.selectbox("Summary Depth:", ["Short", "Medium", "Detailed"], index=1, key="fg_len")

    if st.button("Generate Complete Guide", type="primary", key="btn_full"):
        with st.spinner("Compiling complete study guide..."):
            res = assistant.get_full_study_guide(fg_topic, level=fg_level.lower(), length=fg_len.lower())
            st.markdown(res["markdown"])
            if res.get("success"):
                st.download_button(
                    "Download Complete Study Guide (.md)",
                    data=res["markdown"],
                    file_name=f"{fg_topic}_complete_guide.md",
                    mime="text/markdown"
                )

# ----------------- Tab 6: AI Doubt Solver -----------------
with tab_qa:
    st.subheader("AI Doubt Solver & Concept Explainer")
    st.write("Ask questions on difficult computer science concepts to receive clear explanations with examples and analogies.")

    user_question = st.text_input(
        "Enter your question or doubt:",
        placeholder="e.g. What is the difference between Paging and Segmentation in Operating Systems?"
    )

    if st.button("Ask Question", type="primary", key="btn_qa"):
        if not user_question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Fetching explanation..."):
                ans = assistant.ask_ai_tutor(user_question)
                if ans.get("success"):
                    st.markdown(ans["answer"])
                    st.download_button(
                        "Download Explanation (.md)",
                        data=ans["answer"],
                        file_name="concept_explanation.md",
                        mime="text/markdown"
                    )
                else:
                    st.error(ans.get("error"))
