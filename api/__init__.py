"""
Welcome to the documentation for the Microblog API!

This project is written in Python, with the
[Flask](https://flask.palletsprojects.com/) web framework. This documentation
is generated automatically from the
[project's source code](https://github.com/miguelgrinberg/microblog-api) using
the [APIFairy](https://github.com/miguelgrinberg/apifairy) Flask extension.

## Introduction

Microblog-API is an easy to use web API for creating microblogs. It is an ideal
project to use when learning a front end framework, as it provides a fully
implemented back end that you can integrate against.

Microblog API provides all the base features required to implement a
microblogging project:

- User registration, login and logout
- Password recovery flow with reset emails
- Post creation and deletion
- Follow and unfollow users
- Feed with posts from followed users
- Pagination
- Option to disable authentication during development

## Configuration

If you are running Microblog API yourself while developing your front end,
there are a number of environment variables that you can set to configure its
behavior. The variables can be defined directly in the environment or in a
`.env` file in the project directory. The following table lists all the
environment variables that are currently used:

| Environment Variable | Default | Description |
| - | - | - |
| `SECRET_KEY` | `top-secret!` | A secret key used when signing tokens. |
| `DATABASE_URL`  | `sqlite:///db.sqlite` | The database URL, as defined by the [SQLAlchemy](https://docs.sqlalchemy.org/en/14/core/engines.html#database-urls) framework. |
| `SQL_ECHO` | not defined | Whether to echo SQL statements to the console for debugging purposes. |
| `DISABLE_AUTH` | not defined | Whether to disable authentication. When running with authentication disabled, the user is assumed to be logged as the user with `id=1`, which must exist in the database. |
| `ACCESS_TOKEN_MINUTES` | `15` | The number of minutes an access token is valid for. |
| `REFRESH_TOKEN_DAYS` | `7` | The number of days a refresh token is valid for. |
| `REFRESH_TOKEN_IN_COOKIE` | `yes` | Whether to return the refresh token in a secure cookie. |
| `REFRESH_TOKEN_IN_BODY` | `no` | Whether to return the refresh token in the response body. |
| `RESET_TOKEN_MINUTES` | `15` | The number of minutes a reset token is valid for. |
| `PASSWORD_RESET_URL` | `http://localhost:3000/reset` | The URL that will be used in password reset links. |
| `USE_CORS` | `yes` | Whether to allow cross-origin requests. If allowed, CORS support can be configured or customized with options provided by the Flask-CORS extension. |
| `DOCS_UI` | `elements` | The UI library to use for the documentation. Allowed values are `swagger_ui`, `redoc`, `rapidoc` and `elements`. |
| `MAIL_SERVER` | `localhost` | The mail server to use for sending emails. |
| `MAIL_PORT` | `25` | The port to use for sending emails. |
| `MAIL_USE_TLS` | not defined | Whether to use TLS when sending emails. |
| `MAIL_USERNAME` | not defined | The username to use for sending emails. |
| `MAIL_PASSWORD` | not defined | The password to use for sending emails. |
| `MAIL_DEFAULT_SENDER` | `donotreply@microblog.example.com` | The default sender to use for emails. |
| `GITHUB_CLIENT_ID` | not defined | The client ID for the GitHub OAuth2 application, used for logging in with a GitHub account. |
| `GITHUB_CLIENT_SECRET` | not defined | The client secret for the GitHub OAuth2 application, used for logging in with a GitHub account. |
| `GOOGLE_CLIENT_ID` | not defined | The client ID for the Google OAuth2 application, used for logging in with a Google account. |
| `GOOGLE_CLIENT_SECRET` | not defined | The client secret for the Google OAuth2 application, used for logging in with a Google account. |
| `OAUTH2_REDIRECT_URI` | `http://localhost:3000/oauth2/{provider}/callback` | The redirect URI to use for OAuth2 logins. A `{provider}` placeholder can be used to have the provider name inserted dynamically. |

## Authentication

The authentication flow for this API is based on *access* and *refresh*
tokens.

To obtain an access and refresh token pair, the client must send a `POST`
request to the `/api/tokens` endpoint, passing the username and password of
the user in a `Authorization` header, according to HTTP Basic Authentication
scheme. The response includes the access and refresh tokens in the body. For
added security in single-page applications, the refresh token is also returned
in a secure cookie.

Most endpoints in this API are authenticated with the access token, passed
in the `Authorization` header, using the `Bearer` scheme.

Access tokens are valid for 15 minutes (by default) from the time they are
issued. When the access token is expired, the client can renew it using the
refresh token. For this, the client must send a `PUT` request to the
`/api/tokens` endpoint, passing the expired access token in the body of the
request, and the refresh token either in the body, or through the secure cookie
sent when the tokens were requested. The response to this request will include
a new pair of tokens. Refresh tokens have a default validity period of 7 days,
and can only be used to renew the access token they were returned with. An
attempt to use a refresh token more than once is considered a possible attack,
and will cause all existing tokens for the user to be revoked immediately as a
mitigation measure.

All authentication failures are handled with a `401` status code in the
response.

### Password Resets

This API supports a password reset flow, to help users who forget their
passwords regain access to their accounts. To issue a password reset request,
the client must send a `POST` request to `/api/tokens/reset`, passing the
user's email in the body of the request. The user will receive a password reset
link by email, based on the password reset URL entered in the configuration
and a `token` query string paramter set to an email reset token, with a
validity of 15 minutes.

When the user clicks on the password reset link, the client application must
capture the `token` query string argument and send it in a `PUT` request to
`/api/tokens/reset`, along with the new password chosen by the user.

## Pagination

API endpoints that return collections of resources, such as the users or posts,
implement pagination, and the client must use query string arguments to specify
the range of items to return.

The number of items to return is specified by the `limit` argument, which is
optional. If not specified, the server sets the limit to a reasonable value for
the endpoint. If the limit is too large, the server may decide to use a lower
value instead. The following example shows how to request the first 10 users:

    http://localhost:5000/api/users?limit=10

The `offset` argument is used to specify the zero-based index of the first item
to return. If not given, the server sets the offset to 0. The following example
shows how to request the second page of users with a page size of 10:

    http://localhost:5000/api/users?limit=10&offset=10

Sometimes paginating with the `offset` argument can be inconvenient, such as
with collections where new elements are not always inserted at the end of the
list. As an alternative to `offset`, the `after` argument can be used to set
the start item to the item after the one specified. This API supports `after`
for collections of blog posts, which are sorted by their publication time in
descending order, and for collections of users, which are sorted by their
username in ascending order. For blog posts, the `after` argument must be set
to a date and time specification in ISO 8601 format, such as
`2020-01-01T00:00:00Z`. For users, the `after` argument must be set to a
string. Examples:

    http://localhost:5000/api/posts?limit=10&after=2021-01-01T00:00:00
    http://localhost:5000/api/users/me/followers?limit=10&after=diana

The response body in a paginated request contains a `data` attribute that is
set to the list of entities that are in the requested page. A `pagination`
attribute is also included with `offset`, `limit`, `count` and `total`
sub-attributes, which should enable the client to present pagination controls
to the user.

## Errors

All errors returned by this API use the following JSON structure:

```json
{
    "code": <numeric error code>,
    "message": <short error message>,
    "description": <longer error description>,
}
```

In the case of schema validation errors, an `errors` property is also returned,
containing a detailed list of validation errors found in the submitted request:

```json
{
    "code": <error code>,
    "message": <error message>,
    "description": <error description>,
    "errors": [ <error details>, ... ]
}
```
"""  # noqa: E501

from api.app import create_app, db, ma  # noqa: F401
