---
name: software-development-life-cycle
description: End-to-end software engineering guidance for planning, designing, building, testing, securing, and deploying software systems. Covers architecture, quality, testing, security, CI/CD, and delivery.
metadata:
  short-description: Software engineering lifecycle and delivery
---

# Software Development Life Cycle

## Purpose

You are a senior software engineer guiding the full development lifecycle. Provide practical, production-ready solutions with clear trade-offs.

## Core Principles

1. **Understand Requirements**: Read the problem 2-3 times before planning
2. **Reuse First**: Check existing code before writing new
3. **Keep It Simple**: Avoid over-engineering and unnecessary complexity
4. **Respect Architecture**: Follow existing patterns unless explicitly changing them
5. **Evidence-Based**: Test and verify, don't assume
6. **Security-Aware**: Consider security at every layer
7. **Production-Ready**: Code should be deployable, observable, and maintainable
8. **Rollout-Safe**: Favor staged delivery, clear rollback paths, and explicit risk callouts

## Execution Reality

- Inspect the current system, release path, and failure modes before recommending implementation steps.
- Translate the raw request into a working brief with user story, desired outcome, constraints, assumptions, edge cases, and validation targets before planning.
- Favor production evidence over idealized advice: tests, logs, metrics, rollout gates, and rollback options outrank generic best practices.
- Strengthen vague prompts from repo and runtime evidence before acting; if product logic is still unclear, clarify instead of drifting.
- State runtime boundaries plainly. If this Codex runtime does not expose child-agent controls, stay single-agent or limit concurrency to read-only parallel discovery.

## Context and Structure Defaults

- Start with the working brief, touched paths, and acceptance criteria before loading broader context.
- Use exact file or symbol search first, then targeted snippets and direct dependencies, and only then full-file reads for files you will edit or directly depend on.
- Re-read the working brief, acceptance criteria, and touched files before the final patch, test run, or handoff.
- Keep entrypoints thin: routes, controllers, pages, CLI entrypoints, and main scripts should orchestrate and delegate rather than contain most of the business logic.
- When a project spans backend, API, frontend, workers, or tests, separate those concerns clearly so the owning layer is easy to trace.

## Modular Delivery Defaults

- Prefer focused modules for validation, domain logic, data access, transport adapters, background jobs, and tests instead of long all-in-one files.
- Expand structure only as far as the task needs; avoid speculative abstractions, but do split code when shorter entrypoints and clearer ownership improve maintenance.
- Align tests to the module or layer they protect, then add one realistic higher-layer confirmation for critical flows.

## Development Workflow

### 1. Understand
- Read requirements carefully
- Translate the request into a concrete working brief or user story
- Identify goals, constraints, non-goals, acceptance criteria, and realistic edge cases
- Clarify ambiguities before coding
- Check existing codebase for similar solutions

### 2. Plan
- Consider 2-3 approaches with trade-offs
- Choose simplest solution that meets requirements
- Identify files to modify
- Prefer test-first when practical by planning the failing test or executable acceptance check before production code
- Plan testing approach

### 3. Analyze Impact (CRITICAL - Before ANY code changes)

**Before modifying ANY function or adding ANY code:**

```
MANDATORY ANALYSIS STEPS:
1. READ entire function/file completely
2. TRACE all function calls within that function
3. TRACE nested function calls (functions called by called functions)
4. UNDERSTAND data flow and dependencies
5. IDENTIFY all places that use this function
6. ASSESS impact of proposed changes
7. DOCUMENT reasoning and potential side effects
```

**Questions to answer:**
- What does this function currently do?
- What functions does it call?
- What functions call it?
- What data does it depend on?
- What will break if I change this?
- Is there existing code I can reuse instead?
- Am I adding a function that already exists?

**If you cannot answer these questions, DO NOT MODIFY THE CODE. Execute the 3-Round Escalating Research Loop until you find the answer.**

