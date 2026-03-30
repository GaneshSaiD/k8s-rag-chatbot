import streamlit as st
import requests
import os
API_URL = os.getenv("API_URL", "https://k8s-rag-chatbot-1.onrender.com/api/v1")

st.set_page_config(
    page_title="K8s Ops AI Assistant",
    page_icon="☸",
    layout="centered"
)

st.title("☸ K8s Ops AI Assistant")
st.caption("Ask anything about Kubernetes — powered by RAG + GPT-4o")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.markdown(f"- [{source}]({source})")

if prompt := st.chat_input("Ask a Kubernetes question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching docs and generating answer..."):
            try:
                response = requests.post(
                    f"{API_URL}/query",
                    json={"question": prompt},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                answer = data["answer"]
                sources = data["sources"]
                st.markdown(answer)
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.markdown(f"- [{source}]({source})")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })