from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import event

db = SQLAlchemy()

class SearchableMixin(object):
    """
    Mixin to handle search index synchronization with database models.
    
    Usage:
        class Post(SearchableMixin, db.Model):
            __tablename__ = 'post'
            id = db.Column(db.Integer, primary_key=True)
            body = db.Column(db.String(255))
        
        class Comment(SearchableMixin, db.Model):
            __tablename__ = 'comment'
            id = db.Column(db.Integer, primary_key=True)
            body = db.Column(db.String(255))
        
        # Register listeners once during app initialization
        SearchableMixin.register_listeners(db)
    """
    
    @classmethod
    def before_commit(cls, session):
        """
        Collect changes for all SearchableMixin subclasses before commit.
        This is a session-level handler that runs once per session.
        """
        # Initialize tracking (always reset for each commit)
        session._changes = {
            'add': [],
            'update': [],
            'delete': [],
        }
        
        # Collect changes for ALL SearchableMixin subclasses
        for obj in session.new:
            if isinstance(obj, SearchableMixin):
                session._changes['add'].append(obj)
        
        for obj in session.dirty:
            if isinstance(obj, SearchableMixin):
                session._changes['update'].append(obj)
        
        for obj in session.deleted:
            if isinstance(obj, SearchableMixin):
                session._changes['delete'].append(obj)

    @classmethod
    def after_commit(cls, session):
        """
        Process index changes for all SearchableMixin subclasses after commit.
        Uses the object's actual class to call the appropriate methods.
        """
        changes = getattr(session, '_changes', None)
        if not changes:
            return
        
        # Process adds - using obj's own class for polymorphic support
        for obj in changes['add']:
            obj.__class__.add_to_index(obj)
        
        # Process updates - using obj's own class
        for obj in changes['update']:
            obj.__class__.add_to_index(obj)
        
        # Process deletes - using obj's own class
        for obj in changes['delete']:
            obj.__class__.remove_from_index(obj)
        
        session._changes = None

    @staticmethod
    def add_to_index(obj):
        """
        Add object to search index.
        Override in subclass to implement actual indexing logic.
        """
        print(f"[INDEX] Adding {obj.__class__.__name__}(id={getattr(obj, 'id', 'N/A')}) to index")

    @staticmethod
    def remove_from_index(obj):
        """
        Remove object from search index.
        Override in subclass to implement actual de-indexing logic.
        """
        print(f"[INDEX] Removing {obj.__class__.__name__}(id={getattr(obj, 'id', 'N/A')}) from index")

    @classmethod
    def register_listeners(cls, db_instance):
        """
        Register session-level event listeners for SearchableMixin.
        
        This method should be called once during application initialization.
        It attaches listeners at the session class level, allowing them to
        process changes for all SearchableMixin subclasses automatically.
        
        Args:
            db_instance: The SQLAlchemy instance (e.g., db = SQLAlchemy())
        
        Example:
            app = Flask(__name__)
            db = SQLAlchemy(app)
            
            class Post(SearchableMixin, db.Model):
                ...
            
            class Comment(SearchableMixin, db.Model):
                ...
            
            SearchableMixin.register_listeners(db)
        """
        # Register at the session class level, not at model level
        # This ensures the handlers run for all models in the session
        event.listen(db_instance.session.__class__, 'before_commit', cls.before_commit)
        event.listen(db_instance.session.__class__, 'after_commit', cls.after_commit)


class Post(SearchableMixin, db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Post id={self.id} body='{self.body}'>"


class Comment(SearchableMixin, db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Comment id={self.id} body='{self.body}'>"
