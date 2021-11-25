from api.app import db
from api.models import User, Post
from tests.base_test_case import BaseTestCase


class PaginationTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        user = db.session.get(User, 1)
        for i in range(105):
            post = Post(body=f'Post {i + 1}', author=user)
            db.session.add(post)
        db.session.commit()

    def test_pagination_default(self):
        rv = self.client.get('/api/posts')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 0
        assert rv.json['pagination']['count'] == 10
        assert len(rv.json['data']) == 10
        assert rv.json['data'][0]['body'] == 'Post 1'
        assert rv.json['data'][9]['body'] == 'Post 10'

    def test_pagination_page(self):
        rv = self.client.get('/api/posts?offset=30')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 30
        assert rv.json['pagination']['count'] == 10
        assert len(rv.json['data']) == 10
        assert rv.json['data'][0]['body'] == 'Post 31'
        assert rv.json['data'][9]['body'] == 'Post 40'

    def test_pagination_last(self):
        rv = self.client.get('/api/posts?offset=99')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 99
        assert rv.json['pagination']['count'] == 6
        assert len(rv.json['data']) == 6
        assert rv.json['data'][0]['body'] == 'Post 100'
        assert rv.json['data'][5]['body'] == 'Post 105'

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
        assert len(rv.json['data']) == 5
        assert rv.json['data'][0]['body'] == 'Post 17'
        assert rv.json['data'][4]['body'] == 'Post 21'

    def test_pagination_large_per_page(self):
        rv = self.client.get('/api/posts?offset=37&limit=25')
        assert rv.status_code == 200
        assert rv.json['pagination']['total'] == 105
        assert rv.json['pagination']['offset'] == 37
        assert rv.json['pagination']['count'] == 10
        assert len(rv.json['data']) == 10
        assert rv.json['data'][0]['body'] == 'Post 38'
        assert rv.json['data'][9]['body'] == 'Post 47'
