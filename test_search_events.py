import os
import tempfile
import pytest
from flask import Flask

from models import db, Post, Comment, User, SearchableMixin


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Register listeners once at initialization (generalized)
    SearchableMixin.register_listeners(db)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        # Drop tables to clean up
        db.drop_all()


@pytest.fixture(autouse=True)
def reset_index_ops():
    SearchableMixin.reset_index_ops()
    yield
    SearchableMixin.reset_index_ops()


def test_post_is_tracked(app):
    p = Post(body="hello")
    db.session.add(p)
    db.session.commit()

    ops = SearchableMixin.get_index_ops()
    assert ("add", "Post", p.id) in ops


def test_comment_is_tracked(app):
    c = Comment(body="world")
    db.session.add(c)
    db.session.commit()

    ops = SearchableMixin.get_index_ops()
    assert ("add", "Comment", c.id) in ops


def test_non_searchable_not_tracked(app):
    u = User(username="alice")
    db.session.add(u)
    db.session.commit()

    ops = SearchableMixin.get_index_ops()
    assert ops == []


def test_update_and_delete_behavior(app):
    p = Post(body="first")
    db.session.add(p)
    db.session.commit()
    SearchableMixin.reset_index_ops()

    # Update
    p.body = "updated"
    db.session.add(p)
    db.session.commit()
    ops = SearchableMixin.get_index_ops()
    assert ("add", "Post", p.id) in ops
    SearchableMixin.reset_index_ops()

    # Delete
    db.session.delete(p)
    db.session.commit()
    ops = SearchableMixin.get_index_ops()
    assert ("remove", "Post", p.id) in ops
