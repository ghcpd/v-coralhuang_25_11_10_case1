import os
import pytest
from flask import Flask
from models import db, Post, Comment, Other, SearchableMixin


@pytest.fixture
def app(tmp_path, monkeypatch):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        # register searchable listeners once
        SearchableMixin.register_listeners(db)
        yield app


@pytest.fixture
def session(app):
    # use the db.session from Flask-SQLAlchemy
    return db.session


def test_post_is_tracked(app, session):
    p = Post(body="hello")
    session.add(p)
    session.commit()

    ids, total = SearchableMixin.index.search('Post')
    assert total == 1
    assert ids == [1]


def test_comment_is_tracked(app, session):
    c = Comment(body="world")
    session.add(c)
    session.commit()

    ids, total = SearchableMixin.index.search('Comment')
    assert total == 1
    assert ids == [1]


def test_non_searchable_ignored(app, session):
    before_ids, before_total = SearchableMixin.index.search('Other')
    o = Other(name='noindex')
    session.add(o)
    session.commit()

    after_ids, after_total = SearchableMixin.index.search('Other')
    # Other is not SearchableMixin; index should be unchanged
    assert before_total == after_total == 0
    assert before_ids == after_ids == []
