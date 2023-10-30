from importlib import import_module
from alembic import context
from alchemical.alembic.env import run_migrations
from microblog import app

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# import the application's Alchemical instance
try:
    import_mod, db_name = config.get_main_option('alchemical_db', '').split(
        ':')
    db = getattr(import_module(import_mod), db_name)
except (ModuleNotFoundError, AttributeError):
    raise ValueError(
        'Could not import the Alchemical database instance. '
        'Ensure that the alchemical_db setting in alembic.ini is correct.'
    )

# run the migration engine
# The dictionary provided as second argument includes options to pass to the
# Alembic context. For details on what other options are available, see
# https://alembic.sqlalchemy.org/en/latest/autogenerate.html
run_migrations(db, {
    'render_as_batch': True,
    'compare_type': True,
})
