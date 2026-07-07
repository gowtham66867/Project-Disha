"""Multi-provider LLM governance — Claude primary, Gemini fallback, rule-based last resort.

Mirrors CineAgent's multi-provider pattern: each provider is tried in order;
the first that succeeds returns a response.  All failures are logged so the
caller knows which tier answered.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    provider: str          # "claude" | "gemini" | "rule_based"
    model: str
    fallback_reason: Optional[str] = None


@dataclass
class LLMGovernor:
    """Try providers in order; return the first successful response."""

    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    claude_model: str = "claude-haiku-4-5-20251001"
    gemini_model: str = "gemini-1.5-flash"

    def complete(
        self,
        system: str,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        max_tokens: int = 512,
    ) -> LLMResponse:
        """Try Claude → Gemini → rule-based fallback."""
        if self.anthropic_api_key:
            try:
                return self._claude(system, messages, tools, max_tokens)
            except Exception as e:
                log.warning("Claude failed (%s), falling back to Gemini", e)

        if self.gemini_api_key:
            try:
                return self._gemini(system, messages, max_tokens)
            except Exception as e:
                log.warning("Gemini failed (%s), falling back to rule-based", e)

        return self._rule_based(messages)

    # ------------------------------------------------------------------ #

    def _claude(self, system, messages, tools, max_tokens) -> LLMResponse:
        import anthropic
        client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        kwargs: dict = dict(
            model=self.claude_model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools

        resp = client.messages.create(**kwargs)

        # Handle tool-use response: collect text blocks only for non-tool turns
        text_parts = [b.text for b in resp.content if hasattr(b, "text")]
        text = " ".join(text_parts) if text_parts else ""

        # If stop_reason is tool_use, return the raw content for the caller to handle
        if resp.stop_reason == "tool_use":
            return LLMResponse(text=text, provider="claude", model=self.claude_model)

        return LLMResponse(text=text or "No response.", provider="claude", model=self.claude_model)

    def _gemini(self, system, messages, max_tokens) -> LLMResponse:
        import google.generativeai as genai
        genai.configure(api_key=self.gemini_api_key)
        model = genai.GenerativeModel(
            self.gemini_model,
            system_instruction=system,
        )
        # Flatten messages to a single prompt for Gemini
        prompt = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            if isinstance(m["content"], str)
            else f"User: {m['content']}"
            for m in messages
        )
        resp = model.generate_content(prompt, generation_config={"max_output_tokens": max_tokens})
        return LLMResponse(
            text=resp.text,
            provider="gemini",
            model=self.gemini_model,
            fallback_reason="Claude unavailable",
        )

    def _rule_based(self, messages) -> LLMResponse:
        last = messages[-1] if messages else {}
        content = last.get("content", "") if isinstance(last.get("content"), str) else ""
        text = (
            "Based on the prospect data, I recommend reviewing the lead score breakdown "
            "and following the Next Best Action on their profile page. "
            "No AI provider is currently configured — set ANTHROPIC_API_KEY for full copilot."
        )
        return LLMResponse(
            text=text,
            provider="rule_based",
            model="none",
            fallback_reason="No LLM provider configured",
        )
