from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import Session

# Keep a lightweight in-memory index to validate behavior in tests. In real code,
# this can be replaced by an actual search client (e.g. Elasticsearch wrapper).
_INDEX_OPERATIONS = []

def _index_add(obj):
    _INDEX_OPERATIONS.append(("add", obj.__class__.__name__, getattr(obj, 'id', None)))


def _index_remove(obj):
    _INDEX_OPERATIONS.append(("remove", obj.__class__.__name__, getattr(obj, 'id', None)))


class SQLAlchemyWithEvents(SQLAlchemy):
    """Custom SQLAlchemy subclass allowing access to session class for event registration.
    This is a small helper so we can register listeners on the correct session type.
    Use SQLAlchemyWithEvents(...) instead of SQLAlchemy() when creating `db`.
    """
    pass


db = SQLAlchemyWithEvents()


class SearchableMixin(object):
    """Mixin that adds db session event listeners for keeping a search index up-to-date.

    Use SearchableMixin.register_listeners(db) once at app initialization so all
    subclasses are covered. Event handlers are registered on the session class so
    they apply to all models; handlers use isinstance checks to find which objects
    are SearchableMixin instances.

    Contract: add_to_index(obj) and remove_from_index(obj) are responsible for
    updating the search index. For tests we've added minimal in-memory helpers.
    """

    @classmethod
    def register_listeners(cls, db_instance):
        """Register session-level event listeners to process all SearchableMixin subclasses.

        This should be called once at application start-up, e.g. in the factory function.
        """
        target_session_cls = db_instance.session.__class__

        # Avoid re-registering multiple times when called repeatedly
        if getattr(target_session_cls, "_searchable_listeners_registered", False):
            return

        event.listen(target_session_cls, "before_commit", cls._before_commit)
        event.listen(target_session_cls, "after_commit", cls._after_commit)
        event.listen(target_session_cls, "after_rollback", cls._after_rollback)
        target_session_cls._searchable_listeners_registered = True

    @staticmethod
    def _before_commit(session: Session):
        """Collect changes across all models and stash them on the session.
        Only store objects that are instances of SearchableMixin.
        """
        session._searchable_changes = {
            "add": [obj for obj in session.new if isinstance(obj, SearchableMixin)],
            "update": [obj for obj in session.dirty if isinstance(obj, SearchableMixin)],
            "delete": [obj for obj in session.deleted if isinstance(obj, SearchableMixin)],
        }

    @staticmethod
    def _after_commit(session: Session):
        """Apply index changes for all SearchableMixin objects and clear changes.
        """
        changes = getattr(session, "_searchable_changes", None)
        if not changes:
            return

        for obj in changes["add"]:
            SearchableMixin.add_to_index(obj)
        for obj in changes["update"]:
            SearchableMixin.add_to_index(obj)
        for obj in changes["delete"]:
            SearchableMixin.remove_from_index(obj)

        session._searchable_changes = None

    @staticmethod
    def _after_rollback(session: Session):
        # clear any pending changes on rollback
        if hasattr(session, "_searchable_changes"):
            session._searchable_changes = None

    @staticmethod
    def add_to_index(obj):
        # In production this would push to an external index; here we record ops
        _index_add(obj)

    @staticmethod
    def remove_from_index(obj):
        _index_remove(obj)

    @staticmethod
    def reset_index_ops():
        _INDEX_OPERATIONS.clear()

    @staticmethod
    def get_index_ops():
        return list(_INDEX_OPERATIONS)


class Post(SearchableMixin, db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(SearchableMixin, db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Non-searchable model to assert it doesn't affect the index
class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