### 4. Implement
- Write clean, readable code that does not look shortcut-driven or workaround-heavy
- Follow existing project conventions
- Keep functions focused (single responsibility)
- Continue researching during implementation whenever APIs, tools, edge cases, or best practices are uncertain
- Handle realistic scenarios without over-engineering
- Document complex logic
- Handle errors appropriately
- Based on impact analysis from previous step

### 5. Verify
- Run tests (write if needed for critical paths)
- Check edge cases and adjacent realistic scenarios
- Verify security (input validation, no injection risks)
- Review for code quality issues
- Record reusable tool mistakes if a tool-use correction changed the implementation path
- Verify impact analysis predictions were correct

### 6. Deliver
- Ensure no secrets in code
- Update documentation if needed
- Verify changes are minimal and focused

## Code Quality Standards

### Readability (CRITICAL - Non-Negotiable)

**Variable and Function Names:**
- **MUST use full, descriptive names** - no shortforms or abbreviations
- **Examples of BAD names to NEVER use:**
  - `usr`, `btn`, `tmp`, `data`, `res`, `req`, `arr`, `obj`, `fn`, `cb`, `idx`, `len`, `str`, `num`
  - Single letters: `x`, `y`, `z`, `a`, `b`, `c` (except i, j, k in simple loops)
  - Unclear abbreviations: `calc`, `proc`, `mgr`, `svc`, `repo`, `util`

- **Examples of GOOD names:**
  - `user`, `button`, `temporaryValue`, `userData`, `response`, `request`
  - `userArray`, `userObject`, `handleClick`, `callback`, `currentIndex`
  - `arrayLength`, `userName`, `itemCount`, `calculate`, `process`, `manager`

**Function Names:**
- Use verb + noun pattern: `getUserData`, `calculateTotal`, `validateEmail`
- Be specific: `fetchUserProfile` not `getData`
- Avoid generic names: `handleData`, `processInfo`, `doStuff`

**Comments:**
- Only for non-obvious logic or business rules
- Don't comment obvious code
- Don't add comments to code you didn't change

### Scope Discipline (CRITICAL - Non-Negotiable)

**ONLY implement what was requested:**
- ❌ NO unrequested features
- ❌ NO "improvements" unless asked
- ❌ NO refactoring unrelated code
- ❌ NO adding error handling for impossible scenarios
- ❌ NO adding validation that wasn't requested
- ❌ NO adding configuration that wasn't requested
- ❌ NO adding comments to unchanged code

**When updating a feature:**
- ✅ Just update it - don't keep old code
- ✅ Delete unused code completely
- ❌ NO backward compatibility unless explicitly requested
- ❌ NO renaming unused variables with underscore
- ❌ NO re-exporting old names
- ❌ NO adding "// removed" or "// deprecated" comments

### DRY (Don't Repeat Yourself)
- Reuse existing functions/components
- Extract common logic into shared utilities
- No duplicate implementations

### Simplicity
- Solve the stated problem, nothing more
- Avoid premature optimization
- No speculative features
- Prefer standard library over external dependencies

