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
            'email': 'user2@example.com',
            'password': 'dog'
        })
        assert rv.status_code == 400
        rv = self.client.post('/api/users', json={
            'username': 'user2',
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
        rv = self.client.get('/api/me')
        assert rv.status_code == 200
        assert rv.json['username'] == 'test'
        assert rv.json['email'] == 'test@example.com'
        assert 'password' not in rv.json

    def test_edit_user_no_changes(self):
        rv = self.client.get('/api/me')
        assert rv.status_code == 200
        rv2 = self.client.put('/api/me', json={
            'username': rv.json['username'],
            'email': rv.json['email'],
            'about_me': rv.json['about_me'],
        })
        assert rv2.status_code == 200
        assert rv2.json['username'] == rv.json['username']
        assert rv2.json['email'] == rv.json['email']
        assert rv2.json['about_me'] == rv.json['about_me']

    def test_edit_me(self):
        rv = self.client.put('/api/me', json={
            'about_me': 'I am testing',
        })
        assert rv.status_code == 200
        assert rv.json['username'] == 'test'
        assert rv.json['email'] == 'test@example.com'
        assert rv.json['about_me'] == 'I am testing'
        assert 'password' not in rv.json

    def test_edit_password(self):
        rv = self.client.put('/api/me', json={
            'password': 'bar',
        })
        assert rv.status_code == 400
        rv = self.client.put('/api/me', json={
            'old_password': 'foo1',
            'password': 'bar',
        })
        assert rv.status_code == 400
        rv = self.client.put('/api/me', json={
            'old_password': 'foo',
            'password': 'bar',
        })
        assert rv.status_code == 200
        assert rv.json['username'] == 'test'
        assert rv.json['email'] == 'test@example.com'
        assert 'password' not in rv.json

        rv = self.client.post('/api/tokens', auth=('test@example.com', 'foo'))
        assert rv.status_code == 401
        rv = self.client.post('/api/tokens', auth=('test@example.com', 'bar'))
        assert rv.status_code == 200

    def test_follow_unfollow(self):
        rv = self.client.get('/api/me/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0
        assert rv.json['data'] == []

        rv = self.client.get('/api/me/followers')
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

        rv = self.client.get(f'/api/me/following/{id}')
        assert rv.status_code == 404

        rv = self.client.post(f'/api/me/following/{id}')
        assert rv.status_code == 204

        rv = self.client.get(f'/api/me/following/{id}')
        assert rv.status_code == 204

        rv = self.client.post(f'/api/me/following/{id}')
        assert rv.status_code == 409

        rv = self.client.get('/api/me/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['username'] == 'susan'

        rv = self.client.get('/api/me/followers')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0

        rv = self.client.get('/api/me/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['username'] == 'susan'

        rv = self.client.get('/api/me/followers')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0

        rv = self.client.get('/api/users/2/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0

        rv = self.client.get('/api/users/2/followers')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 1
        assert rv.json['data'][0]['username'] == 'test'

        rv = self.client.delete(f'/api/me/following/{id}')
        assert rv.status_code == 204

        rv = self.client.delete(f'/api/me/following/{id}')
        assert rv.status_code == 409

        rv = self.client.get('/api/me/following')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 0
        assert rv.json['data'] == []
