import asyncio
import streamlit as st
from adk.init_adk import get_google_api_key, initialize_adk, run_at_session

def run_streamlit_app():
    st.title("Personal restaurant recommender")
    st.write("This is an AI App made with ❤️ by Álvaro using Google Agent Development Kit")

    # Check if the user is logged in
    if not st.user.is_logged_in:
        # If not logged in, display a login button
        if st.button("Log in with Google"):
            # Redirect to the OIDC provider for authentication
            st.login("google")
    else:
        # If logged in, display user information and a logout button at the sidebar
        st.sidebar.write(st.user.name)
        # st.write(f"Your email is: {st.user.email}")
        # You can access other user attributes provided by your identity provider

        if st.sidebar.button("Log out"):
            # Log the user out
            st.logout()
            st.rerun() # Rerun the app to show the login state

        get_google_api_key()
        runner = initialize_adk()
        adk_session_id = str(st.user.email)

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
                    loop = asyncio.new_event_loop()
                    responses = loop.run_until_complete(run_at_session(runner, prompt, adk_session_id))
                    print(responses)
                    try:
                        for response in responses:
                            st.markdown(response)
                    except Exception as e:
                        st.error(f"‼️ Error processing LLM response: Details {e}")
                        st.stop()

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": responses})
