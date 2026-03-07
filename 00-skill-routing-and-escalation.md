# Skill Routing and Escalation (Codex CLI)

This document defines how skills should route to each other and when to escalate to specialist skills.

**Note**: This is for Codex CLI only. Claude Code has separate skills in the `claude/` directory.

## Routing Principles

1. **Start Broad, Go Specific**: Begin with general skills, route to specialists when needed
2. **Single Responsibility**: Each skill has a clear domain, don't overlap
3. **Explicit Routing**: Skills should explicitly mention when to use other skills
4. **User Control**: Let users choose skills, but suggest appropriate ones
5. **Avoid Circular Routing**: Don't create routing loops between skills

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

## Codex CLI Skills (11 Total)

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

## Summary

- **REVIEWER**: Final quality gate, DRY enforcement, code simplification
- **SOFTWARE-DEVELOPMENT-LIFE-CYCLE**: Core SDLC, general architecture
- **WEB/MOBILE/BACKEND**: Domain-specific implementation
- **DEVOPS & CLOUD**: Deployment, infrastructure, and pipeline automation
- **QA & SECURITY**: Robustness, automated testing, and cyber defense
- **UI/UX**: Design and research specialists
- **GIT-EXPERT**: Version control specialist

Route explicitly, avoid circular dependencies, and always provide value when routing.
