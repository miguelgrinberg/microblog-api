from api.app import db
from api.models import User, Post
from tests.base_test_case import BaseTestCase


class PostTests(BaseTestCase):
    def test_new_post(self):
        rv = self.client.post('/api/posts', json={
            'body': 'This is a test post',
        })
        assert rv.status_code == 201
        assert rv.json['body'] == 'This is a test post'
        assert rv.json['author']['username'] == 'test'
        id = rv.json['id']

        rv = self.client.get(f'/api/posts/{id}')
        assert rv.status_code == 200
        assert rv.json['body'] == 'This is a test post'

        rv = self.client.get('/api/posts')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['body'] == 'This is a test post'

        rv = self.client.get('/api/users/1/posts')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['body'] == 'This is a test post'

        rv = self.client.get('/api/users/2/posts')
        assert rv.status_code == 404

    def test_edit_post(self):
        rv = self.client.post('/api/posts', json={
            'body': 'This is a test post',
        })
        assert rv.status_code == 201
        assert rv.json['body'] == 'This is a test post'
        id = rv.json['id']

        rv = self.client.put(f'/api/posts/{id}', json={
            'body': 'This is a test post edited',
        })
        assert rv.status_code == 200
        assert rv.json['body'] == 'This is a test post edited'

        rv = self.client.get(f'/api/posts/{id}')
        assert rv.status_code == 200
        assert rv.json['body'] == 'This is a test post edited'

    def test_delete_post(self):
        rv = self.client.post('/api/posts', json={
            'body': 'This is a test post',
        })
        assert rv.status_code == 201
        assert rv.json['body'] == 'This is a test post'
        id = rv.json['id']

        rv = self.client.delete(f'/api/posts/{id}')
        assert rv.status_code == 204

        rv = self.client.get(f'/api/posts/{id}')
        assert rv.status_code == 404

    def test_post_timeline(self):
        user1 = db.session.get(User, 1)
        user2 = User(username='susan', email='susan@example.com',
                     password='dog')
        db.session.add(user2)
        db.session.commit()
        user1.follow(user2)
        post1 = Post(body='Post 1', author=user2)
        post2 = Post(body='Post 2', author=user1)
        post3 = Post(body='Post 3', author=user2)
        db.session.add_all([post1, post2, post3])
        db.session.commit()

        rv1 = self.client.get('/api/users/me/timeline')
        rv2 = self.client.get('/api/users/1/timeline')
        for rv in [rv1, rv2]:
            assert rv.status_code == 200
            assert rv.json['pagination']['total'] == 3
            assert rv.json['data'][0]['body'] == 'Post 3'
            assert rv.json['data'][0]['author']['username'] == 'susan'
            assert rv.json['data'][1]['body'] == 'Post 2'
            assert rv.json['data'][1]['author']['username'] == 'test'
            assert rv.json['data'][2]['body'] == 'Post 1'
            assert rv.json['data'][2]['author']['username'] == 'susan'

    def test_permissions(self):
        user = User(username='susan', email='susan@example.com',
                    password='dog')
        post = Post(body='This is a test post', author=user)
        db.session.add_all([user, post])
        db.session.commit()
        id = post.id

        rv = self.client.put(f'/api/posts/{id}', json={
            'body': 'This is a test post edited',
        })
        assert rv.status_code == 403

        rv = self.client.delete(f'/api/posts/{id}')
        assert rv.status_code == 403

        rv = self.client.get(f'/api/posts/{id}')
        assert rv.status_code == 200
        assert rv.json['body'] == 'This is a test post'
