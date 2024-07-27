"""Initialize the database and handle corresponding logical setup."""

from typing import Self, Type
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import scoped_session, sessionmaker
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ENGINE: Engine = create_engine(f"sqlite:///{os.getenv('DB_PATH')}", echo=True)
Base: DeclarativeMeta = declarative_base()


class DBGlobalSession:
    """Defines a sinigleton to hold the database's active session after initializing."""

    # Instantiate a singleton object
    __instance = None
    _session_class: scoped_session = None

    def __new__(cls: Type["DBGlobalSession"]) -> "DBGlobalSession":
        """Handle creation of a new class instance.

        Because this is a singleton, we only want to create one instance of the class,
        and return that instance every time a new instance is requested.
        """
        if cls.__instance is None:
            cls.__instance = super(DBGlobalSession, cls).__new__(cls)
        return cls.__instance

    def __init__(self: Self) -> None:
        """Initialize this class instance."""
        pass

    def assign_session_class(self: Self, session_class: scoped_session) -> None:
        """Assign the session class to the singleton object."""
        self._session_class = session_class

    def new_session(self: Self) -> scoped_session:
        """Create a new session."""
        return self._session_class()


def init_db() -> None:
    """Initialize the database."""
    logger.info("Initializing database...")
    Base.metadata.create_all(ENGINE)
    logger.info("Creating session...")
    Session = sessionmaker(bind=ENGINE)
    session = scoped_session(Session)

    # Assign the session to the singleton object
    logger.info("Assigning session to the singleton object...")
    db_session = DBGlobalSession()
    db_session.assign_session_class(session)
    logger.info("Database initialized.")
