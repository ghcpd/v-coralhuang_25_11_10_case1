import pytest
import sys
import os
from datetime import datetime
from unittest.mock import patch, call

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Post, Comment, SearchableMixin


@pytest.fixture
def app():
    """Create a Flask app with SQLite in-memory database for testing."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        # Register listeners after db initialization
        SearchableMixin.register_listeners(db)
        yield app
        db.session.remove()
        db.drop_all()


class TestPostIndexing:
    """Test that Post objects are properly indexed."""
    
    def test_post_add_is_indexed(self, app):
        """Verify that adding a Post triggers index add operation."""
        with app.app_context():
            with patch.object(Post, 'add_to_index') as mock_add:
                post = Post(body="Hello World")
                db.session.add(post)
                db.session.commit()
                
                # Verify add_to_index was called with the post object
                mock_add.assert_called()
                assert any(isinstance(arg, Post) for arg in mock_add.call_args[0])
    
    def test_post_update_is_indexed(self, app):
        """Verify that updating a Post triggers index update operation."""
        with app.app_context():
            post = Post(body="Original")
            db.session.add(post)
            db.session.commit()
            
            # Update the post
            with patch.object(Post, 'add_to_index') as mock_add:
                post.body = "Updated"
                db.session.commit()
                
                # Verify add_to_index was called for the update
                mock_add.assert_called()
    
    def test_post_delete_is_indexed(self, app):
        """Verify that deleting a Post triggers index delete operation."""
        with app.app_context():
            post = Post(body="To Delete")
            db.session.add(post)
            db.session.commit()
            
            # Delete the post
            with patch.object(Post, 'remove_from_index') as mock_remove:
                db.session.delete(post)
                db.session.commit()
                
                # Verify remove_from_index was called
                mock_remove.assert_called()
                assert any(isinstance(arg, Post) for arg in mock_remove.call_args[0])


class TestCommentIndexing:
    """Test that Comment objects are properly indexed."""
    
    def test_comment_add_is_indexed(self, app):
        """Verify that adding a Comment triggers index add operation."""
        with app.app_context():
            with patch.object(Comment, 'add_to_index') as mock_add:
                comment = Comment(body="Great post!")
                db.session.add(comment)
                db.session.commit()
                
                # Verify add_to_index was called
                mock_add.assert_called()
                assert any(isinstance(arg, Comment) for arg in mock_add.call_args[0])
    
    def test_comment_update_is_indexed(self, app):
        """Verify that updating a Comment triggers index update operation."""
        with app.app_context():
            comment = Comment(body="Original comment")
            db.session.add(comment)
            db.session.commit()
            
            # Update the comment
            with patch.object(Comment, 'add_to_index') as mock_add:
                comment.body = "Edited comment"
                db.session.commit()
                
                # Verify add_to_index was called
                mock_add.assert_called()
    
    def test_comment_delete_is_indexed(self, app):
        """Verify that deleting a Comment triggers index delete operation."""
        with app.app_context():
            comment = Comment(body="To delete")
            db.session.add(comment)
            db.session.commit()
            
            # Delete the comment
            with patch.object(Comment, 'remove_from_index') as mock_remove:
                db.session.delete(comment)
                db.session.commit()
                
                # Verify remove_from_index was called
                mock_remove.assert_called()


class TestMultiModelBehavior:
    """Test behavior with multiple SearchableMixin models in a single session."""
    
    def test_mixed_adds_indexed(self, app):
        """Verify that adding both Post and Comment in same transaction works."""
        with app.app_context():
            with patch.object(Post, 'add_to_index') as mock_post_add, \
                 patch.object(Comment, 'add_to_index') as mock_comment_add:
                
                post = Post(body="A post")
                comment = Comment(body="A comment")
                
                db.session.add(post)
                db.session.add(comment)
                db.session.commit()
                
                # Both should be indexed
                mock_post_add.assert_called()
                mock_comment_add.assert_called()
    
    def test_mixed_operations_indexed(self, app):
        """Verify mixed add/update/delete operations work correctly."""
        with app.app_context():
            # Create initial objects
            post = Post(body="Post 1")
            comment = Comment(body="Comment 1")
            db.session.add(post)
            db.session.add(comment)
            db.session.commit()
            
            # Perform mixed operations
            with patch.object(Post, 'add_to_index') as mock_post_add, \
                 patch.object(Comment, 'add_to_index') as mock_comment_add, \
                 patch.object(Comment, 'remove_from_index') as mock_comment_remove:
                
                post.body = "Post 1 Updated"
                db.session.delete(comment)
                new_comment = Comment(body="Comment 2")
                db.session.add(new_comment)
                db.session.commit()
                
                # All operations should be indexed
                mock_post_add.assert_called()  # update uses add_to_index
                mock_comment_remove.assert_called()  # delete
                mock_comment_add.assert_called()  # new add


class TestNonSearchableModels:
    """Test that non-searchable models don't interfere with indexing."""
    
    def test_non_searchable_model_ignored(self, app):
        """Create a non-SearchableMixin model and verify it doesn't cause errors."""
        with app.app_context():
            # Create a table that is NOT searchable
            class NonSearchable(db.Model):
                __tablename__ = 'non_searchable'
                id = db.Column(db.Integer, primary_key=True)
                name = db.Column(db.String(255))
            
            db.create_all()
            
            # Add searchable and non-searchable objects
            with patch.object(Post, 'add_to_index') as mock_add:
                post = Post(body="Test")
                non_searchable = NonSearchable(name="Test")
                
                db.session.add(post)
                db.session.add(non_searchable)
                
                # Should not raise an error
                db.session.commit()
                
                # Only Post should be indexed
                mock_add.assert_called_once()
                
                # Verify objects were created
                assert Post.query.count() == 1
                assert NonSearchable.query.count() == 1


