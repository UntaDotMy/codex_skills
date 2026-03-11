# Open-Source Memory Patterns Applied Here

This note records the live design patterns that informed the current `codex_skills` memory layout so future edits do not drift back to a flat replay-everything model.

## Source Patterns

- Anthropic Claude Code memory hierarchy separates user memory from project memory and lets local project memory live closer to the working repo. Source: https://docs.anthropic.com/en/docs/claude-code/memory
- Mem0 documents scoped memory identities such as `user_id`, `agent_id`, and `run_id`, which keeps shared knowledge separate from per-agent and per-run context. Source: https://docs.mem0.ai/open-source/graph_memory/overview
- `repoMemory` keeps repo-specific memory aware of branches and worktrees so code-change context does not smear across unrelated lines of work. Source: https://github.com/alioshr/repoMemory

## Applied Decisions In This Repo

- Keep **workspace memory** for shared repo-level guidance.
- Add **workstream memory** so a branch, feature lane, or focused task can hold its own summary and memory without polluting the whole workspace.
- Keep **role memory** for reused reviewer, worker, architect, or other role lanes inside the same workspace and workstream.
- Add **agent-instance memory** so one reused sub-agent can keep its own bounded notes instead of sharing every detail with every other same-role agent.
- Keep the **research cache shared at workspace scope** so validated research can be reused across agents without redoing the same web loop.
- Keep **archive lanes** for stale or superseded cache entries so old findings are preserved without staying in the active reuse path.
- Resolve memory in this order: agent instance, role, workstream, workspace, shared cache, episodic rollout evidence, then global durable memory.
- Mirror the user's **L2 memory** and **L3 reference** split with explicit scoped `memory/` and `reference/` lanes so one home per fact stays enforceable instead of becoming a vague convention.

## Boundary Notes

- The repo treats the working-buffer trigger as a runtime-aware heuristic: use roughly 60 percent context usage when a runtime exposes that signal, otherwise switch on the buffer as soon as context pressure is clearly rising.
- Self-awareness, self-healing, and self-learning are implemented here as bounded maintenance loops over scoped memory, validation, reward or penalty tracking, and recalibration. They are not claims of autonomous model retraining.

## Why This Matters

- Different tasks in the same repo no longer need to read the same large memory bundle.
- Reused reviewers or workers can resume with smaller context.
- Old findings stay available, but stale findings stop crowding the active memory lane.
- The system can reward, penalize, archive, and refresh memory with narrower blast radius.
