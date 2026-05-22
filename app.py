import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, (str, int, float, bool)):
            os.environ.setdefault(_k, str(_v))
except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
    pass

import json
from agent_runtime import generate_response
from lambda_retrieval import get_permission_envelope
import lambda_retrieval

# Page Configuration
st.set_page_config(
    page_title="Prokoti RAG Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .citation-card {
        background-color: #1e2130;
        border-left: 5px solid #00d4ff;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        font-size: 0.85rem;
    }
    .envelope-box {
        background-color: #0e1117;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar: Identity & Configuration
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield-configuration.png", width=80)
    st.title("Identity Center")
    st.markdown("---")
    
    user_id = st.text_input("User ID", value="acme_logistics_0", help="Enter a valid ID from the database (e.g., acme_research_0)")
    
    if user_id:
        with st.spinner("Enriching Identity..."):
            envelope = get_permission_envelope(user_id)

            st.subheader("🛡️ Permission Envelope")
            st.markdown(f"**Tenant:** `{envelope['tenant_id']}`")
            st.markdown(f"**Org ID:** `{envelope['org_id']}`")
            st.markdown(f"**Roles:** `{', '.join(envelope['roles'])}`")

            if envelope["tenant_id"] == "public" and lambda_retrieval.LAST_ENRICHMENT_ERROR:
                try:
                    _secret_keys = sorted(list(st.secrets.keys()))
                except Exception:
                    _secret_keys = ["<unavailable>"]
                st.error(
                    f"Identity lookup failed → returned deny-by-default envelope.\n\n"
                    f"**Reason:** {lambda_retrieval.LAST_ENRICHMENT_ERROR}\n\n"
                    f"**DB host being used:** `{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}` "
                    f"as user `{os.getenv('DB_USER')}`\n\n"
                    f"**st.secrets keys found:** `{_secret_keys}`"
                )

            with st.expander("View Full Metadata"):
                st.json(envelope)
    
    st.markdown("---")
    agent_type = st.selectbox("Select Agent", ["COREAIAGENT", "ONBOARDINGAGENT"])
    
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# Main Interface
st.title("🛡️ CoSec AI")
st.caption("Secured by POOLED Architecture | Identity-Driven Data Isolation")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "citations" in message and message["citations"]:
            with st.expander("📚 Sources & Metadata"):
                for i, cite in enumerate(message["citations"]):
                    st.markdown(f"<div class='citation-card'><b>Source {i+1}</b>: {cite.get('classification', 'Public').upper()} | {cite.get('org_id', 'N/A')}</div>", unsafe_allow_html=True)

# Chat Input
if prompt := st.chat_input("Ask about employees, projects, or logistics..."):
    # User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent Message
    with st.chat_message("assistant"):
        with st.spinner("Retrieving authorized context..."):
            try:
                response = generate_response(prompt, user_id=user_id, agent_type=agent_type)
                
                st.markdown(response["result"])
                
                citations = response.get("citations", [])
                if citations:
                    with st.expander("📚 Sources & Metadata"):
                        for i, cite in enumerate(citations):
                            st.markdown(f"<div class='citation-card'><b>Source {i+1}</b>: {cite.get('classification', 'Public').upper()} | {cite.get('org_id', 'N/A')}</div>", unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response["result"],
                    "citations": citations
                })
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Prokoti GenAI Security Wall v2.2 (Identity-First Protection) - Multi-Tenant Isolation Verified</p>", unsafe_allow_html=True)
