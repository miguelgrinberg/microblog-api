from flask import Blueprint, request, abort
from apifairy import authenticate, body, response, other_responses

from api.app import db
from api.auth import basic_auth
from api.email import send_email
from api.models import User
from api.schemas import TokenSchema, PasswordResetRequestSchema, \
    PasswordResetSchema, EmptySchema

tokens = Blueprint('tokens', __name__)
token_schema = TokenSchema()


@tokens.route('/tokens', methods=['POST'])
@authenticate(basic_auth)
@response(token_schema)
@other_responses({401: 'Invalid username or password'})
def new():
    """Create new access and refresh tokens"""
    access_token, refresh_token = basic_auth.current_user().generate_tokens(
        fresh=True)
    return {'access_token': access_token, 'refresh_token': refresh_token}


@tokens.route('/tokens', methods=['PUT'])
@body(token_schema)
@response(token_schema, description='Newly issued access and refresh tokens')
@other_responses({401: 'Invalid access or refresh token'})
def refresh(args):
    """Refresh an expired access token"""
    user = User.check_refresh_token(
        args['refresh_token'], args['access_token'])
    if user is None:
        abort(401)
    access_token, refresh_token = user['user'].generate_tokens(fresh=False)
    return {'access_token': access_token, 'refresh_token': refresh_token}


@tokens.route('/tokens/reset', methods=['POST'])
@body(PasswordResetRequestSchema)
@response(EmptySchema, status_code=204,
          description='Password reset email sent')
def reset(args):
    """Request a password reset token"""
    user = db.session.scalar(User.select().filter_by(email=args['email']))
    if user is not None:
        reset_token = user.generate_reset_token()
        reset_url = (request.referrer or '') + '?token=' + reset_token
        send_email(args['email'], 'Reset Your Password', 'reset',
                   token=reset_token, url=reset_url)
    return {}


@tokens.route('/tokens/reset', methods=['PUT'])
@body(PasswordResetSchema)
@response(EmptySchema, status_code=204,
          description='Password reset successful')
@other_responses({400: 'Invalid reset token'})
def password_reset(args):
    """Reset a user password"""
    user = User.check_reset_token(args['token'])
    user.password = args['new_password']
    db.session.commit()
    return {}, 204
