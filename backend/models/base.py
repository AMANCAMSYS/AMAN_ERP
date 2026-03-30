from sqlalchemy.orm import DeclarativeBase


class ModelBase(DeclarativeBase):
    """Base class for ORM models used by Alembic autogenerate."""

