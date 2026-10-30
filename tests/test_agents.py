"""Offline checks of the agent definitions and callbacks (no model calls)."""
from google.adk.agents import SequentialAgent
from google.adk.models import LlmResponse
from google.genai import types

from geo_validator.agent import CountryCapital
from geo_validator.agent import root_agent as geo
from llm_auditor.agent import root_agent as auditor
from llm_auditor.sub_agents.critic.agent import _render_reference
from llm_auditor.sub_agents.reviser.agent import _remove_end_of_edit_mark
from my_google_search_agent.agent import root_agent as scout


def test_travel_scout_has_google_search():
    assert [t.name for t in scout.tools] == ["google_search"]


def test_geo_validator_enforces_schema_and_no_transfers():
    assert geo.output_schema is CountryCapital
    assert geo.disallow_transfer_to_parent and geo.disallow_transfer_to_peers
    assert CountryCapital.model_validate_json('{"capital": "Paris"}').capital == "Paris"


def test_auditor_is_critic_then_reviser():
    assert isinstance(auditor, SequentialAgent)
    assert [a.name for a in auditor.sub_agents] == ["critic_agent", "reviser_agent"]
    assert [t.name for t in auditor.sub_agents[0].tools] == ["google_search"]


def _resp(*texts):
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=t) for t in texts]))


def test_reviser_strips_end_of_edit_mark():
    out = _remove_end_of_edit_mark(None, _resp("Corrected.\n---END-OF-EDIT---\nscratch", "more"))
    assert [p.text for p in out.content.parts] == ["Corrected.\n"]


def test_reviser_tolerates_non_text_parts():
    resp = LlmResponse(content=types.Content(role="model", parts=[
        types.Part(function_call=types.FunctionCall(name="x", args={})), types.Part(text="ok")]))
    assert _remove_end_of_edit_mark(None, resp).content.parts[1].text == "ok"


def test_critic_appends_grounding_references():
    resp = _resp("Claim is inaccurate.")
    resp.grounding_metadata = types.GroundingMetadata(grounding_chunks=[
        types.GroundingChunk(web=types.GroundingChunkWeb(title="Example source", uri="https://example.com/a"))])
    out = _render_reference(None, resp)
    assert "Reference:" in out.content.parts[0].text
    assert "[Example source](https://example.com/a)" in out.content.parts[0].text