class TestIndexState:
    """Test that index state is correctly maintained."""
    
    def test_changes_reset_after_commit(self, app):
        """Verify that session._changes is reset for each commit."""
        with app.app_context():
            post = Post(body="Test")
            db.session.add(post)
            db.session.commit()
            
            # After first commit, changes were processed
            # Now make a second commit - it should reinitialize _changes
            comment = Comment(body="Test comment")
            db.session.add(comment)
            db.session.commit()  # Should not error even though first commit set it to None
            
            # Second commit should also work
            assert Post.query.count() == 1
            assert Comment.query.count() == 1
    
    def test_no_indexing_on_rollback(self, app):
        """Verify that changes are not indexed on rollback."""
        with app.app_context():
            with patch.object(Post, 'add_to_index') as mock_add:
                post = Post(body="Will rollback")
                db.session.add(post)
                db.session.rollback()
                
                # Object should not be in database and not indexed
                assert Post.query.count() == 0
                mock_add.assert_not_called()
    
    def test_multiple_commits_independent(self, app):
        """Verify that multiple commits are processed independently."""
        with app.app_context():
            # First commit
            with patch.object(Post, 'add_to_index') as mock_post_add:
                post1 = Post(body="Post 1")
                db.session.add(post1)
                db.session.commit()
                mock_post_add.assert_called_once()
            
            # Second commit - should work without errors
            with patch.object(Comment, 'add_to_index') as mock_comment_add:
                comment1 = Comment(body="Comment 1")
                db.session.add(comment1)
                db.session.commit()
                mock_comment_add.assert_called_once()


class TestPolymorphicDispatch:
    """Test that polymorphic method dispatch works correctly."""
    
    def test_correct_class_method_called(self, app):
        """Verify that the correct class's method is called, not a hardcoded one."""
        with app.app_context():
            with patch.object(Post, 'add_to_index') as mock_post_add, \
                 patch.object(Comment, 'add_to_index') as mock_comment_add:
                
                post = Post(body="Test post")
                comment = Comment(body="Test comment")
                
                db.session.add(post)
                db.session.add(comment)
                db.session.commit()
                
                # Verify each class's method was called
                mock_post_add.assert_called_once()
                mock_comment_add.assert_called_once()
                
                # Verify they were called with the correct types
                post_arg = mock_post_add.call_args[0][0]
                comment_arg = mock_comment_add.call_args[0][0]
                
                assert isinstance(post_arg, Post)
                assert isinstance(comment_arg, Comment)
                assert post_arg.__class__ == Post
                assert comment_arg.__class__ == Comment


class TestRegressionIssues:
    """Test that the original bugs from the issue are fixed."""
    
    def test_comment_is_tracked_bug_fix(self, app):
        """
        Original bug: Comment changes not tracked even though it inherits SearchableMixin.
        This test verifies the fix.
        """
        with app.app_context():
            # The original test case from the issue
            with patch.object(Comment, 'add_to_index') as mock_add:
                c = Comment(body="world")
                db.session.add(c)
                # BUG WAS: no event listener was registered for Comment, so index will not be updated
                # FIX: Now it should be indexed
                db.session.commit()
                
                # Now Comment should be indexed
                mock_add.assert_called_once()
    
    def test_post_still_works_after_fix(self, app):
        """
        Verify that Post (the original working model) still works after the fix.
        """
        with app.app_context():
            with patch.object(Post, 'add_to_index') as mock_add:
                p = Post(body="hello")
                db.session.add(p)
                db.session.commit()
                
                # Post should still be indexed
                mock_add.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
