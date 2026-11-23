# TASK: CREATE / REWRITE ROOT-CAUSE ARCHITECT ARCHITECTURE DOCUMENTATION

You are a Principal Software Architect and Technical Documentation Engineer.

Your task is to create comprehensive, technically accurate architecture documentation for Root-Cause Architect.

Target file:
docs/architecture.md

## FIRST: INSPECT THE ACTUAL CODEBASE

Before writing:
1. Inspect the repository directory structure.
2. Read the main SKILL.md and README.
3. Inspect all 14 agent definitions.
4. Inspect engine, parser, graph, intelligence, refactoring, verification, and reporting modules.
5. Inspect framework configurations.
6. Inspect workflows and scripts.
7. Inspect storage and memory implementation.
8. Inspect tests.
9. Identify which capabilities are implemented, partial, planned, or absent.

Do not document proposed architecture as implemented architecture.

## REQUIRED DOCUMENT STRUCTURE

### 1. System Overview
Explain:
- What Root-Cause Architect does.
- Its engineering philosophy.
- The relationship between AI reasoning and deterministic tooling.
- Local-first architecture.
- Evidence-driven engineering.

### 2. High-Level Architecture
Document the actual architecture layers:
- Agent intelligence layer.
- Orchestration layer.
- Repository intelligence layer.
- Parsing and semantic analysis.
- Dependency graph.
- Data-flow analysis.
- Root-cause investigation.
- Duplication and dead-code analysis.
- Refactoring and implementation.
- Verification.
- Reporting.
- Memory.

Show component relationships using Mermaid.

### 3. Agent Architecture
Document all 14 agents:
- Responsibilities.
- Inputs.
- Outputs.
- Dependencies.
- Execution order.
- Collaboration model.
- Approval boundaries.

Explain which agents are actually executable through platform integration and which are instruction files only.

### 4. Repository Intelligence Engine
Explain:
- File discovery.
- Exclusion rules.
- Language detection.
- Framework detection.
- Symbol extraction.
- Parser architecture.
- Semantic resolution.
- Error handling.

### 5. Architecture Knowledge Graph
Document:
- Node types.
- Relationship types.
- Graph construction.
- Evidence metadata.
- Static versus runtime relationships.
- Confidence.
- Reachability.
- Graph refresh and invalidation.

### 6. Data-Flow and Execution Analysis
Explain:
- Source-to-sink tracing.
- API flows.
- Database reads and writes.
- Events.
- Background jobs.
- External integrations.
- Runtime instrumentation, if implemented.

### 7. Root-Cause and Duplication Intelligence
Explain how the system identifies:
- Root causes.
- Contributing conditions.
- Duplicate business logic.
- Dead code candidates.
- Competing implementations.
- Safe deletion candidates.

### 8. Refactoring and Safety
Explain:
- Unified solution design.
- Delete-first strategy.
- Contract preservation.
- Blast-radius analysis.
- Safety levels L0–L3.
- Human approval requirements.

### 9. Verification Architecture
Explain:
- Test selection.
- Regression verification.
- Security review.
- Performance review.
- Adversarial review.
- Evidence reporting.

### 10. Persistent Memory
Document SQLite storage, repository fingerprints, Git commit association, invalidation, and confidence only where implemented.

### 11. Execution Lifecycle
Include a complete Mermaid sequence diagram from user request through final report.

### 12. Architectural Decisions
Document important decisions, alternatives, trade-offs, and limitations.

## QUALITY REQUIREMENTS

- Include real module paths.
- Explain real interfaces.
- Use accurate Mermaid diagrams.
- Avoid generic marketing language.
- Distinguish current implementation from intended architecture.
- Never fabricate module names or execution capabilities.

Write the complete document and verify every referenced path exists.