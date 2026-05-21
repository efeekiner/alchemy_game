from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from apothecaria.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_session_iter() -> Iterator[Session]:
    """Yield a SQLAlchemy session that auto-commits on success and rolls back on error.

    Use this as a FastAPI ``Depends`` provider to inject a per-request DB session.
    :return: An open :class:`~sqlalchemy.orm.Session` (generator, for use with ``yield``).
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all ORM-mapped tables in the configured database.

    Use this at application startup or in test fixtures to ensure the schema
    exists before any queries run. Safe to call multiple times (no-op if tables
    already exist).
    """
    Base.metadata.create_all(engine)
