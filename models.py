from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import event


# Application db instance
db = SQLAlchemy()


class SearchableMixin(object):
    # Simple in-memory index used for testing.
    # Keys: (tablename, id) -> True. Use class methods to interact with it.
    _index = {}

    @staticmethod
    def _is_searchable(obj):
        # Detect whether object is a subclass of SearchableMixin (covers Post, Comment, etc.)
        return isinstance(obj, SearchableMixin)

    @staticmethod
    def before_commit(session):
        # Collect only objects that are instances of SearchableMixin
        session._changes = {
            'add': [obj for obj in session.new if SearchableMixin._is_searchable(obj)],
            'update': [obj for obj in session.dirty if SearchableMixin._is_searchable(obj)],
            'delete': [obj for obj in session.deleted if SearchableMixin._is_searchable(obj)],
        }

    @staticmethod
    def after_commit(session):
        changes = getattr(session, '_changes', None)
        if not changes:
            return
        # Apply operations across all searchable models
        for obj in changes['add']:
            SearchableMixin.add_to_index(obj)
        for obj in changes['update']:
            SearchableMixin.add_to_index(obj)
        for obj in changes['delete']:
            SearchableMixin.remove_from_index(obj)
        session._changes = None

    @staticmethod
    def add_to_index(obj):
        # Create a simple in-memory index keyed by (tablename, id) for tests
        if obj is None:
            return
        key = (getattr(obj, '__tablename__', obj.__class__.__name__), getattr(obj, 'id', None))
        SearchableMixin._index[key] = True

    @staticmethod
    def remove_from_index(obj):
        key = (getattr(obj, '__tablename__', obj.__class__.__name__), getattr(obj, 'id', None))
        if key in SearchableMixin._index:
            del SearchableMixin._index[key]

    @classmethod
    def reset_index(cls):
        cls._index = {}

    @classmethod
    def register_listeners(cls, db):
        """
        Register SQLAlchemy session-level listeners once for all searchable models.

        This binds before_commit/after_commit to the session class, and listeners
        will look for instances of SearchableMixin using isinstance checks.
        """
        session_class = db.session.__class__
        # Avoid double-listening
        if getattr(session_class, '_searchable_listeners_installed', False):
            return
        event.listen(session_class, 'before_commit', SearchableMixin.before_commit)
        event.listen(session_class, 'after_commit', SearchableMixin.after_commit)
        setattr(session_class, '_searchable_listeners_installed', True)


class Post(SearchableMixin, db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Comment(SearchableMixin, db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
