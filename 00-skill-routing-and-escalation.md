# Skill Routing and Escalation (Codex CLI)

This document defines how skills should route to each other, when to escalate to specialist skills, and how the Codex-first skill pack stays fast, focused, and token-efficient.

## Routing Principles

1. **Start Broad, Go Specific**: Begin with general skills, route to specialists when needed
2. **Single Responsibility**: Each skill has a clear domain, don't overlap
3. **Explicit Routing**: Skills should explicitly mention when to use other skills
4. **User Control**: Let users choose skills, but suggest appropriate ones
5. **Avoid Circular Routing**: Don't create routing loops between skills
6. **Use the Cheapest Useful Context First**: Start with exact file or symbol search, then targeted snippets, then full-file reads only when the edit scope requires it
7. **Prefer Surgical Patches**: Keep stable context, patch only impacted ranges, and avoid rewriting untouched sections

## Skill Hierarchy (Codex CLI)

```
┌─────────────────────────────────────────────────────────────┐
│                         REVIEWER                             │
│    (Final quality gate, DRY enforcement, orchestrator)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────┐
│  SOFTWARE-DEVELOPMENT-LIFE-CYCLE     │
│  (Core SDLC, architecture, general)  │
└──────────────────────────────────────┘
                │
                ├────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐
                │            │            │            │            │            │            │            │            │
                ▼            ▼            ▼            ▼            ▼            ▼            ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   WEB    │  │  MOBILE  │  │ BACKEND  │  │  DEVOPS  │  │ QA &     │  │ SECURITY │  │    UI    │  │    UX    │  │   GIT    │
│   LIFE   │  │   LIFE   │  │  & DATA  │  │ & CLOUD  │  │ AUTOMAT. │  │ & COMPL. │  │  DESIGN  │  │ RESEARCH │  │  EXPERT  │
│  CYCLE   │  │  CYCLE   │  │          │  │          │  │          │  │          │  │  SYSTEMS │  │ STRATEGY │  │          │
└──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## Codex CLI Skills (12 Total)

1. **reviewer** - Production readiness, DRY enforcement, code simplification
2. **software-development-life-cycle** - Full SDLC, architecture
3. **web-development-life-cycle** - Web frontend and full-stack frameworks
4. **mobile-development-life-cycle** - Mobile development
5. **backend-and-data-architecture** - APIs, microservices, databases, message queues
6. **cloud-and-devops-expert** - Infrastructure as Code, CI/CD, container orchestration
7. **qa-and-automation-engineer** - TDD, E2E frameworks, test automation
8. **security-and-compliance-auditor** - Threat modeling, vulnerability hunting, compliance
9. **ui-design-systems-and-responsive-interfaces** - UI design
10. **ux-research-and-experience-strategy** - UX research
11. **git-expert** - Version control
12. **memory-status-reporter** - Memory health, learning recaps, and mistake-resolution reporting

## Context Efficiency Defaults

Use this ladder before loading large amounts of context:

1. **Working brief first** — translate the request into user story, outcome, constraints, acceptance criteria, and validation plan
2. **Exact retrieval first** — use symbol, path, or keyword search to narrow the candidate files
3. **Targeted reads second** — read only the relevant sections or neighboring call sites before expanding
4. **Full reads only for edit scope** — fully read the files that will actually be changed plus direct dependencies
5. **Surgical patching** — update only the impacted ranges instead of rewriting whole files
6. **Final re-read** — re-read the working brief and touched files before the final answer or validation step

## Final Output Memory Snapshot

For non-trivial tasks, the final answer should include a compact learning snapshot when memory artifacts are available:

- what Codex learned today,
- mistakes and tool-use mistakes encountered,
- whether they were resolved,
- heuristic memory-health stats such as growth or momentum.

Treat these values as artifact-based heuristics, not literal cognition.

## Summary

- **REVIEWER**: Final quality gate, DRY enforcement, code simplification
- **SOFTWARE-DEVELOPMENT-LIFE-CYCLE**: Core SDLC, general architecture
- **WEB/MOBILE/BACKEND**: Domain-specific implementation
- **DEVOPS & CLOUD**: Deployment, infrastructure, and pipeline automation
- **QA & SECURITY**: Robustness, automated testing, and cyber defense
- **UI/UX**: Design and research specialists
- **MEMORY STATUS REPORTER**: Human-style memory health, daily learning, and mistake-status reporting
- **GIT-EXPERT**: Version control specialist

Route explicitly, avoid circular dependencies, keep context lean, and always provide value when routing.
