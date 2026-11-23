# Root-Cause Methodology

Separate every failure into seven distinct layers:
1. **Symptom** — What the user or monitor observes.
2. **Trigger** — The input, event, or timing that initiates the failure.
3. **Immediate Failure** — The exact line/exception where execution breaks.
4. **Earliest Invalid State** — The first place data or state violates an invariant.
5. **Underlying Defect** — The flawed logic, missing validation, or wrong assumption causing that invalid state.
6. **Architectural Weakness** — Structural issue (e.g., split source of truth, missing transaction boundary) that enabled the defect.
7. **Contributing Defects** — Secondary issues (e.g., swallowed errors, stale caches) that amplified the impact.

Never stop at layer 3 when layer 4–5 is upstream.
