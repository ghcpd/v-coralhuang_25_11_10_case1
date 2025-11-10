from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import event
from typing import Tuple, List

db = SQLAlchemy()


class InMemoryIndex:
    """A tiny in-memory index to make tests deterministic.

    Contract: index methods return consistent types: (list_of_ids, total)
    """

    def __init__(self):
        self._docs = {}

    def add(self, obj):
        self._docs[(obj.__class__.__name__, obj.id)] = obj

    def remove(self, obj):
        self._docs.pop((obj.__class__.__name__, obj.id), None)

    def search(self, cls_name: str) -> Tuple[List[int], int]:
        ids = [k[1] for k in self._docs.keys() if k[0] == cls_name]
        return ids, len(ids)


class SearchableMixin(object):
    # shared in-memory index for tests; in real usage, replace with real index client
    index = InMemoryIndex()

    @classmethod
    def _collect_changes(cls, session):
        # collect changes for all objects that are instances of SearchableMixin
        return {
            'add': [obj for obj in session.new if isinstance(obj, SearchableMixin)],
            'update': [obj for obj in session.dirty if isinstance(obj, SearchableMixin)],
            'delete': [obj for obj in session.deleted if isinstance(obj, SearchableMixin)],
        }

    @classmethod
    def _after_commit(cls, session):
        changes = getattr(session, '_changes', None)
        if not changes:
            return
        # operate on instances regardless of their concrete model class
        for obj in changes['add']:
            cls.add_to_index(obj)
        for obj in changes['update']:
            cls.add_to_index(obj)
        for obj in changes['delete']:
            cls.remove_from_index(obj)
        session._changes = None

    @staticmethod
    def add_to_index(obj):
        SearchableMixin.index.add(obj)

    @staticmethod
    def remove_from_index(obj):
        SearchableMixin.index.remove(obj)

    @classmethod
    def register_listeners(cls, db_instance):
        """Register session-level listeners once. Call during app initialization.

        This binds to the Session class so that any session will trigger handlers.
        It collects only objects that are instances of SearchableMixin, not by concrete model.
        """

        session_cls = db_instance.session.__class__

        # bind only once - guard against double registration
        if getattr(session_cls, '_searchable_listeners_installed', False):
            return

        def before_commit(session):
            session._changes = cls._collect_changes(session)

        def after_commit(session):
            cls._after_commit(session)

        event.listen(session_cls, 'before_commit', before_commit)
        event.listen(session_cls, 'after_commit', after_commit)
        setattr(session_cls, '_searchable_listeners_installed', True)


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


# Example of a non-searchable model to ensure listeners ignore it
class Other(db.Model):
    __tablename__ = 'other'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
