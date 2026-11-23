# Engineering Principles

1. **Understand before editing:** Never propose or apply a fix before mapping the relevant code, callers, and contracts.
2. **Source-of-truth first:** Correct invalid state where it originates rather than papering over it downstream.
3. **One coherent design:** Consolidate duplicate or contradictory rules instead of layering parallel branches.
4. **Evidence over intuition:** Label every diagnosis `PROVEN`, `STRONGLY SUPPORTED`, `HYPOTHESIS`, or `UNKNOWN`.
5. **Conservative deletion:** Prove both static and dynamic safety before removing code; never delete for line-count vanity.
6. **Verify actual behavior:** Report exact commands, actual outcomes, and unexecuted layers honestly.
