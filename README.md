# Flask SearchableMixin — fix for session-level event registration

Reason for change
- Listeners were previously bound to a single model (e.g., `Post`) which made the code fragile and required developers to remember to register each new `SearchableMixin` subclass.
- This PR generalizes session-level event registration so all models that inherit `SearchableMixin` are tracked automatically.

What changed
- `SearchableMixin.register_listeners(db)` — register session-level listeners once for the SQLAlchemy session class.
- `before_commit`/`after_commit` now look for `isinstance(obj, SearchableMixin)` instead of assuming a specific model.
- Simple in-memory index for tests (`SearchableMixin._index`) with `reset_index()` for safe test runs.

How to use
- Call `SearchableMixin.register_listeners(db)` during your app initialization (e.g., in app factory) after calling `db.init_app(app)`.
- The event listeners will be installed once and will handle all subclasses of `SearchableMixin`.

Why this is safer
- No need to manually register each model. If any model chooses to inherit `SearchableMixin`, it will be handled automatically.

Testing
- Use pytest: `pytest -q` or use the run scripts in this repository. Tests ensure both `Post` and `Comment` updates are indexed and a non-searchable model is not indexed.

