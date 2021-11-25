from api import ma
from api.models import User, Post

paginated_schema_cache = {}


class EmptySchema(ma.Schema):
    pass


class PaginationRequestSchema(ma.Schema):
    class Meta:
        ordered = True

    offset = ma.Integer()
    limit = ma.Integer()
    total = ma.Integer(dump_only=True)


class PaginationSchema(ma.Schema):
    class Meta:
        ordered = True

    offset = ma.Integer()
    count = ma.Integer()
    total = ma.Integer(dump_only=True)


def PaginatedCollection(schema):
    if schema in paginated_schema_cache:
        return paginated_schema_cache[schema]

    class PaginatedSchema(ma.Schema):
        class Meta:
            ordered = True
            name = 'Foo'

        pagination = ma.Nested(PaginationSchema)
        data = ma.Nested(schema, many=True)

    PaginatedSchema.__name__ = 'Paginated{}'.format(schema.__class__.__name__)
    paginated_schema_cache[schema] = PaginatedSchema
    return PaginatedSchema


class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        ordered = True

    id = ma.auto_field(dump_only=True)
    url = ma.String(dump_only=True)
    username = ma.auto_field(required=True)
    email = ma.auto_field(required=True)
    password = ma.String(required=True, load_only=True)
    avatar_url = ma.String(dump_only=True)
    about_me = ma.auto_field()
    first_seen = ma.auto_field(dump_only=True)
    last_seen = ma.auto_field(dump_only=True)
    posts_url = ma.URLFor('posts.user_all', values={'id': '<id>'},
                          dump_only=True)


class PostSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Post
        include_fk = True
        ordered = True

    id = ma.auto_field(dump_only=True)
    url = ma.String(dump_only=True)
    body = ma.auto_field(required=True)
    timestamp = ma.auto_field(dump_only=True)
    author = ma.Nested(UserSchema, dump_only=True)


class TokenSchema(ma.Schema):
    class Meta:
        ordered = True

    access_token = ma.String(required=True)
    refresh_token = ma.String(required=True)


class PasswordResetRequestSchema(ma.Schema):
    class Meta:
        ordered = True

    email = ma.String(required=True)


class PasswordResetSchema(ma.Schema):
    class Meta:
        ordered = True

    token = ma.String(required=True)
    new_password = ma.String(required=True)
