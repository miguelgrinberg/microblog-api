from datetime import timedelta
from api.app import db
from api.dates import naive_utcnow
from api.models import User, Post
from tests.base_test_case import BaseTestCase


class PaginationTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        user = db.session.get(User, 1)
        tm = naive_utcnow()
        for i in range(105):
            tm -= timedelta(minutes=1)
            post = Post(text=f'Post {i + 1}', author=user, timestamp=tm)
            db.session.add(post)
        for i in range(26):
            follower = User(username=chr(ord('a') + i),
                            email=f'{chr(ord("a") + i)}@example.com')
            db.session.add(follower)
            follower.follow(user)
        db.session.commit()

    def test_pagination_default(self):
        rv = self.client.get('/api/posts')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 0
        assert rv.json['pagination']['count'] == 25
        assert rv.json['pagination']['limit'] == 25
        assert len(rv.json['data']) == 25
        assert rv.json['data'][0]['text'] == 'Post 1'
        assert rv.json['data'][24]['text'] == 'Post 25'

    def test_pagination_page(self):
        rv = self.client.get('/api/posts?offset=30&limit=10')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 30
        assert rv.json['pagination']['count'] == 10
        assert rv.json['pagination']['limit'] == 10
        assert len(rv.json['data']) == 10
        assert rv.json['data'][0]['text'] == 'Post 31'
        assert rv.json['data'][9]['text'] == 'Post 40'

    def test_pagination_last(self):
        rv = self.client.get('/api/posts?offset=99')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 99
        assert rv.json['pagination']['count'] == 6
        assert rv.json['pagination']['limit'] == 25
        assert len(rv.json['data']) == 6
        assert rv.json['data'][0]['text'] == 'Post 100'
        assert rv.json['data'][5]['text'] == 'Post 105'

    def test_pagination_invalid(self):
        rv = self.client.get('/api/posts?offset=-2')
        assert rv.status_code == 400
        rv = self.client.get('/api/posts?offset=110')
        assert rv.status_code == 400
        rv = self.client.get('/api/posts?limit=0')
        assert rv.status_code == 400
        rv = self.client.get('/api/posts?limit=-10')
        assert rv.status_code == 400

    def test_pagination_custom_limit(self):
        rv = self.client.get('/api/posts?offset=16&limit=5')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 16
        assert rv.json['pagination']['count'] == 5
        assert rv.json['pagination']['limit'] == 5
        assert len(rv.json['data']) == 5
        assert rv.json['data'][0]['text'] == 'Post 17'
        assert rv.json['data'][4]['text'] == 'Post 21'

    def test_pagination_large_per_page(self):
        rv = self.client.get('/api/posts?offset=37&limit=50')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 37
        assert rv.json['pagination']['count'] == 25
        assert rv.json['pagination']['limit'] == 25
        assert len(rv.json['data']) == 25
        assert rv.json['data'][0]['text'] == 'Post 38'
        assert rv.json['data'][24]['text'] == 'Post 62'

    def test_pagination_offset_and_after(self):
        rv = self.client.get('/api/posts?offset=37&after=2021-01-01T00:00:00')
        assert rv.status_code == 400
        rv = self.client.get('/api/users/1/following?offset=37&after=foo')
        assert rv.status_code == 400

    def test_pagination_after_desc(self):
        rv = self.client.get('/api/posts')
        assert rv.status_code == 200
        tm = rv.json['data'][5]['timestamp']

        rv = self.client.get(f'/api/posts?after={tm}')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 6
        assert rv.json['pagination']['count'] == 25
        assert rv.json['pagination']['limit'] == 25
        assert len(rv.json['data']) == 25
        assert rv.json['data'][0]['text'] == 'Post 7'
        assert rv.json['data'][24]['text'] == 'Post 31'

    def test_pagination_after_asc(self):
        rv = self.client.get('/api/users/1/followers?after=g')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 26
        assert rv.json['pagination']['offset'] == 7
        assert rv.json['pagination']['count'] == 19
        assert rv.json['pagination']['limit'] == 25
        assert len(rv.json['data']) == 19
        assert rv.json['data'][0]['username'] == 'h'
        assert rv.json['data'][-1]['username'] == 'z'
