# Workflow: Database Change (Mode D — Risk Level 3)

**When to use:** Schema changes, migrations, indexes, constraints, or persistence-layer refactors.

## Steps
1. **Require Explicit Approval:** Risk Level 3 per `config/safety.yaml`. Never run destructive DB commands or rewrite migration history silently.
2. **Map Persistence Consumers:** Find all models, queries, serializers, background jobs, and migrations touching the affected tables/fields.
3. **Design Safe Migration:** Prefer backward-compatible expand/contract migrations when live traffic or rollbacks matter; define an explicit rollback plan.
4. **Apply in Isolated Environment:** Test forward migration, application behavior, and rollback against a non-production database.
5. **Verify:** Run database, integration, and contract tests; document exact migration files and any manual deployment steps.
