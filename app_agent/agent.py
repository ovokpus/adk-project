"""Trivia agent: the minimal ADK starter from the lab."""

import asyncio
import os
import sys

from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from callback_logging import log_model_response, log_query_to_model, setup_logging  # noqa: E402
from settings import MODEL  # noqa: E402

root_agent = Agent(
    model=MODEL,
    name="trivia_agent",
    description="Answers general trivia questions.",
    instruction="Answer questions.",
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
)


async def main(query: str = "What is the capital of France?"):
    setup_logging()
    runner = InMemoryRunner(agent=root_agent, app_name='my_agent_app')
    session = await runner.session_service.create_session(app_name='my_agent_app', user_id='user1')
    content = types.Content(role='user', parts=[types.Part.from_text(text=query)])
    print('** User says:', query)
    async for event in runner.run_async(user_id='user1', session_id=session.id, new_message=content):
        if event.content and event.content.parts and event.content.parts[0].text:
            print(f'** {event.author}: {event.content.parts[0].text}')


if __name__ == "__main__":
    asyncio.run(main())
