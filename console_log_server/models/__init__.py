"""Domain models and ORM entities."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy Declarative Base."""

    pass


from .user import User  # noqa: E402  # pylint: disable=wrong-import-position
from .refresh_token import RefreshToken  # noqa: E402  # pylint: disable=wrong-import-position
from .room import Room  # noqa: E402  # pylint: disable=wrong-import-position

__all__ = ["Base", "User", "RefreshToken", "Room"]
