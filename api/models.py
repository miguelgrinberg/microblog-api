from datetime import datetime
from hashlib import md5
import secrets
from time import time

from flask import current_app, url_for, abort
import jwt
import sqlalchemy as sqla
from sqlalchemy import orm as sqla_orm
from werkzeug.security import generate_password_hash, check_password_hash

from api.app import db


class Updateable:
    def update(self, data):
        for attr, value in data.items():
            setattr(self, attr, value)


followers = sqla.Table(
    'followers',
    db.Model.metadata,
    sqla.Column('follower_id', sqla.Integer, sqla.ForeignKey('users.id')),
    sqla.Column('followed_id', sqla.Integer, sqla.ForeignKey('users.id'))
)


class User(Updateable, db.Model):
    __tablename__ = 'users'

    id = sqla.Column(sqla.Integer, primary_key=True)
    username = sqla.Column(sqla.String(64), index=True, unique=True,
                           nullable=False)
    email = sqla.Column(sqla.String(120), index=True, unique=True,
                        nullable=False)
    password_hash = sqla.Column(sqla.String(128))
    about_me = sqla.Column(sqla.String(140))
    first_seen = sqla.Column(sqla.DateTime, default=datetime.utcnow)
    last_seen = sqla.Column(sqla.DateTime, default=datetime.utcnow)

    posts = sqla_orm.relationship('Post', back_populates='author',
                                  lazy='noload')
    following = sqla_orm.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers', lazy='noload')
    followers = sqla_orm.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following', lazy='noload')

    def posts_select(self):
        return Post.select().where(sqla_orm.with_parent(self, User.posts))

    def following_select(self):
        return User.select().where(sqla_orm.with_parent(self, User.following))

    def followers_select(self):
        return User.select().where(sqla_orm.with_parent(self, User.followers))

    def followed_posts_select(self):
        return Post.select().join(
            followers, (followers.c.followed_id == Post.user_id)).where(
                followers.c.follower_id == self.id).union(
                    self.posts_select())

    def __repr__(self):  # pragma: no cover
        return '<User {}>'.format(self.username)

    @property
    def url(self):
        return url_for('users.get', id=self.id)

    @property
    def avatar_url(self):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon'

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def ping(self):
        self.last_seen = datetime.utcnow()

    @staticmethod
    def _generate_jwt(token_type, expiration, **kwargs):
        return jwt.encode(
            {
                'type': token_type,
                'exp': time() + expiration,
                **kwargs
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def _verify_jwt(token_type, token):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'],
                              algorithms=['HS256'])
        except jwt.PyJWTError:
            return
        if data.get('type') != token_type:
            return
        return data

    def generate_tokens(self, fresh=False):
        secret = secrets.token_urlsafe()
        access_token = self._generate_jwt(
            'access', current_app.config['ACCESS_TOKEN_EXPIRATION'],
            user_id=self.id, fresh=fresh, secret=secret)
        refresh_token = self._generate_jwt(
            'refresh', current_app.config['REFRESH_TOKEN_EXPIRATION'],
            user_id=self.id, secret=secret)
        return access_token, refresh_token

    @staticmethod
    def check_access_token(access_token):
        data = User._verify_jwt('access', access_token)
        if data:
            user_id = data.pop('user_id')
            user = db.session.get(User, user_id)
            if user:  # pragma: no branch
                user.ping()
                db.session.commit()
                return {'user': user, **data}

    @staticmethod
    def check_refresh_token(refresh_token, access_token):
        refresh_data = User._verify_jwt('refresh', refresh_token) or {}
        refresh_user_id = refresh_data.pop('user_id', None)
        refresh_secret = refresh_data.pop('secret', None)
        access_data = User._verify_jwt('access', access_token) or {}
        access_user_id = access_data.pop('user_id', None)
        access_secret = access_data.pop('secret', None)
        if refresh_user_id != access_user_id or \
                refresh_secret != access_secret:
            return
        return {'user': db.session.get(User, refresh_user_id),
                **refresh_data}

    def generate_reset_token(self):
        return self._generate_jwt(
            'reset', current_app.config['RESET_TOKEN_EXPIRATION'],
            email=self.email)

    @staticmethod
    def check_reset_token(reset_token):
        reset_data = User._verify_jwt('reset', reset_token)
        return db.session.scalar(User.select().filter_by(
            email=reset_data['email'])) or abort(400)

    def follow(self, user):
        if not self.is_following(user):
            db.session.execute(followers.insert().values(
                follower_id=self.id, followed_id=user.id))

    def unfollow(self, user):
        if self.is_following(user):
            db.session.execute(followers.delete().where(
                followers.c.follower_id == self.id,
                followers.c.followed_id == user.id))

    def is_following(self, user):
        return db.session.scalars(User.select().where(
            User.id == self.id, User.following.contains(
                user))).one_or_none() is not None


class Post(Updateable, db.Model):
    __tablename__ = 'posts'

    id = sqla.Column(sqla.Integer, primary_key=True)
    body = sqla.Column(sqla.String(280), nullable=False)
    timestamp = sqla.Column(sqla.DateTime, index=True, default=datetime.utcnow,
                            nullable=False)
    user_id = sqla.Column(sqla.Integer, sqla.ForeignKey(User.id), index=True)

    author = sqla_orm.relationship('User', back_populates='posts')

    def __repr__(self):  # pragma: no cover
        return '<Post {}>'.format(self.body)

    @property
    def url(self):
        return url_for('posts.get', id=self.id)
