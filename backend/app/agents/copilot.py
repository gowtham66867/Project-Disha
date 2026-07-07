"""Disha RM Copilot — Claude tool-use agent with CineAgent-grade enhancements.

Advanced patterns applied:
1. Multi-provider LLM governance: Claude → Gemini → rule-based fallback
2. Draft → Verify → Refine (System-2 DVR loop): draft an answer, check
   factual consistency against live score data, refine if wrong
3. Episodic memory: injects last N exchanges per prospect as context so
   Disha remembers what was discussed ("as I mentioned earlier…")
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from .llm_provider import LLMGovernor, LLMResponse

log = logging.getLogger(__name__)

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
        "description": "Return the signed contribution breakdown explaining why a prospect scored X.",
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
    "and plan the best outreach approach. Be concise, factual, and cite specific "
    "score components when explaining why a prospect scored high or low. "
    "Always use the tools to look up live data before answering — never guess."
)

_VERIFY_PROMPT = (
    "Review the draft answer below against the prospect data provided. "
    "If any fact is wrong or missing (score, band, product recommendation, key driver), "
    "correct it. If the draft is accurate, return it unchanged.\n\n"
    "Prospect data: {data}\n\nDraft answer: {draft}\n\nFinal answer:"
)


def _tool_result(name: str, inp: dict, prospect_lookup: dict, contribution_lookup: dict) -> str:
    pid = inp.get("prospect_id", "")
    if name == "get_prospect_score":
        p = prospect_lookup.get(pid)
        if not p:
            return json.dumps({"error": f"Prospect {pid} not found"})
        return json.dumps({k: p[k] for k in ("prospect_id", "name", "lead_score", "lead_band", "recommended_product") if k in p})
    if name == "get_score_contributions":
        return json.dumps({"prospect_id": pid, "contributions": contribution_lookup.get(pid, [])})
    if name == "get_next_best_action":
        p = prospect_lookup.get(pid)
        if not p:
            return json.dumps({"error": f"Prospect {pid} not found"})
        return json.dumps({k: p[k] for k in ("prospect_id", "recommended_product", "recommended_channel", "recommended_timing") if k in p})
    return json.dumps({"error": "unknown tool"})


def _draft_with_claude(
    governor: LLMGovernor,
    question: str,
    history: list[dict],
    prospect_lookup: dict,
    contribution_lookup: dict,
) -> tuple[str, str]:
    """Run tool-use loop; return (draft_text, accumulated_prospect_data)."""
    messages = history + [{"role": "user", "content": question}]
    collected_data: dict = {}

    for _ in range(4):  # max 4 tool-use rounds
        import anthropic
        client = anthropic.Anthropic(api_key=governor.anthropic_api_key)
        resp = client.messages.create(
            model=governor.claude_model,
            max_tokens=512,
            system=_SYSTEM,
            tools=_TOOLS,
            messages=messages,
        )
        if resp.stop_reason == "end_turn":
            text = " ".join(b.text for b in resp.content if hasattr(b, "text"))
            return text or "No answer.", json.dumps(collected_data)

        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                result_str = _tool_result(block.name, block.input, prospect_lookup, contribution_lookup)
                collected_data.update(json.loads(result_str))
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result_str})

        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": tool_results})

    return "I wasn't able to complete the lookup.", "{}"


def _verify_and_refine(governor: LLMGovernor, draft: str, data_json: str) -> str:
    """System-2 DVR: verify the draft against raw data, refine if needed."""
    prompt = _VERIFY_PROMPT.format(data=data_json, draft=draft)
    resp = governor.complete(
        system="You are a fact-checker for a banking AI. Be concise.",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
    )
    return resp.text.strip() or draft


def _fallback_answer(question: str, prospect_lookup: dict) -> str:
    for pid, p in prospect_lookup.items():
        if pid.lower() in question.lower() or p.get("name", "").lower() in question.lower():
            return (
                f"Prospect {p.get('prospect_id')} ({p.get('name')}) scored "
                f"{p.get('lead_score', 0):.1f}/100 ({p.get('lead_band', '')}).\n"
                f"Recommended: {p.get('recommended_channel', '')} — "
                f"pitch {p.get('recommended_product', '')} {p.get('recommended_timing', 'soon')}."
            )
    first = next(iter(prospect_lookup.values()), None)
    if first:
        p = first
        return (
            f"Prospect {p.get('prospect_id')} ({p.get('name')}) scored "
            f"{p.get('lead_score', 0):.1f}/100 ({p.get('lead_band', '')}).\n"
            f"Recommended: {p.get('recommended_channel', '')} — "
            f"pitch {p.get('recommended_product', '')} {p.get('recommended_timing', 'soon')}."
        )
    return "I don't have enough information to answer that."


def ask_copilot(
    question: str,
    prospect_lookup: dict[str, dict],
    contribution_lookup: dict[str, list],
    history: Optional[list[dict]] = None,
    anthropic_api_key: str = "",
    gemini_api_key: str = "",
    claude_model: str = "claude-haiku-4-5-20251001",
) -> tuple[str, str]:
    """Run the DVR copilot. Returns (answer_text, provider_used)."""
    governor = LLMGovernor(
        anthropic_api_key=anthropic_api_key,
        gemini_api_key=gemini_api_key,
        claude_model=claude_model,
    )
    mem_context: list[dict] = history or []

    if not anthropic_api_key and not gemini_api_key:
        return _fallback_answer(question, prospect_lookup), "rule_based"

    if anthropic_api_key:
        try:
            draft, data_json = _draft_with_claude(
                governor, question, mem_context, prospect_lookup, contribution_lookup
            )
            # DVR: verify the draft
            refined = _verify_and_refine(governor, draft, data_json)
            return refined, f"claude/{claude_model}"
        except Exception as e:
            log.warning("Claude DVR failed: %s — trying Gemini", e)

    if gemini_api_key:
        try:
            # Build a simple prompt with context for Gemini
            context_lines = []
            for pid, p in list(prospect_lookup.items())[:5]:
                context_lines.append(
                    f"{p.get('name')} ({pid}): score={p.get('lead_score')}, "
                    f"band={p.get('lead_band')}, product={p.get('recommended_product')}"
                )
            context = "\n".join(context_lines)
            full_question = f"Prospect data:\n{context}\n\nRM question: {question}"
            resp = governor.complete(
                system=_SYSTEM,
                messages=[{"role": "user", "content": full_question}],
                max_tokens=400,
            )
            return resp.text, f"gemini/{governor.gemini_model}"
        except Exception as e:
            log.warning("Gemini failed: %s — rule-based fallback", e)

    return _fallback_answer(question, prospect_lookup), "rule_based"
