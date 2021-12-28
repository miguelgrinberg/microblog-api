from flask import Blueprint, abort
from apifairy import authenticate, body, response, other_responses

from api import db
from api.models import User, Post
from api.schemas import PostSchema
from api.auth import token_auth
from api.decorators import paginated_response
from api.schemas import DateTimePaginationSchema

posts = Blueprint('posts', __name__)
post_schema = PostSchema()
posts_schema = PostSchema(many=True)
update_post_schema = PostSchema(partial=True)


@posts.route('/posts', methods=['POST'])
@authenticate(token_auth)
@body(post_schema)
@response(post_schema, 201)
def new(args):
    """Create a new post"""
    user = token_auth.current_user()
    post = Post(author=user, **args)
    db.session.add(post)
    db.session.commit()
    return post


@posts.route('/posts/<int:id>', methods=['GET'])
@authenticate(token_auth)
@response(post_schema)
@other_responses({404: 'Post not found'})
def get(id):
    """Retrieve a post by id"""
    return db.session.get(Post, id) or abort(404)


@posts.route('/posts', methods=['GET'])
@authenticate(token_auth)
@paginated_response(posts_schema, order_by=Post.timestamp,
                    order_direction='desc',
                    pagination_schema=DateTimePaginationSchema)
def all():
    """Retrieve all posts"""
    return Post.select()


@posts.route('/users/<int:id>/posts', methods=['GET'])
@authenticate(token_auth)
@paginated_response(posts_schema, order_by=Post.timestamp,
                    order_direction='desc',
                    pagination_schema=DateTimePaginationSchema)
@other_responses({404: 'User not found'})
def user_all(id):
    """Retrieve all posts from a user"""
    user = db.session.get(User, id) or abort(404)
    return user.posts_select()


@posts.route('/posts/<int:id>', methods=['PUT'])
@authenticate(token_auth)
@body(update_post_schema)
@response(post_schema)
@other_responses({403: 'Not allowed to edit this post',
                  404: 'Post not found'})
def put(data, id):
    """Edit a post"""
    post = db.session.get(Post, id) or abort(404)
    if post.author != token_auth.current_user():
        abort(403)
    post.update(data)
    db.session.commit()
    return post


@posts.route('/posts/<int:id>', methods=['DELETE'])
@authenticate(token_auth)
@other_responses({403: 'Not allowed to delete the post'})
def delete(id):
    """Delete a post"""
    post = db.session.get(Post, id) or abort(404)
    if post.author != token_auth.current_user():
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return '', 204


@posts.route('/feed', methods=['GET'])
@authenticate(token_auth)
@paginated_response(posts_schema, order_by=Post.timestamp,
                    order_direction='desc',
                    pagination_schema=DateTimePaginationSchema)
def feed():
    """Retrieve the user's post feed"""
    user = token_auth.current_user()
    return user.followed_posts_select()
