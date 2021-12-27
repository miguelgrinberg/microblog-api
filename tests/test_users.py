from tests.base_test_case import BaseTestCase


class UserTests(BaseTestCase):
    def test_create_user(self):
        rv = self.client.post('/api/users', json={
            'username': 'user',
            'email': 'user@example.com',
            'password': 'dog'
        })
        assert rv.status_code == 201
        user_id = rv.json['id']
        rv = self.client.post('/api/users', json={
            'username': 'user',
            'email': 'user@example.com',
            'password': 'dog'
        })
        assert rv.status_code == 400
        rv = self.client.get(f'/api/users/{user_id}')
        assert rv.status_code == 200
        assert rv.json['username'] == 'user'
        assert rv.json['email'] == 'user@example.com'

    def test_create_invalid_user(self):
        rv = self.client.post('/api/users', json={
            'username': '1user',
            'email': 'user@example.com',
            'password': 'dog'
        })
        assert rv.status_code == 400
        rv = self.client.post('/api/users', json={
            'username': '',
            'email': 'user@example.com',
            'password': 'dog'
        })
        assert rv.status_code == 400

    def test_get_users(self):
        rv = self.client.get('/api/users')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['username'] == 'test'
        assert rv.json['data'][0]['email'] == 'test@example.com'
        assert 'password' not in rv.json['data'][0]

    def test_get_user(self):
        rv = self.client.get('/api/users/1')
        assert rv.status_code == 200
        assert rv.json['id'] == 1
        assert rv.json['username'] == 'test'
        assert rv.json['email'] == 'test@example.com'
        assert 'password' not in rv.json
        rv = self.client.get('/api/users/test')
        assert rv.status_code == 200
        assert rv.json['id'] == 1
        assert rv.json['username'] == 'test'
        assert rv.json['email'] == 'test@example.com'
        assert 'password' not in rv.json

    def test_get_me(self):
        rv = self.client.get('/api/users/me')
        assert rv.status_code == 200
        assert rv.json['username'] == 'test'
        assert rv.json['email'] == 'test@example.com'
        assert 'password' not in rv.json

    def test_edit_me(self):
        rv = self.client.put('/api/users/me', json={
            'about_me': 'I am testing',
        })
        assert rv.status_code == 200
        assert rv.json['username'] == 'test'
        assert rv.json['email'] == 'test@example.com'
        assert rv.json['about_me'] == 'I am testing'
        assert 'password' not in rv.json

    def test_follow_unfollow(self):
        rv = self.client.get('/api/users/me/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0
        assert rv.json['data'] == []

        rv = self.client.get('/api/users/me/followers')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0
        assert rv.json['data'] == []

        rv = self.client.post('/api/users', json={
            'username': 'susan',
            'email': 'susan@example.com',
            'password': 'dog',
        })
        assert rv.status_code == 201
        id = rv.json['id']

        rv = self.client.post(f'/api/users/me/following/{id}')
        assert rv.status_code == 204

        rv = self.client.post(f'/api/users/me/following/{id}')
        assert rv.status_code == 409

        rv = self.client.get('/api/users/me/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['username'] == 'susan'

        rv = self.client.get('/api/users/me/followers')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0

        rv = self.client.get('/api/users/1/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['username'] == 'susan'

        rv = self.client.get('/api/users/1/followers')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0

        rv = self.client.get('/api/users/2/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0

        rv = self.client.get('/api/users/2/followers')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['username'] == 'test'

        rv = self.client.delete(f'/api/users/me/following/{id}')
        assert rv.status_code == 204

        rv = self.client.delete(f'/api/users/me/following/{id}')
        assert rv.status_code == 409

        rv = self.client.get('/api/users/me/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0
        assert rv.json['data'] == []
