# Context Efficiency Playbook

This document captures the retrieval, token-efficiency, and memory-architecture techniques that best fit this Codex skill pack.

## Goals

- load less context without losing correctness
- reduce token spend on repeated or stale context
- keep code changes surgical and traceable
- preserve a human-style memory model without pretending the system has literal cognition

## Recommended Architecture

### 1. Working Brief Before Retrieval

Always translate the raw request into:

- user story or job-to-be-done
- desired outcome
- constraints and non-goals
- acceptance criteria
- edge cases
- validation plan

Why it helps:

- narrows search terms before any file load
- makes query rewriting easier
- reduces wasted token spend on irrelevant code or docs

### 2. Retrieval Ladder

Use the cheapest useful retrieval layer first:

1. **Exact path or symbol lookup**
2. **Targeted snippet reads**
3. **Full-file reads for edit scope only**
4. **Hybrid retrieval for large corpora**
5. **Compression before generation**

## Techniques That Save Tokens

### Stable Prompt Prefixes and Prompt Caching

Keep stable instructions and reusable setup text at the front of prompts, and append volatile evidence later. This improves cache reuse and reduces repeated billed input on compatible models.

### Research Cache Design

Persist reusable research findings when they answer a non-trivial question correctly enough to change future work.

Cache these items:

- resolved API usage patterns and correct command sequences
- version-specific caveats and migration notes with freshness dates
- known library bugs or workaround patterns with source links
- external benchmark findings that are likely to be reused
- search terms or source combinations that consistently produced the right answer

Do not cache these items durably:

- raw transcripts or full tool logs
- large copied documentation blocks
- stale vendor pricing, model behavior, or release claims without freshness markers
- one-off local environment noise that is not reusable outside the current task

Freshness rules:

- official docs and standards can live longer, but refresh when version-sensitive
- community workarounds should carry a shorter freshness horizon and lower default confidence
- durable architecture principles can stay longer when they are not tied to a fast-moving version
- if a cached finding is disproven, convert it into a penalty pattern and mark it stale instead of silently reusing it

Reward and penalty loop:

- validated cache hits become rewarded patterns that future agents should prefer first
- repeated mistakes, stale assumptions, and disproven cache entries become penalty patterns that future agents should avoid or refresh

### Surgical Patching

Prefer:

- diff-like edits
- narrow replacements
- modular helper extraction
- partial file reads followed by full reads only on touched files

Avoid:

- whole-file rewrites without need
- repeating unchanged code in prompts
- expanding scope because a file is already open

### Memory Layering

Use a human-style engineering analogy:

- **working memory** = active brief, current files, immediate validation target
- **episodic memory** = rollout summaries and recent task outcomes
- **durable memory** = indexed lessons and persistent user preferences

The point is not to mimic biology literally. The point is to stop replaying everything on every task.

### Compression and Summarization

When context is long:

- summarize first-pass findings into compact notes
- collapse old turns into reusable facts
- carry forward decisions, not raw transcript dumps
- use compact memory snapshots in final answers when the user wants learning visibility

### Small-Model and Narrow-Task Routing

Use the smallest acceptable step for classification, routing, candidate filtering, query expansion, or duplicate detection. Reserve the large model context budget for actual implementation, final synthesis, and difficult reasoning across multiple evidence sources.

## How This Repo Implements the Strategy

- `AGENTS.md` requires a working brief before research or coding
- `AGENTS.md` requires a context retrieval ladder before broad context loading
- `sync-skills.sh` injects the shared execution-policy lines into `~/.codex/config.toml`
- `memory-status-reporter/scripts/memory_status_report.py --format compact` provides the final-answer learning footer
- `README.md` documents the setup and operational workflow

## Sources

- Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks — https://arxiv.org/abs/2005.11401
- LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression — https://arxiv.org/abs/2310.06839
- OpenAI Prompt Caching 101 — https://cookbook.openai.com/examples/prompt_caching101
- OpenAI latency optimization guide — https://platform.openai.com/docs/guides/latency-optimization
- OpenAI model page for GPT-5 mini — https://platform.openai.com/docs/models/gpt-5-mini
- GitHub code search syntax — https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax
- GitHub code navigation — https://docs.github.com/en/repositories/working-with-files/using-files/navigating-code-on-github
