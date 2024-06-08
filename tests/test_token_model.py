from datetime import timedelta
from api.app import db
from api.dates import naive_utcnow
from api.models import Token, User
from tests.base_test_case import BaseTestCase


class TokenModelTests(BaseTestCase):
    def test_token_clean(self):
        user = db.session.scalar(User.select())
        token1 = Token(
            access_token='a1', refresh_token='r1',
            access_expiration=naive_utcnow() + timedelta(days=1),
            refresh_expiration=naive_utcnow() + timedelta(days=1),
            user=user)
        token2 = Token(
            access_token='a2', refresh_token='r2',
            access_expiration=naive_utcnow() - timedelta(days=2),
            refresh_expiration=naive_utcnow() - timedelta(days=2),
            user=user)
        db.session.add_all([token1, token2])
        db.session.commit()

        Token.clean()
        db.session.commit()

        tokens = db.session.scalars(Token.select()).all()
        assert len(tokens) == 1
        assert tokens[0].access_token == 'a1'
