from alembic import context
from sqlalchemy import engine_from_config, pool

from finz_api import models  # noqa: F401
from finz_api.config import database_url
from finz_api.db import Base

config = context.config
if not config.attributes.get("url_override"):
    config.set_main_option("sqlalchemy.url", database_url().replace("%", "%%"))
target_metadata = Base.metadata

if context.is_offline_mode():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
