# Lifecycle, Requirements, and Architecture

## Agile and SDLC Model Selection

Choose model by risk profile, uncertainty, and regulatory constraints:

- Waterfall: stable requirements, strong stage gates, heavy compliance contexts.
- V-Model: test-planning tied to each development phase; strong verification traceability.
- Spiral: risk-driven iterative loops for uncertain/high-risk systems.
- Iterative/Incremental: evolving requirements with regular feedback loops.
- Agile: adaptive planning, short increments, continuous stakeholder feedback.

## Requirements Engineering

Define requirements in layered form:

1. Business outcomes
2. Functional requirements
3. Non-functional requirements
4. Constraints and compliance rules
5. Acceptance criteria

### Functional vs Non-Functional

- Functional: what the system must do.
- Non-functional: how well it must perform (security, reliability, latency, usability, maintainability, etc).

### User Stories and Acceptance Criteria

- Use clear user stories with role-goal-benefit format.
- Use measurable acceptance criteria (Given/When/Then style when useful).
- Keep traceability from requirement to tests and release notes.

## Prioritization and Scope Management

- MoSCoW: Must/Should/Could/Won't for release planning.
- Kano: classify by basic expectations, performance drivers, delight factors.
- Maintain a scope baseline and change-control policy.
- Track requirement volatility and its delivery impact.

## Architecture Basics

### Common Styles

- Layered architecture
- Client-server
- Monolith
- Microservices

### Trade-off Lens

Evaluate each architecture by:

- Team topology and skill distribution
- Deployment independence needs
- Operational complexity tolerance
- Data consistency requirements
- Reliability and latency targets

## UML and Diagramming Baseline

Use diagrams as communication artifacts, not decoration:

- Use case diagram: actors and system goals
- Sequence diagram: interaction timing and control flow
- Class diagram: static structure and relationships
- Activity diagram: workflow logic and branching
- ERD: data entities, relationships, and cardinality

Keep diagrams versioned with the system and updated when interfaces evolve.

## Design Patterns Baseline

Use patterns intentionally:

- Factory for controlled object creation
- Strategy for interchangeable business rules
- Observer for event-driven notifications
- MVC/MVVM for UI separation concerns

Avoid forced pattern usage that increases accidental complexity.
