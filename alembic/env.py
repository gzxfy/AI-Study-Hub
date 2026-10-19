import logging
import os
from logging.config import fileConfig

from alembic import context
from flask import current_app


config = context.config
if config.config_file_name and os.path.exists(config.config_file_name):
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")
target_db = current_app.extensions["migrate"].db
target_metadata = (
    target_db.metadatas[None]
    if hasattr(target_db, "metadatas")
    else target_db.metadata
)
configure_args = dict(current_app.extensions["migrate"].configure_args)
config.set_main_option(
    "sqlalchemy.url",
    current_app.config["SQLALCHEMY_DATABASE_URI"].replace("%", "%%"),
)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **configure_args,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with target_db.engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            **configure_args,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
