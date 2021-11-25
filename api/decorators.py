from functools import wraps
from flask import abort
from apifairy import arguments, response
import sqlalchemy as sqla
from api.app import db
from api.schemas import PaginationRequestSchema, PaginatedCollection


def paginated_response(schema, max_limit=10, model_from_statement=None):
    def inner(f):
        @wraps(f)
        def paginate(*args, **kwargs):
            args = list(args)
            pagination = args.pop(-1)
            select_query = f(*args, **kwargs)

            count = db.session.scalar(sqla.select(
                sqla.func.count()).select_from(select_query))

            offset = pagination.get('offset', 0)
            limit = pagination.get('limit', max_limit)
            if limit > max_limit:
                limit = max_limit

            if offset < 0 or (count > 0 and offset >= count) or limit <= 0:
                abort(400)

            if model_from_statement:
                data = db.session.scalars(
                    model_from_statement.select().from_statement(
                        select_query.limit(limit).offset(offset))).all()
            else:
                data = db.session.scalars(select_query.limit(limit).offset(
                    offset)).all()

            return {'data': data, 'pagination': {
                'offset': offset,
                'count': len(data),
                'total': count,
            }}

        # wrap with APIFairy's arguments and response decorators
        return arguments(PaginationRequestSchema)(response(PaginatedCollection(
            schema))(paginate))

    return inner
