"""Destination Verifier: returns the capital of a country as strict JSON (CountryCapital)."""

import asyncio
import os
import sys

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from callback_logging import log_model_response, log_query_to_model, setup_logging  # noqa: E402
from settings import MODEL  # noqa: E402


class CountryCapital(BaseModel):
    capital: str = Field(description="The capital city of the requested country.")


# Module-level root_agent so `adk web`, `adk run` and the local console can load it
# (it used to be created inside main(), so only the script entrypoint could use it).
root_agent = Agent(
    model=MODEL,
    name="geo_validator",
    description="Verifies geographic capital cities and answers in strict JSON.",
    instruction="Return the capital city of the requested country in the strict JSON format specified.",
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    output_schema=CountryCapital,       # enforce strict JSON output matching the schema
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)


async def main(query: str = "What is the capital of France?"):
    setup_logging()
    runner = InMemoryRunner(agent=root_agent, app_name='geo_validator_app')
    session = await runner.session_service.create_session(app_name='geo_validator_app', user_id='user1')
    content = types.Content(role='user', parts=[types.Part.from_text(text=query)])
    print('** User says:', query)
    async for event in runner.run_async(user_id='user1', session_id=session.id, new_message=content):
        if event.content and event.content.parts and event.content.parts[0].text:
            print(f'** {event.author}: {event.content.parts[0].text}')


if __name__ == "__main__":
    asyncio.run(main())
