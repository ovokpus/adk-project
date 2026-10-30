import logging

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse

from settings import ENABLE_CLOUD_LOGGING

logger = logging.getLogger("adk_callbacks")
_cloud_ready = False


def setup_logging() -> None:
    """Route logs to Google Cloud Logging when ENABLE_CLOUD_LOGGING=true, else stdlib only.

    The original code created a Cloud Logging client on every import and every callback,
    which fails without GCP credentials and leaks clients.
    """
    global _cloud_ready
    logging.basicConfig(level=logging.INFO)
    if ENABLE_CLOUD_LOGGING and not _cloud_ready:
        import google.cloud.logging

        google.cloud.logging.Client().setup_logging()
        _cloud_ready = True


def log_query_to_model(callback_context: CallbackContext, llm_request: LlmRequest):
    setup_logging()
    if llm_request.contents and llm_request.contents[-1].role == 'user':
        if llm_request.contents[-1].parts[-1].text:
            last_user_message = llm_request.contents[-1].parts[0].text
            logger.info(f"[query to {callback_context.agent_name}]: " + last_user_message)


def log_model_response(callback_context: CallbackContext, llm_response: LlmResponse):
    setup_logging()
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if part.text:
                logger.info(f"[response from {callback_context.agent_name}]: " + part.text)
            elif part.function_call:
                logger.info(f"[function call from {callback_context.agent_name}]: " + part.function_call.name)
