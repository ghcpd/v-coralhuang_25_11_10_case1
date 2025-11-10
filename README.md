Flask SearchableMixin event binding fix

Problem
-------
The original code registered SQLAlchemy session event listeners bound to a concrete model (e.g. Post.before_commit). That approach assumes only that model will use SearchableMixin. When later models inherit SearchableMixin (for example, Comment), they were not handled because no listeners were registered for them.

Fix
---
This repository centralizes event registration on the Session class via SearchableMixin.register_listeners(db). The listeners collect all changes for objects that are instances of SearchableMixin using isinstance(obj, SearchableMixin), so no model-specific registration is required.

How to use
----------
Call SearchableMixin.register_listeners(db) once during your app initialization (after db is bound to the app). This will install session-level before_commit/after_commit handlers.

Why this is better
------------------
- Avoids forgetting to register new models
- Works for all current and future subclasses of SearchableMixin
- Keeps indexing logic centralized and testable

Files added
-----------
- models.py: refactored mixin and a small InMemoryIndex for tests
- test_search_events.py: pytest tests validating behavior across Post, Comment, and a non-searchable model
- requirements.txt, README.md, Dockerfile, setup.sh, run_test.sh, run_test.bat: helpers for running tests and building the project
- output.json: produced by the test run step (if tests are executed)

Notes
-----
The in-memory index is a tiny deterministic stand-in for a real search index. In production, replace SearchableMixin.index with an actual search client and adapt add/remove/search methods accordingly.