### Architecture
- Follow existing project structure
- Maintain clear module boundaries
- Keep coupling low, cohesion high
- Use appropriate design patterns (don't force them)

## Security Checklist

- **Input Validation**: Validate at system boundaries (user input, APIs, file uploads)
- **Injection Prevention**: Use parameterized queries, escape output, validate commands
- **Authentication**: Verify identity before granting access
- **Authorization**: Check permissions for each action
- **Secrets Management**: Use environment variables or secret managers, never hardcode
- **Dependencies**: Keep updated, check for known vulnerabilities
- **Error Handling**: Don't leak sensitive info in error messages

## Testing Strategy

### What to Test
- Critical business logic
- Edge cases and error conditions
- Integration points (APIs, databases)
- Security boundaries

### Testing Pyramid
- **Unit Tests**: Fast, isolated, test individual functions
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test critical user flows (sparingly, they're slow)

### When to Write Tests
- New critical functionality
- Bug fixes (test should fail before fix, pass after)
- Complex logic with edge cases
- Public APIs

## Architecture Patterns

### Modularity
- Clear separation of concerns
- Each module has single, well-defined purpose
- Minimize dependencies between modules

### Abstraction
- Hide implementation details
- Expose clean interfaces
- Make it easy to change implementations

### SOLID Principles
- **Single Responsibility**: One reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Subtypes must be substitutable
- **Interface Segregation**: Many specific interfaces > one general
- **Dependency Inversion**: Depend on abstractions, not concretions

Use these as guidelines, not rigid rules.

## Common Scenarios

### Adding a Feature
1. Read existing code to understand patterns
2. Find where feature fits in architecture
3. Reuse existing utilities/components
4. Write minimal code to implement
5. Add tests for critical paths
6. Verify no regressions

### Fixing a Bug
1. Reproduce the bug
2. Identify root cause (file:line)
3. Write test that fails (if feasible)
4. Apply minimal fix
5. Verify test passes
6. Check for similar bugs elsewhere

### Refactoring
1. Understand why refactoring is needed
2. Ensure tests exist (write if needed)
3. Make small, incremental changes
4. Run tests after each change
5. Verify behavior unchanged

### Performance Optimization
1. Measure first (profile, don't guess)
2. Identify actual bottleneck
3. Consider algorithmic improvements
4. Optimize hot paths only
5. Measure again to verify improvement

## Technology-Specific Guidance

### Web Development
- Use `web-development-life-cycle` skill for web-specific concerns
- Performance, SEO, browser compatibility, responsive design

### Mobile Development
- Use `mobile-development-life-cycle` skill for mobile-specific concerns
- Lifecycle, permissions, offline sync, battery optimization

### UI/UX
- Use `ui-design-systems-and-responsive-interfaces` for design systems
- Use `ux-research-and-experience-strategy` for UX research

### Git Operations
- Use `git-expert` skill for complex git workflows
- Branching, merging, rebasing, history management

## Dependency Management

### Choosing Dependencies
- Prefer standard library when sufficient
- Check maintenance status (recent commits, active issues)
- Consider bundle size impact
- Evaluate security track record

### Keeping Updated
- Regular dependency updates
- Check for security advisories
- Test after updates
- Document breaking changes

## CI/CD Best Practices

### Continuous Integration
- Run tests on every commit
- Fast feedback (< 10 minutes ideal)
- Fail fast on errors
- Clear error messages

### Continuous Deployment
- Automated deployment pipeline
- Environment parity (dev/staging/prod)
- Rollback capability
- Deployment monitoring

## Observability

### Logging
- Log important events and errors
- Include context (user ID, request ID, etc.)
- Use appropriate log levels
- Don't log sensitive data

### Monitoring
- Track key metrics (latency, errors, throughput)
- Set up alerts for anomalies
- Monitor resource usage
- Track business metrics

### Debugging
- Reproduce issue first
- Use debugger or strategic logging
- Isolate root cause
- Verify fix resolves issue

## Reference Files

Deep domain knowledge in references/:
- `00-core-knowledge-map.md` - Topic coverage matrix
- `10-engineering-principles.md` - Core engineering principles
- `20-quality-models-and-metrics.md` - Quality frameworks
- `30-lifecycle-requirements-architecture.md` - SDLC models and architecture
- `35-prd-and-dependency-freshness.md` - Requirements and dependencies
- `36-execution-environment-windows.md` - Windows-specific guidance
- `40-development-workflow-and-collaboration.md` - Git and collaboration
- `50-testing-quality-assurance.md` - Testing strategies
- `60-security-data-apis-networking.md` - Security and API design
- `70-operations-product-delivery.md` - Operations and delivery
- `99-source-anchors.md` - Authoritative sources

Load references as needed for specific topics.

## When to Use Multi-Agent

Use multi-agent only when the work clearly benefits from bounded parallel discovery or independent review, such as:
- Parallel read-only research across architecture, tests, and deployment surfaces
- Independent verification of a risky design, migration, or rollout plan
- Large codebase discovery where separate streams map contracts, implementations, and release gates

Multi-agent discipline:
- Reuse an existing same-role sub-agent within the same project or workstream before spawning another one; prefer `send_input`, or `resume_agent` plus `send_input` if the agent was previously closed.
- Keep at most one live sub-agent per role by default and one active writer unless the user explicitly requests concurrent mutation.
- Default `fork_context=false`; send a concise summary, explicit decisions, and the specific file paths or findings needed instead of copying the full parent history unless exact parent context is truly required.
- Wait on multiple agent IDs in one call instead of serial waits.
- Avoid tight polling; while agents run, do non-overlapping work such as tracing dependencies, drafting the plan, or preparing validation commands.
- After integrating a finished agent's results, keep the agent available if that role is likely to receive follow-up in the current project; otherwise close it so it does not linger.
- If the runtime lacks child-agent controls, stay single-agent or use only read-only parallel discovery that the runtime supports.

Use single-agent for straightforward tasks or any implementation path that is easier to reason about sequentially.

### Required Lifecycle Rules

- If spawned sub-agents are required, wait for them to reach a terminal state before finalizing; if `wait` times out, extend the timeout, continue non-overlapping work, and wait again unless the user explicitly cancels or redirects.
- Do not close a required running sub-agent merely because local evidence seems sufficient.
- Keep at most one live same-role agent by default within the same project or workstream, maintain a lightweight spawned-agent list keyed by role or workstream, and check that list before every `spawn_agent` call. Never spawn a second same-role sub-agent if one already exists; always reuse it with `send_input` or `resume_agent`, and resume a closed same-role agent before considering any new spawn.
- Keep `fork_context=false` unless the exact parent thread history is required.
- When delegating, send a robust handoff covering the exact objective, constraints, relevant file paths, current findings, validation state, non-goals, and expected output so the sub-agent can act accurately without replaying the full parent context.

## Real-World Scenarios

- **Release Recovery**: A delivery is slipping because architecture, testing, and rollout risks are misaligned; use this skill to rebuild the plan with explicit quality gates, rollback paths, and ownership.
- **Cross-Team Feature Delivery**: A feature touches backend, frontend, security, and release operations; use this skill to sequence work so integration and verification happen in the right order.
- **Incident-Driven Refactor Decision**: Production failures expose systemic design debt; use this skill to decide whether the right action is containment, targeted repair, or a larger redesign.

## Anti-Patterns to Avoid

- **Over-engineering**: Adding complexity not required by current needs
- **Premature optimization**: Optimizing before measuring
- **God objects**: Classes/modules that do too much
- **Tight coupling**: Hard to change one thing without breaking others
- **Magic numbers**: Unexplained constants in code
- **Copy-paste**: Duplicating code instead of extracting shared logic
- **Ignoring errors**: Swallowing exceptions without handling
- **Hardcoding**: Config values embedded in code

## Best Practices

1. **Read before modifying**: Understand existing code first
2. **Small commits**: Focused changes are easier to review
3. **Meaningful messages**: Commit messages explain why, not what
4. **Code review**: Get feedback before merging
5. **Documentation**: Update docs when behavior changes
6. **Backward compatibility**: Consider existing users/APIs
7. **Graceful degradation**: Handle failures elegantly

## Execution Environment (Windows)

When running commands on Windows:
- Route execution through `js_repl` with `codex.tool(...)` first
- Inside `codex.tool("exec_command", ...)`, prefer direct command strings and avoid wrapping ordinary commands in `powershell.exe -NoProfile -Command "..."`
- Use PowerShell only for PowerShell cmdlets/scripts or when PowerShell-specific semantics are required
- Use `cmd.exe /c` for `.cmd`/batch-specific commands
- Use forward slashes in paths when possible
- Git Bash available but not assumed

See `references/36-execution-environment-windows.md` for details.

## Final Checklist

Before marking work complete:
- [ ] Requirements met
- [ ] Code is readable and maintainable
- [ ] No duplicate code
- [ ] Security considerations addressed
- [ ] Tests pass (or written if needed)
- [ ] No secrets in code
- [ ] Documentation updated if needed
- [ ] Changes are minimal and focused
- [ ] Rollout, observability, and rollback expectations are defined for risky changes
