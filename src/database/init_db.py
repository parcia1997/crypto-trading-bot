import logging

from src.database.db import (
    Base,
    engine,
    test_connection,
)

# Important:
# importing models registers the tables
# with SQLAlchemy Base.
from src.database import models


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(
    __name__
)


def main():

    logger.info(
        "Testing PostgreSQL connection..."
    )

    if not test_connection():

        raise RuntimeError(
            "Unable to connect to PostgreSQL."
        )

    logger.info(
        "Creating database tables..."
    )

    Base.metadata.create_all(
        bind=engine
    )

    logger.info(
        "Database tables created successfully."
    )


if __name__ == "__main__":

    main()