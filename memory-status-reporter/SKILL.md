---
name: memory-status-reporter
description: Produces human-style memory status reports from Codex memory files. Use for requests like "what did you learn today", "show memory status", "what mistakes happened and are they resolved", "how is memory growing", or "summarize what you understand about my needs."
metadata:
  short-description: Human-style memory health and learning reports
---

# Memory Status Reporter

## Purpose

Turn Codex memory artifacts into a human-readable status report that feels like a check-in, not a raw dump.

## Use This Skill When

- The user asks what Codex learned today or recently.
- The user wants mistakes encountered, whether they were resolved, and what remains open.
- The user wants heuristic memory-health stats such as learning capture, resolution rate, or brain growth.
- The user wants tool-use mistakes and tool failure patterns remembered as mistakes too when those corrections are reusable.
- The user wants a report that reflects remembered user preferences and current needs.

## Report Contract

Always produce these sections unless the user narrows the scope:

1. **Status** — `Healthy`, `Mixed`, `Needs Attention`, or `Quiet`
2. **What I Learned** — durable learnings grounded in memory artifacts from the requested window
3. **Mistakes Encountered** — mark each item as `Resolved`, `Open`, or `Unclear`, including tool-use mistakes when artifacts captured them
4. **Needs I Remember** — summarize recurring user preferences from `memory_summary.md`
5. **Learning Stats (Heuristic)** — task completion, learning capture, mistake resolution, brain size, brain growth, momentum, and confidence
6. **Reality Check** — explicitly label heuristic percentages as estimates derived from memory files, not literal cognition measurements

## Workflow

1. Determine the reporting window. Default to today in the local timezone unless the user asks for a different period.
2. Run the bundled script through `js_repl` with `codex.tool("exec_command", ...)`:
   ```javascript
   await codex.tool("exec_command", {
     cmd: "python3 ~/.codex/skills/memory-status-reporter/scripts/memory_status_report.py --memory-base ~/.codex/memories"
   })
   ```
3. For a final-answer footer or quick check-in, use the compact mode:
   ```javascript
   await codex.tool("exec_command", {
     cmd: "python3 ~/.codex/skills/memory-status-reporter/scripts/memory_status_report.py --memory-base ~/.codex/memories --format compact"
   })
   ```
4. Read the script output before responding. Do not paraphrase away uncertainty.
5. If tool-use mistakes were part of the work, ensure the rollout summary captures the tool name, failure symptom, cause, verified fix, and prevention note so future reports can surface it.
6. If the user wants a saved artifact, rerun with `--output ~/.codex/memories/reports/<date>-memory-status.md`.
7. If the user wants a broader window, use `--days 7` for a trailing seven-day view ending on the anchor date, or pair it with a specific `--date`.
8. Only use spawned sub-agents when the report itself requires independent verification or parallel evidence gathering. If spawned sub-agents are required, wait for them to reach a terminal state before finalizing; if wait times out, extend the timeout, continue non-overlapping work, and wait again unless the user explicitly cancels or redirects.
9. Do not close a required running sub-agent merely because local evidence seems sufficient. Within the same project or workstream, keep at most one live same-role agent, maintain a lightweight spawned-agent list keyed by role or workstream, and check that list before every `spawn_agent` call. Never spawn a second same-role sub-agent if one already exists; always reuse it with `send_input` or `resume_agent`, and resume a closed same-role agent before considering any new spawn. Keep `fork_context` off unless the exact parent thread history is required.
10. When delegating, send a robust handoff covering the exact objective, constraints, relevant file paths, current findings, validation state, non-goals, and expected output.

## Source Priority

1. `~/.codex/memories/rollout_summaries/*.md` for dated task outcomes, reusable knowledge, mistakes, and captured tool-use failure patterns
2. `~/.codex/memories/MEMORY.md` for durable cross-session learnings
3. `~/.codex/memories/memory_summary.md` for user-needs context
4. `~/.codex/memories/raw_memories.md` only when higher-priority files are too thin

## Guardrails

- Never present brain growth as literal cognition. Say it is a heuristic derived from memory artifacts.
- Prefer no percentage over a fake percentage. If the sample is too small, say so.
- Distinguish clearly between "no learning captured" and "no work happened".
- Quote only short snippets when necessary; otherwise summarize.
- If the report window has no artifacts, say that directly and recommend the next useful window.
- Do not invent tool mistakes; report only tool-use failures that are actually captured in memory artifacts.

## References

- `references/reporting-rubric.md` for metric definitions and status thresholds
