# Skill Routing and Agent Orchestration

## Purpose

This file provides guidance for Codex CLI on when to use skills and multi-agent orchestration.

## Skill Routing

### Default Behavior

When no skill is explicitly mentioned:
1. Start with `reviewer` skill for triage
2. Route to specialist skills if needed based on task type
3. Return to `reviewer` for final quality check

### Specialist Skills

Load specialist skills when the task clearly requires domain expertise:

- **reviewer**: Code review, quality gate, production readiness (includes DRY/simplification)
- **software-development-life-cycle**: Architecture, SDLC process, cross-domain engineering
- **web-development-life-cycle**: Web performance, SEO, browser compatibility
- **mobile-development-life-cycle**: Mobile lifecycle, permissions, offline sync
- **backend-and-data-architecture**: API design, database schemas, microservices, messaging
- **cloud-and-devops-expert**: Infrastructure as Code, CI/CD pipelines, container orchestration
- **qa-and-automation-engineer**: Test automation, E2E frameworks, load testing
- **security-and-compliance-auditor**: Vulnerability hunting, threat modeling, compliance
- **ui-design-systems-and-responsive-interfaces**: Design systems, responsive UI
- **ux-research-and-experience-strategy**: UX research, user testing
- **git-expert**: Complex git operations, branching strategy

### Keep It Simple

- Don't load multiple skills for simple tasks
- Use single skill when sufficient
- Let Codex CLI's native capabilities handle basic operations

## Multi-Agent Orchestration

### When to Use Multi-Agent

Use Codex CLI's multi-agent features (`multi_agent = true`) when:

1. **Parallel Research**: Need to search multiple sources simultaneously
2. **Large Codebase**: Exploring unfamiliar large codebases benefits from parallel search
3. **Independent Verification**: Complex architectural decisions need independent review
4. **Concurrent Tasks**: Truly independent work streams (research while implementing)

### When NOT to Use Multi-Agent

Don't force multi-agent for:
- Simple, straightforward tasks
- Single-file modifications
- Clear, well-defined problems
- Tasks where sequential execution is clearer

### Multi-Agent Collaboration Workflow (Codex)

