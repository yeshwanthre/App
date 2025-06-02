import streamlit as st
import re
from lanchain_helper import get_similar_answer_from_documents, fetch_txt_files_from_sharepoint, index_documents
import pyttsx3
import threading
import os

# 🎨 UI Setup
col1, col2 = st.columns([0.1, 1])
with col1:
    st.image("kenai.png", width=50)
with col2:
    st.markdown("<h1 style='display: flex; align-items: center;'>Oracle Convopilot</h1>", unsafe_allow_html=True)

# Initialize chat history and indexing flag
if "messages" not in st.session_state:
    st.session_state.messages = []

if "indexed" not in st.session_state:
    st.session_state.indexed = False

# Initialize TTS engine singleton & lock
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1)
tts_lock = threading.Lock()

def speak_text(text):
    def run_speech():
        with tts_lock:
            try:
                engine.say(text)
                engine.runAndWait()
            except RuntimeError as e:
                print(f"⚠️ TTS RuntimeError ignored: {e}")
    threading.Thread(target=run_speech, daemon=True).start()

# Auto index on app start if needed (only once)
if not st.session_state.indexed:
    if not os.path.exists("./vector_index"):
        with st.spinner("📥 Indexing documents from SharePoint for first use..."):
            try:
                index_documents()
                st.session_state.indexed = True
                st.success("✅ Document index ready!")
            except Exception as e:
                st.error(f"❌ Failed to index documents: {e}")
    else:
        st.session_state.indexed = True

# Test SharePoint connection button
if st.button("🧪 Test SharePoint Connection"):
    st.info("Testing connection to SharePoint and fetching .txt files...")
    try:
        documents = fetch_txt_files_from_sharepoint()
        if documents:
            st.success(f"✅ Successfully fetched {len(documents)} .txt file(s) from SharePoint!")
            for doc in documents:
                st.markdown(f"📘 **{doc.metadata['source']}** Preview:")
                preview = doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else "")
                st.code(preview)
        else:
            st.warning("⚠️ No .txt files found in the specified SharePoint folder.")
    except Exception as e:
        st.error(f"❌ Error fetching files from SharePoint: {e}")

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input field
input_container = st.container()
with input_container:
    question = st.chat_input("Ask me anything...")

# Process the question
if question:
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.messages[-1]["content"] == question:
        pass
    else:
        st.session_state.messages.append({"role": "user", "content": question})

    if not re.match(r'^[a-zA-Z0-9\s?.,!@#$%^&*()_+=-]*$', question) or len(question.strip()) < 3:
        response = "I couldn't understand that. Please ask a clear question."
        full_doc = None
    else:
        with st.spinner("🔍 Fetching answer..."):
            response, full_doc = get_similar_answer_from_documents(question)

    st.session_state.messages.append({"role": "assistant", "content": response})

    with chat_container:
        with st.chat_message("assistant"):
            st.markdown(response)

    if full_doc:
        with st.expander("📄 View Full Document"):
            st.text_area("Document Content", full_doc, height=400)

    speak_text(response)
