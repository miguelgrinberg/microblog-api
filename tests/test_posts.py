from datetime import timedelta
from api.app import db
from api.dates import naive_utcnow
from api.models import User, Post
from tests.base_test_case import BaseTestCase


class PostTests(BaseTestCase):
    def test_new_post(self):
        rv = self.client.post('/api/posts', json={
            'text': 'This is a test post',
        })
        assert rv.status_code == 201
        assert rv.json['text'] == 'This is a test post'
        assert rv.json['author']['username'] == 'test'
        id = rv.json['id']

        rv = self.client.get(f'/api/posts/{id}')
        assert rv.status_code == 200
        assert rv.json['text'] == 'This is a test post'

        rv = self.client.get('/api/posts')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['text'] == 'This is a test post'

        rv = self.client.get('/api/users/1/posts')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['text'] == 'This is a test post'

        rv = self.client.get('/api/users/2/posts')
        assert rv.status_code == 404

    def test_edit_post(self):
        rv = self.client.post('/api/posts', json={
            'text': 'This is a test post',
        })
        assert rv.status_code == 201
        assert rv.json['text'] == 'This is a test post'
        id = rv.json['id']

        rv = self.client.put(f'/api/posts/{id}', json={
            'text': 'This is a test post edited',
        })
        assert rv.status_code == 200
        assert rv.json['text'] == 'This is a test post edited'

        rv = self.client.get(f'/api/posts/{id}')
        assert rv.status_code == 200
        assert rv.json['text'] == 'This is a test post edited'

    def test_delete_post(self):
        rv = self.client.post('/api/posts', json={
            'text': 'This is a test post',
        })
        assert rv.status_code == 201
        assert rv.json['text'] == 'This is a test post'
        id = rv.json['id']

        rv = self.client.delete(f'/api/posts/{id}')
        assert rv.status_code == 204

        rv = self.client.get(f'/api/posts/{id}')
        assert rv.status_code == 404

    def test_post_feed(self):
        user1 = db.session.get(User, 1)
        user2 = User(username='susan', email='susan@example.com',
                     password='dog')
        db.session.add(user2)
        db.session.commit()
        user1.follow(user2)
        now = naive_utcnow()
        post1 = Post(text='Post 1', author=user2,
                     timestamp=now - timedelta(minutes=2))
        post2 = Post(text='Post 2', author=user1,
                     timestamp=now - timedelta(minutes=1))
        post3 = Post(text='Post 3', author=user2, timestamp=now)
        db.session.add_all([post1, post2, post3])
        db.session.commit()

        rv = self.client.get('/api/feed')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 3
        assert rv.json['data'][0]['text'] == 'Post 3'
        assert rv.json['data'][0]['author']['username'] == 'susan'
        assert rv.json['data'][1]['text'] == 'Post 2'
        assert rv.json['data'][1]['author']['username'] == 'test'
        assert rv.json['data'][2]['text'] == 'Post 1'
        assert rv.json['data'][2]['author']['username'] == 'susan'

    def test_permissions(self):
        user = User(username='susan', email='susan@example.com',
                    password='dog')
        post = Post(text='This is a test post', author=user)
        db.session.add_all([user, post])
        db.session.commit()
        id = post.id

        rv = self.client.put(f'/api/posts/{id}', json={
            'text': 'This is a test post edited',
        })
        assert rv.status_code == 403

        rv = self.client.delete(f'/api/posts/{id}')
        assert rv.status_code == 403

        rv = self.client.get(f'/api/posts/{id}')
        assert rv.status_code == 200
        assert rv.json['text'] == 'This is a test post'
