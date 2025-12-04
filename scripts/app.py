from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from nucleai.agent.core import create_nucleai_agent

# Load environment variables
load_dotenv()

# Configure page with custom favicon
current_dir = Path(__file__).resolve().parent
favicon_path = str(current_dir / ".." / "assets" / "favicon.png")
st.set_page_config(page_title="Nuclear-AI Chat", page_icon=favicon_path, layout="wide")
st.title("Nuclear-AI Research Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize agent
if "agent" not in st.session_state:
    with st.spinner("Initializing Agent..."):
        st.session_state.agent = create_nucleai_agent()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask a scientific question..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"), st.spinner("Thinking..."):
        try:
            # Invoke the agent
            response = st.session_state.agent.invoke({"messages": [("user", prompt)]})

            # Extract output
            output = ""
            if "messages" in response and response["messages"]:
                output = response["messages"][-1].content

            st.markdown(output)
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": output})
        except Exception as e:
            st.error(f"Error: {e}")
