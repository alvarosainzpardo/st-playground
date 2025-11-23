import os
from time import time
import asyncio

from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search

import streamlit as st
from st_cookies_manager import EncryptedCookieManager

# Constants definitions
APP_NAME="default_app"
USER_ID="default_user"
ADK_SESSION_KEY="default_session_key"

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

# try:
#     GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
#     os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
#     os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
#     st.write("✅ Gemini API key setup complete.")
# except Exception as e:
#     st.write(f"🔑 Authentication Error: Please make sure you have added 'GOOGLE_API_KEY' to your Kaggle secrets. Details: {e}")

def init_cookies():
    cookies_password = st.secrets["COOKIES_PASSWORD"]
    if not cookies_password:
        st.error("‼️ Cookies initialization Error: Please make sure you have added 'COOKIES_PASSWORD' to your Streamlit secrets. 🔑")
        st.stop()
    return EncryptedCookieManager(password=cookies_password)

@st.cache_resource
def init_adk():
    try:
        root_agent = Agent(
            name = "my_first_agent",
            model = "gemini-2.5-flash-lite",
            instruction="""You are a very helpful agent. If you dont know something, or in case of doubt, use google_search tool.
            At the beginning of the conversation, you ask the user her name.
            If and only if the user tells you that her name is Laura, or Laura García, you answer saying that it's a pleasure to talk with her, but instead of Laura you say 'Ponisita',
            and after that you say that you are a helpful agent developed with love by 'Ponisito'.
            If the user tells you other name, you answer greeting the user saying that you can help with her questions.
            And after that, in both cases, you continue answering the user questions.
            """,
            tools=[google_search]
        )
        # st.write("✅ Root Agent defined.")
        # InMemorySessionService stores conversations in RAM (temporary)
        session_service = InMemorySessionService()

        # Step 3: Create the Runner
        runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
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


def get_adk_session(runner: Runner, cookies: EncryptedCookieManager):
    if ADK_SESSION_KEY in st.session_state:
        session_id = st.session_state[ADK_SESSION_KEY]
    elif ADK_SESSION_KEY in cookies:
        session_id = cookies[ADK_SESSION_KEY]
    else:
        # session_id = f"streamlit_adk_session_{int(time())}_{os.urandom(4).hex()}"
        session_id = st.user.email
        st.session_state[ADK_SESSION_KEY] = session_id
        cookies[ADK_SESSION_KEY] = session_id
        asyncio.run(runner.session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id))
    return session_id

# Define helper functions that will be reused throughout the notebook
async def run_at_session(runner_instance: Runner, prompt: str, session_name: str = "default"):
    # Get app name from the Runner
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
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text and part.text != "None":
                        response.append(part.text)
    return response

def main():
    st.title("Meet AI Mode-like clone")
    st.text("An AI Agent made with ❤️ by Álvaro")

    # Check if the user is logged in
    if not st.user.is_logged_in:
        # If not logged in, display a login button
        if st.button("Log in with Google"):
            # Redirect to the OIDC provider for authentication
            st.login("google")
    else:
        # If logged in, display user information and a logout button
        if st.user.email == "laurigh1@gmail.com":
            st.markdown("""
            Hello Ponisita:

            - Eres la más preciosa del mundo
            - ¡Eres mi amore y siempre lo serás!
            """)
        else:
            st.write(f"Hello, {st.user.name}!")
        # st.write(f"Your email is: {st.user.email}")
        # You can access other user attributes provided by your identity provider

        if st.button("Log out"):
            # Log the user out
            st.logout()
            st.rerun() # Rerun the app to show the login state

        get_google_api_key()
        runner = init_adk()
        cookies = init_cookies()
        if not cookies.ready():
            st.stop()
        adk_session_id = get_adk_session(runner, cookies)

        st.subheader("Ask detailed questions for better responses")
        st.divider()
        # st.subheader("Chat with the assistant")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                messages = message["content"]
                if type(messages) == str:
                    messages = [messages]
                for message in messages:
                    st.markdown(message)

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
                    responses = asyncio.run(run_at_session(runner, prompt, adk_session_id))
                    for response in responses:
                        st.markdown(response)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": responses})

main()
