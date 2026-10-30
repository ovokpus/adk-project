"""Local console API for the Cymbal Travel ADK agents.

Offline (no credentials) you can still list and inspect every agent, see the pipeline
graph, validate JSON against the geo_validator schema and exercise the auditor
callbacks. Running an agent calls Gemini and needs credentials (see settings.py);
without them /run returns 503 with the reason. Model output is never simulated.
"""

import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.models import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, ValidationError

import settings
from app_agent.agent import root_agent as trivia_agent
from geo_validator.agent import root_agent as geo_validator
from llm_auditor.agent import root_agent as llm_auditor
from llm_auditor.sub_agents.reviser.agent import _remove_end_of_edit_mark
from my_google_search_agent.agent import root_agent as travel_scout

AGENTS: dict[str, dict[str, Any]] = {
    "my_google_search_agent": {"agent": travel_scout, "title": "Travel Scout",
                               "example": "What are some major events in Tokyo in 2025?"},
    "geo_validator": {"agent": geo_validator, "title": "Destination Verifier",
                      "example": "What is the capital of France?"},
    "llm_auditor": {"agent": llm_auditor, "title": "Brochure Auditor",
                    "example": "Double check this: You can take a direct train from Hawaii to Japan."},
    "app_agent": {"agent": trivia_agent, "title": "Trivia starter",
                  "example": "What is the capital of France?"},
}

app = FastAPI(title="Cymbal Travel ADK console", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def describe(agent: BaseAgent) -> dict:
    d: dict[str, Any] = {"name": agent.name, "type": type(agent).__name__,
                         "description": agent.description or ""}
    if isinstance(agent, LlmAgent):
        instr = agent.instruction if isinstance(agent.instruction, str) else "(dynamic)"
        d.update(
            model=agent.model if isinstance(agent.model, str) else type(agent.model).__name__,
            instruction=instr,
            tools=[getattr(t, "name", getattr(t, "__name__", str(t))) for t in agent.tools],
            output_schema=agent.output_schema.model_json_schema() if agent.output_schema else None,
            disallow_transfer_to_parent=agent.disallow_transfer_to_parent,
            disallow_transfer_to_peers=agent.disallow_transfer_to_peers,
            callbacks={
                "before_model": getattr(agent.before_model_callback, "__name__", None),
                "after_model": getattr(agent.after_model_callback, "__name__", None),
            },
        )
    d["sub_agents"] = [describe(s) for s in agent.sub_agents]
    return d


@app.get("/health")
def health():
    return {"status": "ok", "llm": settings.llm_status(), "model": settings.MODEL, "agents": list(AGENTS)}


@app.get("/api/agents")
def list_agents():
    return [{"id": k, "title": v["title"], "example": v["example"], **describe(v["agent"])} for k, v in AGENTS.items()]


class RunRequest(BaseModel):
    message: str


def _event_dict(ev) -> dict:
    parts = []
    for p in (ev.content.parts if ev.content and ev.content.parts else []):
        if p.text:
            parts.append({"kind": "text", "text": p.text})
        elif p.function_call:
            parts.append({"kind": "function_call", "name": p.function_call.name, "args": p.function_call.args})
        elif p.function_response:
            parts.append({"kind": "function_response", "name": p.function_response.name})
    return {"author": ev.author, "final": ev.is_final_response(), "parts": parts}


@app.post("/api/agents/{agent_id}/run")
async def run_agent(agent_id: str, req: RunRequest):
    if agent_id not in AGENTS:
        raise HTTPException(404, "unknown agent")
    status = settings.llm_status()
    if not status["configured"]:
        raise HTTPException(503, {"configured": False, "reason": status["reason"],
                                  "note": "Not run. No model output was generated or simulated."})
    agent = AGENTS[agent_id]["agent"]
    runner = InMemoryRunner(agent=agent, app_name=f"console_{agent_id}")
    session = await runner.session_service.create_session(app_name=f"console_{agent_id}", user_id="console")
    started = time.perf_counter()
    events = []
    try:
        async for ev in runner.run_async(
            user_id="console", session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=req.message)]),
        ):
            events.append(_event_dict(ev))
    except Exception as e:  # surface the real upstream error, e.g. invalid key / quota / model name
        raise HTTPException(502, {"configured": True, "error": type(e).__name__, "reason": str(e)[:800],
                                  "events_before_error": events}) from e
    return {"run_id": str(uuid.uuid4()), "agent": agent_id, "backend": status["backend"],
            "model": settings.MODEL, "elapsed_ms": round((time.perf_counter() - started) * 1000), "events": events}


class ValidateRequest(BaseModel):
    raw: str


@app.post("/api/agents/{agent_id}/validate-output")
def validate_output(agent_id: str, req: ValidateRequest):
    """Check a JSON string against the agent's output_schema (no model call)."""
    agent = AGENTS.get(agent_id, {}).get("agent")
    if not isinstance(agent, LlmAgent) or not agent.output_schema:
        raise HTTPException(404, "agent has no output_schema")
    try:
        return {"valid": True, "parsed": agent.output_schema.model_validate_json(req.raw).model_dump()}
    except ValidationError as e:
        return {"valid": False, "errors": [{"loc": list(x["loc"]), "msg": x["msg"]} for x in e.errors()]}


class TextRequest(BaseModel):
    text: str


@app.post("/api/callbacks/reviser-end-of-edit")
def reviser_callback(req: TextRequest):
    """Run the reviser's real after_model_callback on a text you supply (no model call)."""
    resp = LlmResponse(content=types.Content(role="model", parts=[types.Part(text=req.text)]))
    out = _remove_end_of_edit_mark(None, resp)
    return {"input": req.text, "output": "".join(p.text or "" for p in out.content.parts)}
