import os
import tempfile
import pytest
from flask import Flask
from models import db, Post, Comment, SearchableMixin


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'  # in-memory
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_post_and_comment_indexed(app):
    # Set up listeners and reset index
    SearchableMixin.reset_index()
    SearchableMixin.register_listeners(db)

    # Add a Post and a Comment; they should be indexed after commit
    p = Post(body='hello')
    c = Comment(body='world')
    db.session.add_all([p, c])
    db.session.commit()

    # After commit, both objects should have entries in the in-memory index
    # We expect keys to be (tablename, id)
    post_key = ('post', p.id)
    comment_key = ('comment', c.id)

    assert post_key in SearchableMixin._index
    assert comment_key in SearchableMixin._index


def test_non_searchable_is_ignored(app):
    # Create a non-searchable model on the fly
    class Tag(db.Model):
        __tablename__ = 'tag'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(64))

    db.create_all()
    SearchableMixin.reset_index()
    SearchableMixin.register_listeners(db)

    tag = Tag(name='untagged')
    db.session.add(tag)
    db.session.commit()

    tag_key = ('tag', tag.id)
    assert tag_key not in SearchableMixin._index


def test_index_update_and_delete(app):
    SearchableMixin.reset_index()
    SearchableMixin.register_listeners(db)

    p = Post(body='to update')
    db.session.add(p)
    db.session.commit()
    assert ('post', p.id) in SearchableMixin._index

    # Update object
    p.body = 'updated'
    db.session.add(p)
    db.session.commit()
    assert ('post', p.id) in SearchableMixin._index

    # Delete object
    db.session.delete(p)
    db.session.commit()
    assert ('post', p.id) not in SearchableMixin._index


def test_register_listeners_idempotent(app):
    # Registering listeners multiple times should be a no-op and not throw errors
    SearchableMixin.reset_index()
    SearchableMixin.register_listeners(db)
    SearchableMixin.register_listeners(db)  # second call -> should do nothing

    p = Post(body='idempotent')
    db.session.add(p)
    db.session.commit()

    assert ('post', p.id) in SearchableMixin._index
