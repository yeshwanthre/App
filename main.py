import streamlit as st
import re
from lanchain_helper import get_similar_answer_from_documents, fetch_txt_files_from_sharepoint, index_documents
import os

# 🎨 UI Setup
col1, col2 = st.columns([0.15, 0.85])
with col1:
    st.image("kenai.png", width=100)
with col2:
    st.markdown("<h1 style='display: flex; align-items: center;'>Oracle ConvoPilot</h1>", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "indexed" not in st.session_state:
    st.session_state.indexed = False

# Auto-index docs on first load
if not st.session_state.indexed:
    if not os.path.exists("./vector_index"):
        with st.spinner("🗓 Indexing documents from SharePoint for first use..."):
            try:
                index_documents()
                st.session_state.indexed = True
                st.success("✅ Document index ready!")
            except Exception as e:
                st.error(f"❌ Failed to index documents: {e}")
    else:
        st.session_state.indexed = True

# Input section
input_container = st.container() 
with input_container:
    question = st.chat_input("Ask me anything...")

# Process question
if question:
    if not (st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1]["content"] == question):
        st.session_state.messages.append({"role": "user", "content": question})

    if not re.match(r'^[\s\S]{3,}$', question):
        response = "I couldn't understand that. Please ask a clear question."
        full_doc = None
    else:
        with st.spinner("🔍 Fetching answer..."):
            try:
                response, full_doc = get_similar_answer_from_documents(question, score_threshold=1.0)
                if not response or response.strip() == "":
                    response = "I'm not sure how to help with that. Please ask something related to Oracle documents."
                    full_doc = None
            except Exception as e:
                response = "I'm not sure how to help with that. Please ask something related to Oracle documents."
                full_doc = None

    st.session_state.messages.append({"role": "assistant", "content": response, "full_doc": full_doc})

# Display chat history
chat_container = st.container()
with chat_container:
    reversed_messages = list(reversed(st.session_state.messages))
    pairs = []
    temp_pair = []
    for msg in reversed_messages:
        temp_pair.append(msg)
        if msg["role"] == "user":
            pairs.append(temp_pair)
            temp_pair = []

    doc_counter = 0
    for pair in pairs:
        for msg in reversed(pair):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and "full_doc" in msg and msg["full_doc"]:
                    with st.expander("📄 View Full Document"):
                        st.text_area("Document Content", msg["full_doc"], height=400, key=f"doc_text_{doc_counter}")
                        st.download_button(
                            label="📂 Download .txt",
                            data=msg["full_doc"],
                            file_name="matched_document.txt",
                            mime="text/plain",
                            key=f"download_{doc_counter}"
                        )
                        doc_counter += 1
