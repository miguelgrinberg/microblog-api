from unittest import mock
from tests.base_test_case import BaseTestCase, TestConfigWithAuth


class AuthTests(BaseTestCase):
    config = TestConfigWithAuth

    def test_no_auth(self):
        rv = self.client.get('/api/users')
        assert rv.status_code == 401

    def test_get_token(self):
        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        access_token = rv.json['access_token']
        refresh_token = rv.json['refresh_token']

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token}'})
        assert rv.status_code == 200
        assert rv.json['data'][0]['username'] == 'test'

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token + "x"}'})
        assert rv.status_code == 401

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {refresh_token}'})
        assert rv.status_code == 401

    def test_refresh_token(self):
        rv = self.client.post('/api/tokens', auth=('test@example.com', 'foo'))
        assert rv.status_code == 200
        access_token = rv.json['access_token']
        refresh_token = rv.json['refresh_token']

        rv = self.client.put('/api/tokens', json={
            'access_token': access_token,
            'refresh_token': refresh_token,
        })
        assert rv.status_code == 200
        token = rv.json['access_token']

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {token}'})
        assert rv.status_code == 200
        assert rv.json['data'][0]['username'] == 'test'

        rv = self.client.put('/api/me', headers={
            'Authorization': f'Bearer {token}'}, json={'password': 'bar'})
        assert rv.status_code == 403

    def test_refresh_token_failure(self):
        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        access_token = rv.json['access_token']
        refresh_token = rv.json['refresh_token']

        rv = self.client.put('/api/tokens', json={
            'access_token': access_token + 'x',
            'refresh_token': refresh_token,
        })
        assert rv.status_code == 401

        rv = self.client.put('/api/tokens', json={
            'access_token': access_token,
            'refresh_token': refresh_token + 'x',
        })
        assert rv.status_code == 401

    def test_no_login(self):
        rv = self.client.post('/api/tokens')
        assert rv.status_code == 401

    def test_bad_login(self):
        rv = self.client.post('/api/tokens', auth=('test', 'bar'))
        assert rv.status_code == 401

    def test_reset_password(self):
        with mock.patch('api.tokens.send_email') as send_email:
            rv = self.client.post('/api/tokens/reset', json={
                'email': 'bad@example.com'})
            assert rv.status_code == 204
            rv = self.client.post('/api/tokens/reset', json={
                'email': 'test@example.com'})
            assert rv.status_code == 204
        send_email.assert_called_once()
        assert send_email.call_args[0] == (
            'test@example.com', 'Reset Your Password', 'reset')
        reset_token = send_email.call_args[1]['token']

        rv = self.client.put('/api/tokens/reset', json={
            'token': reset_token,
            'new_password': 'bar'
        })
        assert rv.status_code == 204

        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 401

        rv = self.client.post('/api/tokens', auth=('test', 'bar'))
        assert rv.status_code == 200
