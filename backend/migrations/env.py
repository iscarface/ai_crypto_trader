import os, sys
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base  # Import your SQLAlchemy models

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

config = context.config
DATABASE_URL = os.getenv("DATABASE_URL")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# Target metadata
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(DATABASE_URL)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
