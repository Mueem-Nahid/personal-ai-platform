from __future__ import annotations

import time
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.exc import OperationalError

from core.config import settings
from database.base import Base
import models  # noqa: F401 — register all models for autogenerate

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", "+psycopg"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    connection = _connect_with_retry(connectable, max_retries=15, delay=2.0)
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def _connect_with_retry(engine, *, max_retries: int, delay: float):
    for attempt in range(1, max_retries + 1):
        try:
            return engine.connect()
        except OperationalError as e:
            msg = str(e.__cause__ or e)
            if attempt >= max_retries:
                raise
            print(f"Migration connection attempt {attempt}/{max_retries} failed — retrying in {delay}s: {msg}")
            time.sleep(delay)
    raise RuntimeError("unreachable")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
