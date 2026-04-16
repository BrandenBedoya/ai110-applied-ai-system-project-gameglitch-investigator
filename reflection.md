# Reflection — GameGlitch Investigator v2

**Course:** AI110 — Foundations of AI Engineering  
**Module:** 5 — Agentic Workflows & Reliability  
**Author:** Branden Bedoya  
**Base project:** [Module 1 — Game Glitch Investigator](https://github.com/BrandenBedoya/ai110-module1show-gameglitchinvestigator-starter)

---

## What I Built and Why

In Module 1, I manually debugged a broken Streamlit number-guessing game — fixing backwards hints,
a state-reset bug, and a type mismatch. The process was instructive, but entirely manual.

For the capstone, I asked: *what if the AI could do what I did?*

The result is a system that takes any Python game code snippet, retrieves relevant bug patterns
from a curated knowledge base, and uses Claude to reason about the specific bugs in the submitted
code — producing a structured Bug Report with root causes and fix suggestions.

---

## Design Decisions

### RAG without heavy dependencies
I chose TF-IDF + cosine similarity (scikit-learn) instead of a dense embedding model like
`sentence-transformers`. This keeps the dependency footprint small, eliminates the need for a
model download on first run, and is fast enough for a 15-pattern knowledge base.

The trade-off: TF-IDF misses semantic similarity (e.g. "flip the direction" won't match
"backwards hint" as well as a dense model would). For this domain and corpus size, keyword
overlap is sufficient.

### Agentic tool use rather than a single prompt
Early iterations just sent the code directly to Claude with a `here are the bug patterns` block
in the prompt. That worked but felt like a lookup table, not reasoning.

Switching to tool use meant Claude *decides* when and how to search, and can make multiple
targeted queries. It makes the system more explainable: the tool call trace shows exactly what
the agent was looking for at each step.

### Prompt caching
The system prompt (role description, output format, severity table) is static across all requests.
Marking it with `"cache_control": {"type": "ephemeral"}` means Anthropic caches it for up to 5
minutes, reducing both latency and token cost on back-to-back analyses.

### Pydantic v2 guardrails at the entry point
I validated inputs before they reach Claude rather than inside the agent. This keeps the agent
code clean and makes it easy to test the validation layer in isolation. The guardrails block:

- Empty or oversized inputs
- Prompt injection phrases
- Shell execution patterns (os.system, subprocess, eval)

They do NOT attempt to detect all possible malicious inputs — that would require a dedicated
content classifier. The goal was to add a meaningful first line of defence, not a complete one.

---

## What Worked Well

**The RAG retrieval is accurate for known patterns.** On every test scenario, the agent retrieved
at least one relevant pattern within the top 3 results, and the pattern descriptions contained
enough context to ground Claude's analysis.

**The agentic loop is predictable.** Claude consistently uses the `search_bug_patterns` tool on
the first iteration and produces a final answer on the second. The max-iterations guard (6) was
never triggered in testing.

**The evaluation framework is meaningful.** The keyword + type-match scoring gives a quantitative
view of reliability without needing human labellers. Running `eval.py` produces a reproducible
JSON report that can be tracked over time.

---

## What I'd Improve with More Time

1. **Dense embeddings for RAG.** Swapping TF-IDF for `sentence-transformers` (all-MiniLM-L6-v2)
   would improve retrieval on semantically related but lexically different queries.

2. **Structured output parsing.** Currently the agent's Bug Report is freeform markdown. Adding
   a second pass that parses it into a `DebugReport` Pydantic model would enable richer UI
   rendering (expandable findings, severity badges, etc.).

3. **More scenarios.** Five scenarios cover the most common bugs but miss things like off-by-one
   errors, mutable default arguments, and import failures. A larger eval set would surface edge
   cases in the agent's reasoning.

4. **Persistent vector store.** For a larger knowledge base, ChromaDB or FAISS with a stored
   index would be faster than rebuilding the TF-IDF matrix on every startup.

5. **User feedback loop.** A thumbs-up/thumbs-down on each report could be stored to identify
   systematically weak areas in the knowledge base.

---

## AI Collaboration Notes

Claude Code (claude-sonnet-4-6) was used as the primary development assistant throughout:

- **Architecture design**: I described the goals and Claude proposed the modular `src/` layout,
  which I reviewed and adjusted (e.g. choosing TF-IDF over sentence-transformers).
- **Boilerplate generation**: `__init__.py`, `.gitignore`, conftest setup — all generated and
  accepted without modification.
- **Prompt engineering**: The system prompt went through two revisions. The first was too
  prescriptive ("step 1, step 2, step 3"). The final version uses a format guide instead,
  giving Claude more flexibility to organise the report.
- **Test coverage**: Claude identified the score-floor regression test and the backwards-hint
  regression test as the two highest-value cases. Both were included.

The main area where I overrode Claude's suggestions was dependency selection — it initially
proposed ChromaDB + sentence-transformers, which I replaced with sklearn for portability.

---

## Lessons Learned

1. **Agentic ≠ more iterations.** A well-scoped tool and clear system prompt means the agent
   can solve most cases in a single tool call. Complexity adds cost, not quality.

2. **Evaluation design is part of the system.** I defined the scoring criteria before writing
   the agent, which forced me to be precise about what "a correct analysis" actually means.

3. **Guardrails should be proportionate.** I blocked the most obvious injection vectors without
   trying to build an exhaustive content filter. Perfect safety is impossible at this layer;
   the goal is meaningful friction, not false confidence.

4. **The knowledge base is the soul of a RAG system.** Getting the 15 patterns right — accurate
   symptoms, precise code smells, good tags — mattered more than the retrieval algorithm.
