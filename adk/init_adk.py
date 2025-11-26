import os
import streamlit as st
from typing import List

import streamlit as st

from google.genai import types
from google.adk.models.google_llm import Gemini
from google.adk.agents import LlmAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, DatabaseSessionService
from google.adk.tools import google_search, AgentTool

from config.settings import ADK_SESSION_KEY, APP_NAME, USER_ID, retry_config

def get_user_info() -> dict:
    """"Returns the info about the logged user of the application.

    Args:
        None.

    Returns:
        Dictionary with status and the user information. Examples:
        - Success: {"status": "success", user_info: {"user_email": "john@doe.com", "user_full_name: "John Doe"}}
        - Error: {"status": "error", "error_message": "User not logged in"}
    """
    if not st.user:
        return {"status": "error", "error_message": "User not logged in"}
    else:
        # return {"status": "success", "user_email": str(st.user.email), "user_full_name": str(st.user.name)}
        return {"status": "success", "user_info": {"user_email": str(st.user.email), "user_full_name": str(st.user.name)}}

@st.cache_data
def get_google_api_key():
    google_api_key = st.secrets["GOOGLE_API_KEY"]
    if not google_api_key:
        st.error("🔑 Authentication Error: Please make sure you have added 'GOOGLE_API_KEY' to your Streamlit secrets. ⚠️")
        st.stop()
    os.environ["GOOGLE_API_KEY"] = google_api_key
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    # st.write("✅ Gemini API key setup complete.")
    return google_api_key

@st.cache_resource
def initialize_adk():
    try:
        # BEGIN AGENT DEFINITION
        # Same agent definition of file adk_debug/agent.py
        user_info_agent = LlmAgent(
            name = "user_info_agent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction="""You are an agent that answers any question or request with the user's raw personal data.
            RULES:
                1. Use `get_user_info()` to get the info about the user
                2. Answer any question or request with the RAW response of `get_user_info()` tool, with no further proccessing. 
            EXAMPLES:
                1.  - Question: What is my name?
                    - Use `get_user_info()`
                    - Answer: {"status": "success", "user_info": {"user_email": "bob@smith.com", "user_full_name": "Bob Smith"}} 
                2.  - Question: What is my full name?
                    - Use `get_user_info()`
                    - Answer: {"status": "success", "user_info": {"user_email": "alice@example.com", "user_full_name": "Alice Grant"}} 
                3.  - Question: What is email?
                    - Use `get_user_info()`
                    - Answer: {"status": "success", "user_info": {"user_email": "bob@smith.com", "user_full_name": "Bob Smith"}} 
                4.  - Question: What is my address?
                    - Use `get_user_info()`
                    - Answer: {"status": "success", "user_info": {"user_email": "john@doe.com", "user_full_name": "John Doe", "address": "205 1st Avenue"}} 
            """,
            tools=[get_user_info]
        )

        search_agent = LlmAgent(
            name = "search_agent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction="""You are an agent that answers questions and you use the google_search tool to search the internet for information to answer the questions.
            """,
            tools=[google_search]
        )

        root_agent = LlmAgent(
            name = "root_agent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction="""You are a very helpful agent that answers the user's questions.
            RULES:
            1) Rules for answer the user's questions. Options:
                a) Each time the user greets you or asks you for a greeting:
                    - Use the user_info_agent tool to get information about the user
                    - Answer with a personalized greeting including the user's name and the user's email address, using the information returned by user_info_agent, dont invent any information about the user
                b) For questions the user asks about himself/herself and/or questions about personal data of the user: Use the information returned by user_info_agent tool.
                c) For general questions not directly related to the user or the user's personal data', if you dont know the answer, use the search_agent tool to gather current information.
            3) Always answer the user's questions
            4) Always answer the user in the same language the user is using or the user wants you to use'
            EXAMPLE:
            - This response from user_info_agent: {"status": "success", "user_info": {"user_email": "john@doe.com", "user_full_name": "John Doe", "address": "205 1st Avenue"}} means that the user full name is 'John Doe', the user email is 'john@doe.com' and the user's address is '205 1st Avenue'.
            """,
            tools=[AgentTool(user_info_agent), AgentTool(search_agent)]
        )
        # Root agent sample definition for Streamlit app testing
        # root_agent = LlmAgent(
        #     name = "search_agent",
        #     model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        #     instruction="""You are a very helpful agent that answers the user's questions.
        #     When you don't know something you you the tool google_adk to search the information.
        #     """,
        #     tools=[google_search]
        # )
        # END AGENT DEFINITION

        # st.write("✅ Root Agent defined.")
        # InMemorySessionService stores conversations in RAM (temporary)
        # session_service = InMemorySessionService()
        db_url = f"sqlite:///session_service_data.db"  # Local SQLite file
        session_service = DatabaseSessionService(db_url=db_url)

        # Create the app with context management
        app_compacting = App(
            name=APP_NAME,
            root_agent=root_agent,
            events_compaction_config=EventsCompactionConfig(
                compaction_interval=3,  # Trigger compaction every 3 invocations
                overlap_size=1,  # Keep 1 previous turn for context
            )
        )

        # Create the Runner
        runner = Runner(app=app_compacting, session_service=session_service)
        return runner
    except Exception as e:
        st.error(f"‼️ Google ADK component creation error: Details {e}")
        st.stop()

# # InMemorySessionService stores conversations in RAM (temporary)
# session_service = InMemorySessionService()
#
# # Step 3: Create the Runner
# runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
# st.write("✅ Runner created.")
# st.write(f"   - Application: {APP_NAME}")
# st.write(f"   - User: {USER_ID}")
# st.write(f"   - Using: {session_service.__class__.__name__}")


async def get_adk_session(runner_instance: Runner) -> str:
    # Get app name and session service from the Runner
    app_name = runner_instance.app_name
    session_service = runner_instance.session_service

    if ADK_SESSION_KEY in st.session_state:
        session_id = str(st.session_state[ADK_SESSION_KEY])
    else:
        # session_id = f"streamlit_adk_session_{int(time())}_{os.urandom(4).hex()}"
        session_id = str(st.user.email)
        st.session_state[ADK_SESSION_KEY] = session_id
        try:
            await session_service.create_session(app_name=app_name, user_id=USER_ID, session_id=session_id)
        except:
            await session_service.get_session(app_name=app_name, user_id=USER_ID, session_id=session_id)
    return session_id

# Define helper functions that will be reused throughout the notebook
async def run_at_session(runner_instance: Runner, prompt: str, session_name: str = "default") -> List[str]:
    # Get app name and session service from the Runner
    app_name = runner_instance.app_name
    session_service = runner_instance.session_service


    # Attempt to create a new session or retrieve an existing one
    # try:
    #     session = await session_service.create_session(app_name=app_name, user_id=USER_ID, session_id=session_name)
    #     print(f"Create session: {session}")
    # except:
    #     session = await session_service.get_session(app_name=app_name, user_id=USER_ID, session_id=session_name)
    #     print(f"Get session: {session}")

    session = await session_service.get_session(app_name=app_name, user_id=USER_ID, session_id=session_name)
    if not session:
        session = await session_service.create_session(app_name=app_name, user_id=USER_ID, session_id=session_name)

    response = []

    # Convert the query string to the ADK Content format
    query = types.Content(role="user", parts=[types.Part(text=prompt)])

    # Stream the agent's response asynchronously
    async for event in runner_instance.run_async(user_id=USER_ID, session_id=session.id, new_message=query):
        try:
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and part.text != "None":
                            response.append(part.text)
        except Exception as e:
            st.error(f"‼️ Error processing LLM response: Details {e}")
            st.stop()
    return response

