"""
Lightweight, idempotent schema sync run on startup.

`Base.metadata.create_all` creates missing tables but never alters existing ones,
so columns added to a model later would be missing in databases created by an
older release. This adds any missing column using the model's type and
server_default. It never drops or modifies existing columns.
"""
import logging

from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.schema import CreateColumn

from app.database import Base

logger = logging.getLogger("job_agent.migrate")


def _add_missing_columns(conn: Connection) -> None:
    inspector = inspect(conn)
    existing_tables = set(inspector.get_table_names())

    for table in Base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_cols:
                continue
            if not column.nullable and column.server_default is None:
                logger.warning(
                    "Cannot auto-add NOT NULL column %s.%s without server_default",
                    table.name, column.name,
                )
                continue
            col_sql = CreateColumn(column).compile(dialect=conn.dialect)
            ddl = f"ALTER TABLE {table.name} ADD COLUMN {col_sql}"
            logger.info("Schema sync: %s", ddl)
            conn.exec_driver_sql(ddl)


def sync_schema(conn: Connection) -> None:
    Base.metadata.create_all(conn)
    _add_missing_columns(conn)
