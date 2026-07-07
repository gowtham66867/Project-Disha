"""RM Copilot — Claude-powered tool-use agent.

The copilot answers RM questions like "Why did PR001 score 72?" by calling
structured tools (get_prospect_score, get_contributions, get_nba) and
synthesising a plain-language explanation.  Falls back to a deterministic
templated answer when no ANTHROPIC_API_KEY is configured — so the demo
never breaks.
"""
from __future__ import annotations

import json
from typing import Optional

from ..config import get_settings

settings = get_settings()

_TOOLS = [
    {
        "name": "get_prospect_score",
        "description": "Return the lead score, band, and recommended product for a prospect.",
        "input_schema": {
            "type": "object",
            "properties": {"prospect_id": {"type": "string"}},
            "required": ["prospect_id"],
        },
    },
    {
        "name": "get_score_contributions",
        "description": "Return the SHAP-style breakdown explaining why a prospect received their score.",
        "input_schema": {
            "type": "object",
            "properties": {"prospect_id": {"type": "string"}},
            "required": ["prospect_id"],
        },
    },
    {
        "name": "get_next_best_action",
        "description": "Return the recommended product, channel, and timing for a prospect.",
        "input_schema": {
            "type": "object",
            "properties": {"prospect_id": {"type": "string"}},
            "required": ["prospect_id"],
        },
    },
]

_SYSTEM = (
    "You are Disha, an AI copilot for IDBI Bank Relationship Managers. "
    "You help RMs understand prospect lead scores, prioritise their pipeline, "
    "and plan the best outreach approach. Be concise, factual, and use simple "
    "English (or Hindi if the RM asks). Always cite the specific score components "
    "when explaining why a prospect scored high or low."
)


def _fallback_answer(question: str, prospect_data: Optional[dict]) -> str:
    if prospect_data:
        p = prospect_data
        return (
            f"Prospect {p.get('prospect_id','?')} ({p.get('name','')}) has a lead score of "
            f"{p.get('lead_score', 0):.1f}/100 ({p.get('lead_band','')}).\n"
            f"Recommended action: {p.get('recommended_channel','')} — "
            f"pitch {p.get('recommended_product','')} {p.get('recommended_timing','soon')}."
        )
    return "I don't have enough information to answer that question right now."


def ask_copilot(
    question: str,
    prospect_lookup: dict[str, dict],
    contribution_lookup: dict[str, list],
) -> str:
    """Run the copilot agent. Returns a plain-text answer."""
    if not settings.anthropic_api_key:
        # Best-effort fallback — pick first prospect mentioned
        for pid, p in prospect_lookup.items():
            if pid.lower() in question.lower() or p.get("name", "").lower() in question.lower():
                return _fallback_answer(question, p)
        return _fallback_answer(question, next(iter(prospect_lookup.values()), None))

    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def handle_tool(name: str, inp: dict) -> str:
        pid = inp.get("prospect_id", "")
        if name == "get_prospect_score":
            p = prospect_lookup.get(pid)
            if not p:
                return json.dumps({"error": f"Prospect {pid} not found"})
            return json.dumps({
                "prospect_id": pid,
                "name": p.get("name"),
                "lead_score": p.get("lead_score"),
                "lead_band": p.get("lead_band"),
                "recommended_product": p.get("recommended_product"),
            })
        if name == "get_score_contributions":
            contribs = contribution_lookup.get(pid, [])
            return json.dumps({"prospect_id": pid, "contributions": contribs})
        if name == "get_next_best_action":
            p = prospect_lookup.get(pid)
            if not p:
                return json.dumps({"error": f"Prospect {pid} not found"})
            return json.dumps({
                "prospect_id": pid,
                "recommended_product": p.get("recommended_product"),
                "recommended_channel": p.get("recommended_channel"),
                "recommended_timing": p.get("recommended_timing"),
            })
        return json.dumps({"error": "unknown tool"})

    messages = [{"role": "user", "content": question}]
    while True:
        resp = client.messages.create(
            model=settings.copilot_model,
            max_tokens=512,
            system=_SYSTEM,
            tools=_TOOLS,
            messages=messages,
        )
        if resp.stop_reason == "end_turn":
            for block in resp.content:
                if hasattr(block, "text"):
                    return block.text
            return "I couldn't formulate an answer."

        # Process tool calls
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                result = handle_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": tool_results})