When multi-agent is used, adhere to the following collaboration lifecycle to avoid "workaround" solutions and ensure high performance:
1. **Brainstorming & Parallelism**: Spawn sub-agents for independent tasks or to parallelize research and ideation. 
2. **Context Pruning (CRITICAL)**: Default `fork_context=false`. The upstream Codex `spawn_agent` contract defines `fork_context=true` as forking the current thread history into the new agent, so it copies parent context and can increase startup tokens, latency, and cost as the thread grows. Use `fork_context=true` only when the child truly needs the exact parent history. Otherwise, the main agent MUST summarize the current state and provide only the absolute necessary file paths, decisions, and context to the sub-agent.
3. **Execution & Feedback**: Sub-agents do not just execute blindly; they should collaborate. For complex fixes, sub-agents should propose the idea ("is it okay to implement like this?") before committing extensive code.
4. **Synthesis & Handoff**: Upon completion, a sub-agent MUST return both a **concise summary** and the **detailed context/findings** back to the main agent. 
5. **Main Agent Verification**: The main orchestrating agent MUST formally verify the sub-agent's findings against the original objective. If the work is incomplete or flawed, the main agent will send feedback and instruct the sub-agent to fix it.
6. **Wait Operations**: Wait on multiple agent IDs in one `wait` call instead of serial waits. Use a meaningful timeout for the task size rather than tight polling, do non-overlapping work before waiting again, and prefer one longer wait over many short waits.
7. **Required Completion**: If a spawned sub-agent is materially required for the task, the main agent MUST wait for it to reach a terminal state before finalizing. A sub-agent spawned for independent review, independent verification, or final-gap confirmation is required by default unless the user explicitly cancels or redirects that work. Do not silently ignore, abandon, or interrupt a required sub-agent because it is slow, because local evidence looks "good enough," or because the main agent is no longer blocked. If a `wait` call times out, increase the timeout, continue useful non-overlapping work, and wait again unless the user explicitly cancels or redirects the work.
8. **Lifecycle & Reuse**: Within the same project or workstream, keep at most one live sub-agent per role by default (for example, one `reviewer`). Before `spawn_agent`, check whether a suitable same-role agent already exists; prefer `send_input` to an active or idle agent, or `resume_agent` followed by `send_input` if the agent was previously closed. Spawn a second agent with the same role only when truly independent parallel work materially helps and reuse would block progress. Close a sub-agent only when that role is no longer needed for the current project or during final cleanup. Never close a required sub-agent while its status is still running or queued, and do not leave parallel processes running indefinitely.
9. **Performance Awareness & Delegation Thresholds (Solving the Bottleneck)**:
   - **The Bottleneck Risk**: Spawning, forking context, and terminating sub-agents introduces overhead. If the main agent spawns 5 sub-agents to fix a typo in 5 different files, the systemic overhead will be much slower than executing the tasks natively.
   - **Batching over Spawning**: For repetitive, mechanical, or straightforward tasks (e.g., simple file edits, lint fixes, renaming), the main orchestrating agent MUST execute these natively by batching Codex-native work (for example, one `exec_command` over multiple paths or one `js_repl` step that uses `codex.tool(...)` across a batch) rather than spawning sub-agents.
   - **The Delegation Threshold**: Only spawn a sub-agent if the task meets one of these criteria:
     - It requires a deep, multi-step 3-Round Research Loop.
     - It requires extensive architectural planning or speculative trial-and-error that would bloat the main agent's context history.
     - It requires specialized domain expertise (e.g., handing off a complex IaC terraform setup to the `cloud-and-devops-expert`).
   - **Single-Worker Batching**: If a rote task is too large for the main agent (e.g., refactoring 50 files), delegate the *entire* batch to a SINGLE `worker` or `default` sub-agent to process sequentially or via scripts, rather than spawning 50 individual agents.
   - **Runtime Fallback**: If child-agent controls are unavailable in the active Codex runtime, stay single-agent or use read-only parallel discovery only; do not write instructions that assume unavailable controls.

### Agent Profiles

Your Codex CLI has these agent profiles configured:

- **default**: Balanced speed and depth for general tasks
- **explorer**: Fast scanning for discovery and lightweight exploration
- **worker**: Implementation-heavy tasks with deeper reasoning
- **awaiter**: Wait/monitor tasks (keep cheap)
- **reviewer**: Feedback/review with balanced depth
- **architect**: Architecture and context reading

Use appropriate profiles based on task needs, but don't over-complicate.

## Execution Strategy

### Iterative Development Loop (MANDATORY)

**All tasks must follow this loop until production-ready:**

```
1. RESEARCH → 2. PLAN → 3. IMPLEMENT → 4. TEST → 5. FIX → 6. VERIFY → 7. REVIEW
                ↑                                                              ↓
                └──────────────── If issues found, loop back ─────────────────┘
```

**Loop continues until:**
- ✅ All tests passing
- ✅ No linting/type errors
- ✅ No bugs found
- ✅ Code review passes
- ✅ All requirements met

### 1. Research Loop (3-Round Escalation)

**When to research:**
- Before any non-trivial technical guidance, design decision, or implementation plan
- Any time the facts, tools, APIs, libraries, models, standards, or best practices may have changed
- Unfamiliar technology or API
- Need current best practices
- Unclear how to implement

**Escalating Research Process:**
- **Round 1 (Authoritative)**: Search the live web and official docs, official blogs, and official websites first. Treat internal knowledge as a starting hypothesis, not proof. If the answer is specific and accurate, stop here.
- **Round 2 (Community/Issues)**: If R1 is too general, search Reddit, StackOverflow, and GitHub issues for practical implementations or known bugs.
- **Round 3 (Broad)**: If R2 fails, search general forums, broader websites, and independent tech blogs.
- **Loop Back**: If the result remains too general, refine the search terms and restart the loop. You must rely on current external research plus internal logic to resolve technical ambiguities. Do not trust stale model memory for current facts, do not rely on prompting the user for technical facts you can verify yourself, and do not accept generic answers that still fail to solve the real problem or teach the missing knowledge precisely enough to proceed.

