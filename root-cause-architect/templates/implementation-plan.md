# Unified Implementation Plan

- **Mode:** `Mode A | Mode B | Mode D`
- **Risk Level:** `Level 1 | Level 2 (Review Required) | Level 3 (Explicit Approval)`
- **Source of Truth:** `<module::symbol>`

## 1. Contracts to Preserve
-

## 2. Ordered Changes (Delete-First)
1. **Delete:** (approved `SAFE` superseded logic)
2. **Consolidate:** (duplicate rules merged into source of truth)
3. **Modify:** (root-cause fix + caller updates)
4. **Tests:** (add regression tests, update/remove obsolete tests)

## 3. Migration & Rollback Plan
- Migration required: `Yes / No`
- Rollback steps:

## 4. Verification Plan
- Exact commands and layers to run:
