"""
GameGlitch Debug Agent — agentic loop using Claude with tool use.

Flow:
  1. User submits code → CodeInput validation
  2. Claude is called with the search_bug_patterns tool available
  3. Claude calls the tool (RAG retrieval) one or more times
  4. Claude synthesises retrieved patterns + its own analysis into a Bug Report
  5. Result returned as a plain dict: {report, tool_calls, iterations, model}

Prompt caching is enabled on the static system prompt to reduce latency and cost.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from src.agent.prompts import ANALYSIS_PROMPT_TEMPLATE, SYSTEM_PROMPT
from src.rag.retriever import BugRetriever

logger = logging.getLogger(__name__)

# ── Lazy singletons (avoids import-time failures if key is missing) ────────────

_client = None
_retriever: BugRetriever | None = None


def _get_client():
    global _client
    if _client is None:
        from anthropic import Anthropic  # noqa: PLC0415

        _client = Anthropic()
    return _client


def _get_retriever() -> BugRetriever:
    global _retriever
    if _retriever is None:
        _retriever = BugRetriever()
    return _retriever


# ── Tool definitions sent to Claude ───────────────────────────────────────────

_TOOLS: list[dict] = [
    {
        "name": "search_bug_patterns",
        "description": (
            "Search the GameGlitch knowledge base (game bugs + Python pitfalls) for patterns "
            "similar to what you are observing in the code. Use descriptive queries such as "
            "'backwards hint logic streamlit' or 'mutable default argument list'. "
            "Returns up to top_k ranked patterns with descriptions, fix examples, and source."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language description of the suspected bug.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return (1–5). Defaults to 3.",
                    "default": 3,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "suggest_test_case",
        "description": (
            "Generate a pytest regression test skeleton for the highest-severity bug found. "
            "Call this after identifying the main bug. Returns a ready-to-fill-in test function "
            "that the developer can use to prevent the bug from regressing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string",
                    "description": "Name of the function that contains the bug (e.g. 'check_guess').",
                },
                "bug_description": {
                    "type": "string",
                    "description": "One-sentence summary of the bug (e.g. 'hint messages are reversed').",
                },
                "expected_behavior": {
                    "type": "string",
                    "description": "What the function should do correctly (e.g. 'return Go LOWER when guess > secret').",
                },
            },
            "required": ["function_name", "bug_description", "expected_behavior"],
        },
    },
]


# ── Tool execution ─────────────────────────────────────────────────────────────


def _build_test_skeleton(function_name: str, bug_description: str, expected_behavior: str) -> str:
    """Generate a pytest regression test skeleton — no API call required."""
    safe_name = re.sub(r"[^a-z0-9]+", "_", function_name.lower()).strip("_")
    return (
        f"```python\n"
        f"def test_{safe_name}_regression():\n"
        f'    """\n'
        f"    Regression test — added after fixing: {bug_description}\n"
        f"    Expected: {expected_behavior}\n"
        f'    """\n'
        f"    # TODO: import the function and fill in real test values\n"
        f"    # from src.game.logic_utils import {function_name}  # adjust path\n"
        f"\n"
        f"    # Arrange — set up inputs that trigger the bug\n"
        f"    # ...\n"
        f"\n"
        f"    # Act\n"
        f"    result = {function_name}(...)\n"
        f"\n"
        f"    # Assert — verify the corrected behaviour\n"
        f"    # Example: assert result == expected, f\"Got {{result!r}}\"\n"
        f"    raise NotImplementedError('Replace this line with your assertions')\n"
        f"```"
    )


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "search_bug_patterns":
        query = tool_input.get("query", "")
        top_k = min(int(tool_input.get("top_k", 3)), 5)
        results = _get_retriever().retrieve(query, top_k=top_k)
        if not results:
            return "No matching patterns found in the knowledge base for this query."
        return json.dumps(results, indent=2)

    if tool_name == "suggest_test_case":
        return _build_test_skeleton(
            function_name=tool_input.get("function_name", "unknown_function"),
            bug_description=tool_input.get("bug_description", ""),
            expected_behavior=tool_input.get("expected_behavior", ""),
        )

    return f"Unknown tool: {tool_name}"


# ── Content block serialisation ───────────────────────────────────────────────


def _serialize_content(blocks: list[Any]) -> list[dict]:
    """Convert SDK content block objects to plain dicts for message history."""
    serialized = []
    for b in blocks:
        if b.type == "text":
            serialized.append({"type": "text", "text": b.text})
        elif b.type == "tool_use":
            serialized.append(
                {
                    "type": "tool_use",
                    "id": b.id,
                    "name": b.name,
                    "input": b.input,
                }
            )
    return serialized


# ── Public API ─────────────────────────────────────────────────────────────────


def analyze_code(code: str, context: str = "") -> dict:
    """
    Run the agentic debug workflow on a code snippet.

    Parameters
    ----------
    code:    Python source code to analyse.
    context: Optional natural-language context from the user.

    Returns
    -------
    dict with keys:
      - report (str): The final Bug Report text from Claude.
      - tool_calls (list[dict]): Trace of every tool call made.
      - iterations (int): Number of agentic loop iterations.
      - model (str): Model used.
    """
    logger.info(
        "analyze_code | code_length=%d chars | has_context=%s",
        len(code),
        bool(context),
    )

    client = _get_client()

    messages: list[dict] = [
        {
            "role": "user",
            "content": ANALYSIS_PROMPT_TEMPLATE.format(
                code=code,
                context=context or "None provided.",
            ),
        }
    ]

    # System prompt with prompt caching — static content is cached across calls
    system = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    tool_calls_made: list[dict] = []
    max_iterations = 6

    for iteration in range(1, max_iterations + 1):
        logger.debug("Agent iteration %d/%d", iteration, max_iterations)

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                tools=_TOOLS,
                messages=messages,
            )
        except Exception as exc:
            logger.error("API call failed on iteration %d: %s", iteration, exc)
            raise

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        # No tool calls → Claude is done; extract the final text
        if not tool_use_blocks:
            final_text = "\n\n".join(
                b.text for b in response.content if b.type == "text"
            )
            logger.info(
                "Analysis complete | iterations=%d | tool_calls=%d | report_length=%d chars",
                iteration,
                len(tool_calls_made),
                len(final_text),
            )
            return {
                "report": final_text.strip(),
                "tool_calls": tool_calls_made,
                "iterations": iteration,
                "model": "claude-sonnet-4-6",
            }

        # Execute each tool call and build the result list
        tool_results: list[dict] = []
        for tu in tool_use_blocks:
            logger.debug(
                "Tool call: %s | query=%r", tu.name, tu.input.get("query", "")
            )
            result_text = _execute_tool(tu.name, tu.input)
            logger.debug(
                "Tool result: %d chars returned", len(result_text)
            )
            tool_calls_made.append(
                {
                    "tool": tu.name,
                    "input": tu.input,
                    "result_preview": result_text[:300],
                }
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result_text,
                }
            )

        # Append assistant turn + tool results to conversation history
        messages.append({"role": "assistant", "content": _serialize_content(response.content)})
        messages.append({"role": "user", "content": tool_results})

    # Safety fallback — should not normally be reached
    logger.warning(
        "Max iterations (%d) reached without final answer | tool_calls=%d",
        max_iterations,
        len(tool_calls_made),
    )
    return {
        "report": (
            "Analysis hit the maximum iteration limit. "
            "Please try with a shorter or more focused code snippet."
        ),
        "tool_calls": tool_calls_made,
        "iterations": max_iterations,
        "model": "claude-sonnet-4-6",
    }
