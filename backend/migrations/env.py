from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.base import Base
from app.core.config import settings

# Import every module's models here so Alembic can see them.
import app.modules.audit.models  # noqa: F401
import app.modules.settings.models  # noqa: F401
import app.modules.iam.models  # noqa: F401
import app.modules.org.models  # noqa: F401
import app.modules.iam.rbac_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    """Ignore audit partition tables (audit_log_y2026m11, audit_log_default...).

    They are managed by migrations and a maintenance job, not by models.
    """
    if type_ == "table" and reflected and name.startswith("audit_log_"):
        return False
    return True


def run_migrations_offline() -> None:
    """Generate SQL without connecting to the database."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_object=include_object,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations to the configured database."""
    engine = create_engine(settings.database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()