from datetime import timedelta
from unittest import mock
from api.dates import naive_utcnow
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

    def test_get_token_in_cookie_only(self):
        self.app.config['REFRESH_TOKEN_IN_COOKIE'] = True
        self.app.config['REFRESH_TOKEN_IN_BODY'] = False
        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        assert rv.json['refresh_token'] is None
        assert rv.headers['Set-Cookie'].startswith('refresh_token=')

    def test_get_token_in_body_only(self):
        self.app.config['REFRESH_TOKEN_IN_COOKIE'] = False
        self.app.config['REFRESH_TOKEN_IN_BODY'] = True
        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        assert rv.json['refresh_token'] is not None
        assert 'Set-Cookie' not in rv.headers

    def test_token_expired(self):
        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        access_token = rv.json['access_token']

        with mock.patch('api.models.naive_utcnow') as now:
            now.return_value = naive_utcnow() + timedelta(days=1)
            rv = self.client.get('/api/users', headers={
                'Authorization': f'Bearer {access_token}'})
            assert rv.status_code == 401

    def test_refresh_token(self):
        rv = self.client.post('/api/tokens', auth=('test@example.com', 'foo'))
        assert rv.status_code == 200
        access_token1 = rv.json['access_token']
        refresh_token1 = rv.json['refresh_token']

        rv = self.client.put(
            '/api/tokens', json={'access_token': access_token1},
            headers={'Cookie': 'refresh_token=' + refresh_token1})
        assert rv.status_code == 200
        assert rv.json['access_token'] != access_token1
        assert rv.json['refresh_token'] != refresh_token1
        access_token2 = rv.json['access_token']

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token2}'})
        assert rv.status_code == 200
        assert rv.json['data'][0]['username'] == 'test'

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token1}'})
        assert rv.status_code == 401

    def test_refresh_token_failure(self):
        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        access_token = rv.json['access_token']
        refresh_token = rv.json['refresh_token']

        self.client.delete_cookie('refresh_token', path='/api/tokens')
        rv = self.client.put('/api/tokens', json={
            'access_token': access_token})
        assert rv.status_code == 401
        rv = self.client.put('/api/tokens', json={
            'access_token': access_token,
            'refresh_token': refresh_token + 'x',
        })
        rv = self.client.put('/api/tokens', json={
            'access_token': access_token + 'x',
            'refresh_token': refresh_token,
        })
        assert rv.status_code == 401
        rv = self.client.put('/api/tokens', json={
            'access_token': 'foo',
            'refresh_token': refresh_token,
        })
        assert rv.status_code == 401

    def test_refresh_revoke_all(self):
        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        access_token1 = rv.json['access_token']
        refresh_token1 = rv.json['refresh_token']

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token1}'})
        assert rv.status_code == 200

        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        access_token2 = rv.json['access_token']
        refresh_token2 = rv.json['refresh_token']

        rv = self.client.put('/api/tokens', json={
            'access_token': access_token2})
        assert rv.status_code == 200
        access_token3 = rv.json['access_token']
        refresh_token3 = rv.json['refresh_token']

        rv = self.client.put('/api/tokens', json={
            'access_token': access_token2,
            'refresh_token': refresh_token2})
        assert rv.status_code == 401  # duplicate refresh

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token1}'})
        assert rv.status_code == 401
        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token2}'})
        assert rv.status_code == 401
        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token3}'})
        assert rv.status_code == 401

        rv = self.client.put('/api/tokens', json={
            'access_token': access_token1,
            'refresh_token': refresh_token1})
        assert rv.status_code == 401
        rv = self.client.put('/api/tokens', json={
            'access_token': access_token2,
            'refresh_token': refresh_token2})
        assert rv.status_code == 401
        rv = self.client.put('/api/tokens', json={
            'access_token': access_token3,
            'refresh_token': refresh_token3})
        assert rv.status_code == 401

    def test_revoke(self):
        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 200
        access_token = rv.json['access_token']

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token}'})
        assert rv.status_code == 200

        rv = self.client.delete('/api/tokens', headers={
            'Authorization': f'Bearer {access_token}'})
        assert rv.status_code == 204

        rv = self.client.get('/api/users', headers={
            'Authorization': f'Bearer {access_token}'})
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
                'email': 'bad@example.com',
            })
            assert rv.status_code == 204
            rv = self.client.post('/api/tokens/reset', json={
                'email': 'test@example.com',
            })
            assert rv.status_code == 204
        send_email.assert_called_once()
        assert send_email.call_args[0] == (
            'test@example.com', 'Reset Your Password', 'reset')
        reset_token = send_email.call_args[1]['token']
        reset_url = send_email.call_args[1]['url']
        assert reset_url == 'http://localhost:3000/reset?token=' + reset_token

        rv = self.client.put('/api/tokens/reset', json={
            'token': reset_token + 'x',
            'new_password': 'bar'
        })
        assert rv.status_code == 400

        rv = self.client.put('/api/tokens/reset', json={
            'token': reset_token,
            'new_password': 'bar'
        })
        assert rv.status_code == 204

        rv = self.client.post('/api/tokens', auth=('test', 'foo'))
        assert rv.status_code == 401

        rv = self.client.post('/api/tokens', auth=('test', 'bar'))
        assert rv.status_code == 200

    def test_oauth(self):
        rv = self.client.get('/api/tokens/oauth2/bar')
        assert rv.status_code == 404
        rv = self.client.get('/api/tokens/oauth2/foo')
        assert rv.status_code == 302
        assert rv.headers['Location'].startswith('https://foo.com/login?')
        args = rv.headers['Location'].split('?')[1].split('&')
        assert 'client_id=foo-id' in args
        assert ('redirect_uri='
                'http%3A%2F%2Flocalhost%2Foauth2%2Ffoo%2Fcallback') in args
        assert 'response_type=code' in args
        assert 'scope=user+email' in args
        state = None
        for arg in args:
            if arg.startswith('state='):
                state = arg.split('=')[1]
        assert state is not None

        # redirect to auth provider
        rv = self.client.post('/api/tokens/oauth2/bar',
                              json={'code': '123', 'state': state})
        assert rv.status_code == 404
        rv = self.client.post('/api/tokens/oauth2/foo',
                              json={'code': '123', 'state': 'not-the-state'})
        assert rv.status_code == 401
        with mock.patch('api.tokens.requests.post') as requests_post:
            requests_post.return_value.status_code = 401
            rv = self.client.post('/api/tokens/oauth2/foo',
                                  json={'code': '123', 'state': state})
            assert rv.status_code == 401
            requests_post.assert_called_with(
                'https://foo.com/token', data={
                    'client_id': 'foo-id',
                    'client_secret': 'foo-secret',
                    'code': '123',
                    'grant_type': 'authorization_code',
                    'redirect_uri': 'http://localhost/oauth2/foo/callback',
                }, headers={'Accept': 'application/json'})

        # auth with authorization code (failure case)
        with mock.patch('api.tokens.requests.post') as requests_post:
            with mock.patch('api.tokens.requests.get') as requests_get:
                requests_post.return_value.status_code = 200
                requests_post.return_value.json.return_value = {
                    'access_token': 'foo-token',
                }
                requests_get.return_value.status_code = 401
                rv = self.client.post('/api/tokens/oauth2/foo',
                                      json={'code': '123', 'state': state})
                assert rv.status_code == 401
                requests_post.assert_called_with(
                    'https://foo.com/token', data={
                        'client_id': 'foo-id',
                        'client_secret': 'foo-secret',
                        'code': '123',
                        'grant_type': 'authorization_code',
                        'redirect_uri': 'http://localhost/oauth2/foo/callback',
                    }, headers={'Accept': 'application/json'})

        # auth with authorization code (failure case)
        with mock.patch('api.tokens.requests.post') as requests_post:
            with mock.patch('api.tokens.requests.get') as requests_get:
                requests_post.return_value.status_code = 200
                requests_post.return_value.json.return_value = {
                    'not_access_token': 'foo-token',
                }
                requests_get.return_value.status_code = 200
                rv = self.client.post('/api/tokens/oauth2/foo',
                                      json={'code': '123', 'state': state})
                assert rv.status_code == 401
                requests_post.assert_called_with(
                    'https://foo.com/token', data={
                        'client_id': 'foo-id',
                        'client_secret': 'foo-secret',
                        'code': '123',
                        'grant_type': 'authorization_code',
                        'redirect_uri': 'http://localhost/oauth2/foo/callback',
                    }, headers={'Accept': 'application/json'})

        # auth with authorization code (success case with new user)
        with mock.patch('api.tokens.requests.post') as requests_post:
            with mock.patch('api.tokens.requests.get') as requests_get:
                requests_post.return_value.status_code = 200
                requests_post.return_value.json.return_value = {
                    'access_token': 'foo-token',
                }
                requests_get.return_value.status_code = 200
                requests_get.return_value.json.return_value = {
                    'id': 'user-id',
                    'email': 'foo@foo.com',
                }
                rv = self.client.post('/api/tokens/oauth2/foo',
                                      json={'code': '123', 'state': state})
                assert rv.status_code == 200
                requests_post.assert_called_with(
                    'https://foo.com/token', data={
                        'client_id': 'foo-id',
                        'client_secret': 'foo-secret',
                        'code': '123',
                        'grant_type': 'authorization_code',
                        'redirect_uri': 'http://localhost/oauth2/foo/callback',
                    }, headers={'Accept': 'application/json'})
                requests_get.assert_called_with(
                    'https://foo.com/me', headers={
                        'Authorization': 'Bearer foo-token',
                        'Accept': 'application/json',
                    })
                access_token = rv.json['access_token']

                # test the access token
                rv = self.client.get('/api/me', headers={
                    'Authorization': f'Bearer {access_token}'})
                assert rv.status_code == 200
                assert rv.json['username'] == 'foo'

        # auth with authorization code (success case with existing user)
        with mock.patch('api.tokens.requests.post') as requests_post:
            with mock.patch('api.tokens.requests.get') as requests_get:
                requests_post.return_value.status_code = 200
                requests_post.return_value.json.return_value = {
                    'access_token': 'foo-token',
                }
                requests_get.return_value.status_code = 200
                requests_get.return_value.json.return_value = {
                    'id': 'user-id',
                    'email': 'test@example.com',
                }
                rv = self.client.post('/api/tokens/oauth2/foo',
                                      json={'code': '123', 'state': state})
                assert rv.status_code == 200
                requests_post.assert_called_with(
                    'https://foo.com/token', data={
                        'client_id': 'foo-id',
                        'client_secret': 'foo-secret',
                        'code': '123',
                        'grant_type': 'authorization_code',
                        'redirect_uri': 'http://localhost/oauth2/foo/callback',
                    }, headers={'Accept': 'application/json'})
                requests_get.assert_called_with(
                    'https://foo.com/me', headers={
                        'Authorization': 'Bearer foo-token',
                        'Accept': 'application/json',
                    })
                access_token = rv.json['access_token']

                # test the access token
                rv = self.client.get('/api/me', headers={
                    'Authorization': f'Bearer {access_token}'})
                assert rv.status_code == 200
                assert rv.json['username'] == 'test'
