import os
import streamlit as st

import asyncio

st.markdown("""
    # My first Goggle ADK app

    This is my first and simple Google ADK app
    """
            )

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

response = asyncio.run(runner.run_debug("What is Streamlit?"))
st.markdown(response[0].content.parts[0].text)

response = asyncio.run(runner.run_debug("What is the current weather in Madrid?"))
st.markdown(response[0].content.parts[0].text)

for event in asyncio.run(runner.run_debug(["Whats the complete name of the current president of United States?", "Whats the complete name of his wife?"])):
    if event.content and event.content.parts and event.content.parts[0].text and event.content.parts[0].text != "None":
        response = event.content.parts[0].text
        st.markdown(response)
