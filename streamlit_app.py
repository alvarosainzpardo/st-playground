import os
import streamlit as st

import asyncio

st.title("Chat-GPT-like clone")
st.subheader("Made with love by Alvaro")

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    st.write("✅ Gemini API key setup complete.")
except Exception as e:
    st.write(f"🔑 Authentication Error: Please make sure you have added 'GOOGLE_API_KEY' to your Kaggle secrets. Details: {e}")

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search

try:
    root_agent = Agent(
        name = "my_first_agent",
        model = "gemini-2.5-flash-lite",
        instruction="You are a very helpful agent. If you dont know something, or in case of doubt, use google_search tool",
        tools=[google_search]
    )
    st.write("✅ Root Agent defined.")
except Exception as e:
    st.write(f"Agent creation error: Details {e}")

runner = InMemoryRunner(agent=root_agent)
st.write("✅ Runner created.")

st.divider()
st.subheader("Chat with the assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask anything"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # Create an empty placeholder to update with the assistant's response.
        with st.spinner("Assistant thinking..."): # Show a spinner while the agent processes the request.
            for event in asyncio.run(runner.run_debug([prompt])):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text and part.text != "None":
                                response = part.text
                                st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

