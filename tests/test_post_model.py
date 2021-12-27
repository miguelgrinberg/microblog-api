from api.app import db
from api.models import User, Post
from tests.base_test_case import BaseTestCase


class PostModelTests(BaseTestCase):
    def test_url(self):
        u = User(username='john', email='john@example.com')
        p = Post(text='test post', author=u)
        db.session.add_all([u, p])
        db.session.commit()
        assert p.url == 'http://localhost:5000/api/posts/' + str(p.id)
