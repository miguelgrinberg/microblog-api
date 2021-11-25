from flask import current_app
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from werkzeug.exceptions import Unauthorized, Forbidden

from api.app import db
from api.models import User

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_password(username, password):
    if username and password:
        user = db.session.scalar(User.select().filter_by(username=username))
        if user and user.check_password(password):
            return user


@basic_auth.error_handler
def basic_auth_error(status=401):
    error = (Forbidden if status == 403 else Unauthorized)()
    return {
        'code': error.code,
        'name': error.name,
        'description': error.description,
    }, error.code


@token_auth.verify_token
def verify_token(access_token):
    if current_app.config['DISABLE_AUTH']:
        user = db.session.get(User, 1)
        user.ping()
        return {'type': 'access', 'user': user, 'fresh': True}
    if access_token:
        return User.check_access_token(access_token)


@token_auth.error_handler
def token_auth_error(status=401):
    error = (Forbidden if status == 403 else Unauthorized)()
    return {
        'code': error.code,
        'name': error.name,
        'description': error.description,
    }, error.code
