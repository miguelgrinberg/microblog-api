from datetime import timedelta
import sqlalchemy as sa
import pytest
from api.app import db
from api.dates import naive_utcnow
from api.models import User, Post
from tests.base_test_case import BaseTestCase


class UserModelTests(BaseTestCase):
    def test_password_hashing(self):
        u = User(username='susan', password='cat')
        assert not u.verify_password('dog')
        assert u.verify_password('cat')
        with pytest.raises(AttributeError):
            u.password

    def test_url(self):
        u = User(username='john', email='john@example.com')
        db.session.add(u)
        db.session.commit()
        assert u.url == 'http://localhost:5000/api/users/' + str(u.id)

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        assert u.avatar_url == ('https://www.gravatar.com/avatar/'
                                'd4c74594d841139328695756648b6bd6'
                                '?d=identicon')

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add_all([u1, u2])
        db.session.commit()
        assert db.session.scalars(u1.following.select()).all() == []
        assert db.session.scalars(u1.followers.select()).all() == []

        for _ in range(2):
            u1.follow(u2)
            db.session.commit()
            assert u1.is_following(u2)
            assert not u1.is_following(u1)
            assert not u2.is_following(u1)
            assert db.session.scalar(sa.select(sa.func.count()).select_from(
                u1.following.select().subquery())) == 1
            assert db.session.scalar(u1.following.select()).username == 'susan'
            assert db.session.scalar(sa.select(sa.func.count()).select_from(
                u2.followers.select().subquery())) == 1
            assert db.session.scalar(u2.followers.select()).username == 'john'

        for _ in range(2):
            u1.unfollow(u2)
            db.session.commit()
            assert not u1.is_following(u2)
            assert db.session.scalar(sa.select(sa.func.count()).select_from(
                u1.following.select().subquery())) == 0
            assert db.session.scalar(sa.select(sa.func.count()).select_from(
                u2.followers.select().subquery())) == 0

    def test_get_users(self):
        rv = self.client.post('/api/users', json={
            'username': 'john',
            'email': 'john@example.com',
            'password': 'cat',
        })

        rv = self.client.get('/api/users')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 2
        assert rv.json['data'][1]['username'] == 'john'
        assert rv.json['data'][1]['email'] == 'john@example.com'
        assert 'password' not in rv.json['data'][1]

    def test_follow_posts(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = naive_utcnow()
        p1 = Post(text="post from john", author=u1,
                  timestamp=now + timedelta(seconds=1))
        p2 = Post(text="post from susan", author=u2,
                  timestamp=now + timedelta(seconds=4))
        p3 = Post(text="post from mary", author=u3,
                  timestamp=now + timedelta(seconds=3))
        p4 = Post(text="post from david", author=u4,
                  timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = db.session.scalars(u1.followed_posts_select().order_by(
            Post.timestamp.desc())).all()
        f2 = db.session.scalars(u2.followed_posts_select().order_by(
            Post.timestamp.desc())).all()
        f3 = db.session.scalars(u3.followed_posts_select().order_by(
            Post.timestamp.desc())).all()
        f4 = db.session.scalars(u4.followed_posts_select().order_by(
            Post.timestamp.desc())).all()
        assert f1 == [p2, p4, p1]
        assert f2 == [p2, p3]
        assert f3 == [p3, p4]
        assert f4 == [p4]
