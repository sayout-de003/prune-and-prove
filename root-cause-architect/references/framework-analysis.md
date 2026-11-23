# Framework Analysis Guide

Governed by `config/frameworks.yaml`:
- Require at least `minimum_evidence: 2` independent signals AND framework-specific dependency or config evidence.
- Generic ecosystem manifests (`package.json`, `pyproject.toml`, `Cargo.toml`) alone never prove a specific framework.
- Check framework-specific hidden call paths before deleting code:
  - **Django:** `urls.py`, signals (`@receiver`), `admin.py`, middleware, Celery tasks, management commands.
  - **FastAPI / Flask:** `@app.get/post`, `Depends(...)`, blueprints, lifespan hooks.
  - **React / Next.js:** File-system routes (`app/**/page.tsx`), server actions, contexts, hooks.
  - **Express / NestJS:** Middleware, `router.*`, `@Controller` / `@Injectable` DI containers.
