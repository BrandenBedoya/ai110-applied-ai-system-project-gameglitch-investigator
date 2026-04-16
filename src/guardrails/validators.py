"""
Input/output validation using Pydantic v2.

Provides guardrails for the debug agent:
  - CodeInput: validates submitted code before it reaches Claude
  - BugFinding / DebugReport: structure and validate agent output
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, field_validator

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_CODE_LENGTH = 5_000  # characters
MAX_CONTEXT_LENGTH = 500

# Simple prompt-injection and shell-execution blocklist
_BLOCKED_PATTERNS: list[str] = [
    "ignore all previous instructions",
    "ignore previous instructions",
    "disregard all instructions",
    "import os; os.system",
    "subprocess.call(",
    "subprocess.run(",
    "__import__('os').system",
    "eval(input(",
    "exec(compile(",
]


# ── Input Models ──────────────────────────────────────────────────────────────


class CodeInput(BaseModel):
    """Validated code snippet submitted by the user."""

    code: str
    context: Optional[str] = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Code cannot be empty.")
        if len(v) > MAX_CODE_LENGTH:
            raise ValueError(
                f"Code exceeds maximum length of {MAX_CODE_LENGTH} characters. "
                f"Please submit a smaller snippet."
            )
        lower = v.lower()
        for pattern in _BLOCKED_PATTERNS:
            if pattern.lower() in lower:
                raise ValueError(
                    f"Submission contains a disallowed pattern: '{pattern}'. "
                    "Please submit Python game code only."
                )
        return v

    @field_validator("context")
    @classmethod
    def truncate_context(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > MAX_CONTEXT_LENGTH:
            return v[:MAX_CONTEXT_LENGTH]
        return v


# ── Output Models ─────────────────────────────────────────────────────────────


class BugFinding(BaseModel):
    """A single bug identified in the submitted code."""

    severity: Literal["critical", "high", "medium", "low"]
    category: str
    description: str
    fix: str


class DebugReport(BaseModel):
    """Structured output from the debug agent."""

    bugs_found: int
    findings: list[BugFinding]
    summary: str
    confidence: float  # 0.0 – 1.0

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

    @field_validator("bugs_found")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("bugs_found must be >= 0.")
        return v