**Knowledge Retention (Memory Schema & Pruning):**
- **Do Not Bloat:** Never blindly append massive logs to memory files. 
- **Schema Enforcement:** When writing to `.codex_knowledge.md` or `.codex_lessons.md`, the agent MUST consolidate, deduplicate, and index the file. Use a strict Markdown schema:
  - `## [Topic/Error Name]`
  - `**Context:** Brief 1-sentence description.`
  - `**Resolution/Pattern:** The exact fix or architectural rule to apply.`
- Future agents must check this indexed memory to skip redundant research.
- **Layered Memory:** Keep memory layered the way a human would: high-level reusable guidance in summaries, task-family patterns in indexed memory, and exact commands/errors/evidence only in deeper task-specific notes when they are reusable.
- **Main-Agent Responsibility:** Before non-trivial work, the main agent MUST read relevant memory. After non-trivial work, the main agent MUST consolidate durable learnings, mistakes, validation paths, and failure shields into persistent memory so future agents stay aligned. Sub-agents may discover learnings, but the main agent is responsible for writing the durable memory update.
- **Quality Bar:** Memory entries must be actionable, deduplicated, and specific enough to change future behavior; do not store vague conclusions.

**Exit criteria:**
- Clear understanding of approach, verified against the target issue.
- Know which APIs/methods to use.
- Understand potential pitfalls.
- Core findings saved to memory.

### 2. Planning Loop

**All tasks require planning** - no exceptions:
- What will be changed and why
- How it will be validated
- What could go wrong
- Which files will be modified

**Exit criteria:**
- Clear implementation plan (1-3 sentences minimum)
- Validation strategy defined
- Risks identified

### 3. Impact Analysis Loop (CRITICAL - Before ANY code changes)

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

**Exit criteria:**
- Complete understanding of function and its dependencies
- All nested function calls traced and understood
- Impact of changes documented
- Confirmed no duplicate functionality exists
- Clear reasoning for why changes are needed

**If you cannot answer these questions, DO NOT MODIFY THE CODE. Execute the 3-Round Escalating Research Loop until you find the answer.**

### 4. Implementation Loop

**Write code following all quality standards:**
- Full descriptive names (no shortforms)
- Only requested features (no scope creep)
- Clean updates (delete old code)
- DRY (reuse existing code)
- Based on impact analysis from previous loop

**Exit criteria:**
- Code written
- Follows all quality standards
- No obvious errors
- Changes align with documented impact analysis

### 5. Testing Loop

**Test the implementation:**
- Run existing tests
- Write new tests if needed
- Test edge cases
- Test error scenarios

**Exit criteria:**
- All tests passing
- New tests written for new features
- Edge cases covered

### 6. Fix Loop (CRITICAL - Keep looping until clean)

**If any issues found, fix them:**

```
REPEAT UNTIL CLEAN:
  1. Run linter → Fix all errors
  2. Run type checker → Fix all errors
  3. Run tests → Fix all failures
  4. Check for bugs → Fix all bugs
  5. Run security scan → Fix vulnerabilities
  6. Check code quality → Fix issues
```

**Mistake & Solution Memory (Crucial):**
- If an error, bug, or mistake requires significant effort to resolve, you MUST record the mistake and its verified solution to `.codex_lessons.md`. 
- Follow the **Memory Schema & Pruning** rules above (Consolidate, Deduplicate, Index) to prevent file bloat. This ensures the system explicitly learns without exhausting the context window.

