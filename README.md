# SearchableMixin: Centralized event listener registration

This repository demonstrates a `SearchableMixin` for Flask + SQLAlchemy which keeps a search index in sync with model changes.

Problem solved
- Original code bound session events only to a single model (e.g., `Post.before_commit`), so any other model inheriting `SearchableMixin` (e.g., `Comment`) didn't trigger indexing.
- This refactor registers session-level listeners once and uses `isinstance(obj, SearchableMixin)` to select the relevant objects.

How it works
- Call `SearchableMixin.register_listeners(db)` once during app initialization (for example, in your factory method).
- The mixin registers `before_commit`, `after_commit`, and `after_rollback` on the session class so the handlers apply across all models and sessions.

Why this pattern
- Event binding on a specific model is fragile because it's easy to forget to bind new models.
- Using session-level listeners with `isinstance` ensures all mixin users are handled automatically, reducing mistakes.

Testing
- Tests are included in `test_search_events.py`.
- They verify Post and Comment are indexed when created/updated/deleted and that a non-searchable model (`User`) does not trigger index ops.

Running the tests
- Linux/macOS: run `./run_test.sh`.
- Windows: run `.
un_test.bat` in PowerShell.

Deployment
- A `Dockerfile` is included for creating a reproducible environment and running tests inside a container.
