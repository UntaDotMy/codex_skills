# Memory Reporting Rubric

## Purpose

This rubric defines the memory-health metrics used by `scripts/memory_status_report.py` so the report stays honest and repeatable.

## Source Priority

1. `rollout_summaries/*.md`
2. `MEMORY.md`
3. `memory_summary.md`
4. rewarded-pattern, penalty-pattern, or research-cache sections captured inside those artifacts
5. `raw_memories.md` only when the higher-priority sources are too thin

## Status Labels

- **Healthy**: rollouts exist, no failed tasks, no open mistakes, and no meaningful stale-cache risk
- **Mixed**: work exists but there are partial tasks, open mistakes, unclear mistakes, or stale cache findings that need refresh
- **Needs Attention**: failed tasks exist, open mistakes outweigh resolved mistakes, or penalty pressure is clearly rising
- **Quiet**: no rollout summaries fall inside the requested window

## Metric Definitions

- **Task completion**: successful task outcomes divided by total task outcomes in the window
- **Learning capture**: rollout summaries with reusable-knowledge bullets divided by rollout summaries in the window
- **Mistake resolution**: resolved mistakes divided by total mistakes in the window
- **Reward strength**: rewarded patterns captured in the window plus reusable knowledge that became durable enough to prefer next time
- **Penalty pressure**: repeated open or unclear mistakes, repeated tool mistakes, and stale findings that future work should avoid or refresh
- **Cache reuse rate**: research-cache updates marked as reused divided by total research-cache updates in the window when that sample exists
- **Cache freshness risk**: stale or refresh-needed findings captured in the reporting window
- **Brain size**: durable knowledge-bank units counted from `MEMORY.md` learnings plus reusable user-guidance bullets from `memory_summary.md`
- **Brain growth**: window growth units divided by brain size, where growth units equal reusable-knowledge bullets plus resolved mistakes
- **Learning momentum**: window growth units compared with the trailing seven-day daily average of growth units

## Resolution Labels

- **Resolved**: the issue text contains an explicit fix marker or the rollout succeeded and the issue text describes corrective action
- **Open**: the issue text still signals a blocker, dependency, or follow-up
- **Unclear**: neither condition is strong enough to classify confidently

## Confidence

- **High**: at least two rollout summaries in the window plus durable memory context
- **Medium**: one rollout summary in the window or strong durable memory context
- **Low**: no rollout summaries in the window and only fallback context remains

## Honesty Rule

Always label brain-growth and percentage metrics as heuristics derived from memory artifacts. They are reporting aids, not literal cognition measurements.

