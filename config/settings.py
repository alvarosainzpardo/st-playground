from google.genai import types

# Constants definitions
APP_NAME="default_app"
USER_ID="default_user"
ADK_SESSION_KEY="default_session_key"

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)