**Common issues to fix:**
- Linting errors (don't disable, fix them)
- Type errors (don't use `any`, fix them)
- Test failures (don't skip, fix them)
- Bugs (don't work around, fix them. Find the root cause.)
- Security issues (don't ignore, fix them)
- Code quality issues (shortforms, duplicates, etc.)

**Exit criteria:**
- ✅ Zero linting errors
- ✅ Zero type errors
- ✅ All tests passing
- ✅ No bugs found
- ✅ No security vulnerabilities
- ✅ Code quality standards met
- ✅ Complex fixes and root causes documented in memory

### 7. Verification Loop

**Verify the solution works:**
- Manual testing (if applicable)
- Check all requirements met
- Verify no regressions
- Check performance (if applicable)
- Verify observability (logs, metrics, tracing are implemented)
- Verify impact analysis predictions were correct

**Exit criteria:**
- Solution works as expected
- All requirements met
- No regressions introduced
- No unexpected side effects
- Proper logging/monitoring exists for production visibility

### 8. Review Loop

**Self-review before presenting:**
- Check for shortform names → Fix
- Check for unrequested features → Remove
- Check for dead code → Delete
- Check for duplicates → Refactor
- Check for hardcoded values → Move to config
- Check for missing tests → Add
- Verify impact analysis was thorough

**Exit criteria:**
- Code passes self-review
- Ready for user presentation

### Flow Control

**When to loop back:**
- ❌ Linting errors found → Loop to Fix
- ❌ Type errors found → Loop to Fix
- ❌ Tests failing → Loop to Fix
- ❌ Bugs found → Loop to Fix
- ❌ Security issues found → Loop to Fix
- ❌ Code quality issues found → Loop to Fix
- ❌ Requirements not met → Loop to Impact Analysis
- ❌ Unexpected side effects → Loop to Impact Analysis
- ❌ Review fails → Loop to Fix
- ❌ Impact analysis incomplete → Loop to Impact Analysis

**When to present to user:**
- ✅ All loops complete
- ✅ All exit criteria met
- ✅ Production-ready quality

### Loop Limits

**Maximum iterations per loop:**
- Research: 3 attempts (if still unclear, escalate to advanced code context gathering)
- Impact Analysis: No limit (must understand before coding)
- Implementation: No limit (keep fixing until clean)
- Fix: No limit (must fix all issues)
- Review: 3 attempts (if still failing, escalate to architectural review)

**If stuck in loop:**
1. Identify the blocker
2. Try alternative approach
3. If still stuck after 3 attempts, review historical mistake/solution memory and rethink the core architectural assumption

### General Approach

1. **Understand**: Read requirements carefully
2. **Research**: If needed (see Research Loop)
3. **Plan**: Document approach (see Planning Loop)
4. **Analyze Impact**: Trace functions and dependencies (see Impact Analysis Loop - CRITICAL)
5. **Implement**: Write code (see Implementation Loop)
6. **Test**: Verify it works (see Testing Loop)
7. **Fix**: Fix all issues (see Fix Loop - CRITICAL)
8. **Verify**: Confirm solution (see Verification Loop)
9. **Review**: Self-review (see Review Loop)
10. **Deliver**: Present to user (only when production-ready)

### Code Quality Standards

**CRITICAL - Always enforce these rules:**

**Readability (Non-Negotiable):**
- **NO shortform variable names**: Use full, descriptive names
  - ❌ BAD: `usr`, `btn`, `tmp`, `data`, `res`, `req`, `arr`, `obj`, `fn`, `cb`, `idx`, `len`, `str`, `num`
  - ✅ GOOD: `user`, `button`, `temporaryValue`, `userData`, `response`, `request`, `userArray`, `userObject`, `handleClick`, `callback`, `currentIndex`, `arrayLength`, `userName`, `itemCount`
- **NO single-letter variables** except loop counters in simple loops (i, j, k)
- **NO abbreviations** unless universally known (URL, API, HTTP, ID)
- **Clear function names**: Verb + noun (e.g., `getUserData`, `calculateTotal`, `validateEmail`)

**Scope Discipline & Greenfield vs. Brownfield Rules:**
- **Brownfield (Existing Code)**: Strict compliance. ONLY implement what was requested. NO unrequested features, NO refactoring unrelated code, NO speculative "future-proofing".
- **Greenfield (New Projects)**: Architectural Innovation is ALLOWED. If scaffolding a new project, you MUST set up advanced, scalable boilerplate (e.g., proper dependency injection, generic types, robust folder structures) proactively to prevent future technical debt, even if not explicitly detailed by the user.
- **When updating a feature:**
  - ✅ Just update it - don't keep old code
  - ✅ Delete unused code completely
  - ❌ NO backward compatibility unless explicitly requested

**DRY (Don't Repeat Yourself):**
- Reuse existing code, extract shared logic
- No duplicate functions or logic

**Simplicity:**
- Minimal solution that works
- No over-engineering
- No premature optimization
- **Security**: Validate inputs, no injection risks
- **Testing**: Specific requirements below

### Testing Requirements

**New Features:**
- Unit tests for business logic
- Integration test for happy path
- Edge case coverage

**Bug Fixes:**
- Test that fails before fix
- Test passes after fix
- Regression test for related functionality

**Refactoring:**
- All existing tests must pass
- No test skipping or removal without justification

**Prohibited:**
- Using `.skip()` or `.only()` in committed code
- Commenting out failing tests
- Mocking critical validation logic

## Feature Flags

Your Codex CLI has these features enabled:
- `unified_exec`: Unified execution mode
- `js_repl`: JavaScript REPL for complex operations
- `js_repl_tools_only`: Route tools through js_repl
- `multi_agent`: Multi-agent orchestration
- `child_agents_md`: Agent markdown support
- `memories`: Persistent memory across sessions

Use features when they provide clear value, not by default.

## Best Practices

### Do:
- Read files before modifying
- Understand existing patterns
- Write minimal, focused code
- Test critical functionality
- **Perform Deep Research** when encountering technical blockers, bug fixes, or how-to implementations. Rely on the 3-round research loop and internal analysis rather than interrupting the user for technical help.
- **Use the `request_user_input` tool for Clarification**: If the business requirements, user stories, or product logic are ambiguous, you MUST use `request_user_input` to clarify. It is critical that the agent and the user are on the same page to prevent "drifting" and building the wrong product. There is NO LIMIT to how many times you can use `request_user_input` for requirement clarification. Do not guess the user's intent.
- Use appropriate agent profiles for task type

### Don't:
- Force multi-agent for simple tasks
- Over-engineer solutions
- Add unnecessary features
- Skip security considerations
- Ignore existing code patterns
- Create duplicate functionality

## Prohibited Shortcuts

**Never take these shortcuts** - they create technical debt and maintenance problems:

### Code Quality Shortcuts (CRITICAL)
- **Shortform Variable Names**: Using `usr`, `btn`, `tmp`, `data`, `res`, `req`, `arr`, `obj`, `fn`, `cb` instead of full descriptive names
- **Single-Letter Variables**: Using `x`, `y`, `z`, `a`, `b`, `c` (except i, j, k in simple loops)
- **Cryptic Abbreviations**: Using unclear abbreviations that require mental translation
- **Disabling Linting**: Using `// eslint-disable` or `// @ts-ignore` without clear justification
- **Any Type Abuse**: Using `any` type in TypeScript instead of proper typing
- **Copy-Paste**: Duplicating code instead of extracting shared logic
- **Hardcoding**: Hardcoding values instead of using configuration

### Scope Creep Shortcuts (CRITICAL)
- **Adding Unrequested Features**: Implementing features that weren't asked for
- **Unnecessary Refactoring**: Refactoring code not related to the task
- **Over-Engineering**: Adding abstraction, configuration, or flexibility that wasn't requested
- **Backward Compatibility**: Adding compatibility layers when just updating the feature
- **Keeping Dead Code**: Keeping old code "just in case" instead of deleting it
- **Defensive Programming**: Adding error handling for scenarios that can't happen
- **Speculative Features**: Adding features "for future use"

### Testing Shortcuts
- **Test Skipping**: Using `.skip()`, `.only()`, or commenting out failing tests
- **Incomplete Coverage**: Skipping tests for "simple" code or edge cases
- **Mock Abuse**: Mocking critical validation or business logic

### Security Shortcuts
- **Validation Skipping**: Removing validation "temporarily" or only validating client-side
- **Force Flags**: Using `--force`, `--no-verify`, or similar without understanding why
- **Secret Exposure**: Committing secrets, API keys, or credentials

### Performance Shortcuts
- **Premature Optimization Removal**: Removing optimization because "it's too complex"
- **Ignoring Metrics**: Not measuring performance impact of changes

**If you're tempted to take a shortcut, stop and ask:**
1. Why is the proper solution difficult?
2. What's the root cause of the problem?
3. How can I solve it properly?
4. What help do I need?

## Windows Environment

When running commands on Windows:
- Route tool work through `js_repl` with `codex.tool(...)` first.
- Inside `codex.tool("exec_command", ...)`, prefer direct command strings and avoid wrapping ordinary commands in `powershell.exe -NoProfile -Command "..."`.
- Use PowerShell only for PowerShell cmdlets/scripts or when shell-specific quoting, pipelines, or object semantics are required.
- Use `cmd.exe /c` for `.cmd`/batch-specific commands or `%VAR%` syntax.
- Git Bash available but not assumed

## Code Review Requirements

**Mandatory code review** (use reviewer skill) when:
- Changes touch more than 2 files
- Changes exceed 50 lines
- Authentication, authorization, or data handling changes
- External API integration
- Security-sensitive code
- Performance-critical code

**Security review required** for:
- User input handling
- Database queries
- File system operations
- Network requests
- Authentication/authorization logic
- Cryptography or secrets handling

## Automated Quality Checks

Before marking any task complete, verify:

### Linting & Type Checking
- All linting errors resolved (not disabled with `// eslint-disable`)
- All TypeScript errors resolved (not suppressed with `@ts-ignore`)
- Code follows project style guide

### Testing
- All tests passing (not skipped with `.skip()`)
- New features have unit tests
- Bug fixes have regression tests
- Test coverage maintained or improved

### Security
- No hardcoded secrets or credentials
- Input validation at all boundaries
- Security scan passes (no high/critical vulnerabilities)
- Dependencies up to date (no known CVEs)

### Code Quality
- No duplicate code (DRY violations)
- No commented-out code
- No debug statements (console.log, debugger)
- No TODO/FIXME without issue tracking

### Performance
- Performance impact measured (if applicable)
- No obvious performance regressions
- Images optimized
- Bundle size within budget

**Tools to use:**
- ESLint, Prettier for linting/formatting
- TypeScript for type checking
- npm audit, yarn audit for security
- Jest, Vitest, Playwright for testing
- Lighthouse, WebPageTest for performance

## Quality Gates

Before completing any task, verify ALL of these:
1. ✓ Requirements met completely
2. ✓ Code is clean and maintainable
3. ✓ All linting/type errors resolved (not disabled)
4. ✓ All tests passing (not skipped)
5. ✓ No security issues or vulnerabilities
6. ✓ No secrets or credentials committed
7. ✓ No duplicate code
8. ✓ Changes are minimal and focused
9. ✓ Documentation updated (if needed)
10. ✓ Code review completed (if required)

## Reasoning Effort Levels

Your agent profiles use these reasoning effort levels:
- **high**: Default, worker, architect (balanced depth)
- **xhigh**: Reviewer (thorough analysis)

Codex CLI will use appropriate effort based on agent profile.

## Skill Model Policy

- Do not pin a specific model inside root Codex `agents/openai.yaml` files. Let the workspace default model handle that choice; this repo assumes the workspace default is `gpt-5.4`.
- Treat `reasoning_effort` as the main skill-level control.
- Use `xhigh` only for the complex think-heavy skills.
- Use `high` for implementation-heavy skills and routine workspace-writing tasks.
- When any Codex skill executes tools in this runtime, route the tool work through `js_repl` with `codex.tool(...)` rather than calling tools directly.

## Summary

Keep execution simple and focused. Use multi-agent and specialist skills when they add clear value. Prioritize code quality, security, and maintainability. Let Codex CLI's native orchestration handle complexity naturally.
