import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


logger = logging.getLogger(__name__)


# --------------------------------------------------
# ENVIRONMENT
# --------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured in .env"
    )


# --------------------------------------------------
# SQLALCHEMY ENGINE
# --------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# --------------------------------------------------
# SESSION
# --------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# --------------------------------------------------
# BASE MODEL
# --------------------------------------------------

Base = declarative_base()


# --------------------------------------------------
# DATABASE SESSION
# --------------------------------------------------

def get_db_session():
    """
    Create a new database session.

    Caller must close the session after use.
    """

    return SessionLocal()


# --------------------------------------------------
# TEST CONNECTION
# --------------------------------------------------

def test_connection():
    """
    Test PostgreSQL connection.
    """

    from sqlalchemy import text

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT 1")
            )

            result.scalar()

        logger.info(
            "PostgreSQL connection successful."
        )

        return True

    except Exception:

        logger.exception(
            "PostgreSQL connection failed."
        )

        return False