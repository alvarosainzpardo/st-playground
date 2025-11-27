from google.genai import types
from google.adk.models.google_llm import Gemini
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import google_search, AgentTool

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

def get_user_info() -> dict:
    """"Returns the info about the logged user of the application.

    Args:
        None.

    Returns:
        Dictionary with status and the user information. Examples:
        - Success: {"status": "success", "user_email": "john@doe.com", "user_full_name: "John Doe"}
        - Error: {"status": "error", "error_message": "User not logged in"}
    """
    if False:
        return {"status": "error", "error_message": "User not logged in"}
    else:
        # return {"status": "success", "user_email": str(st.user.email), "user_full_name": str(st.user.name)}
        return {"status": "success", "data": "the email is bob@smith.com; the full name is Bob Smith"}

user_info_agent = LlmAgent(
    name = "user_info_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""You are an agent that answers any question or request with the user's personal data.
        Use `get_user_info()` tool to get the personal data of the user
    """,
    tools=[get_user_info]
)
"""
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
"""

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

    GENERAL RULES:
    - Rules for answering the user's questions. Options:
        1. To answer questions the user asks about himself/herself and/or questions about personal data of the user: Use the information returned by user_info_agent tool.
        2. To answer general questions not directly related to the user or the user's personal data, if you dont know the answer, use the search_agent tool to gather current information.
    - Always answer the user in the same language the user is using or the language the user wants you to use'
    """,
    tools=[AgentTool(user_info_agent), AgentTool(search_agent)]
)
"""
    a) Each time the user greets you or asks you for a greeting:
        - Use the user_info_agent tool to get information about the user
        - Answer with a personalized greeting including the user's name and the user's email address, using the information returned by user_info_agent, dont invent any information about the user
"""
