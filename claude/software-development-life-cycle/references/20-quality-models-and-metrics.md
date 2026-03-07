# Quality Models and Metrics

## Quality Models

### ISO/IEC 9126 (Historical Baseline)

- Treat as a legacy quality model for historical alignment.
- Core characteristics include functionality, reliability, usability, efficiency, maintainability, and portability.
- Use it when organizations explicitly require 9126 terminology.

### ISO/IEC 25010 (Current Evolution of 9126)

- Use as modern default for software product quality discussions.
- Include characteristics such as functional suitability, performance efficiency, compatibility, usability, reliability, security, maintainability, and portability.
- Map project NFRs to 25010 quality characteristics.

### Boehm's Software Quality Model

- Use for historical and conceptual quality decomposition.
- Emphasize utility, maintainability, and portability families.
- Use as a comparative model when discussing quality trade-offs and evolution of quality thinking.

## Measurement Philosophy

- Never optimize a single metric in isolation.
- Pair leading indicators (e.g., test coverage trend, cycle time) with lagging indicators (production defects, outage minutes).
- Use metric suites with context and confidence intervals where possible.

## Metric Categories

### Product Metrics

- Defect density
- Reliability indicators (MTBF/MTTR context)
- Complexity indicators
- Performance indicators (latency, throughput, resource usage)

### Process Metrics

- Lead time and cycle time
- Deployment frequency
- Change failure rate
- Mean time to restore

### People/Team Metrics

- Bus factor and ownership spread
- Review responsiveness
- Collaboration quality signals
- Learning and documentation contributions

Avoid individual surveillance or punitive interpretation of people metrics.

## Halstead Metrics

Use as approximate complexity signals derived from operators/operands:

- Program vocabulary and length
- Volume
- Difficulty
- Effort

Use only as one signal among others; do not equate with maintainability by itself.

## Function Point (FP) Analysis

Use FP for technology-agnostic functional size estimation:

- Count logical user-visible functions (inputs, outputs, inquiries, files, interfaces)
- Weight by complexity
- Normalize for estimation and benchmarking

FP is useful when comparing projects across different languages/stacks.

## Lines of Code (LOC)

Use LOC carefully:

- Good for trend/context in a single codebase.
- Poor as productivity proxy across teams or languages.
- Distinguish source LOC vs generated LOC.

## Practical Metric Set (Recommended Starter)

1. Requirement volatility rate
2. Cycle time from ready to done
3. Escaped defect count and severity
4. Change failure rate
5. MTTR
6. P95 latency and error rate for critical flows
7. Test suite duration and flake rate
8. Coverage trend (with known blind spots documented)
