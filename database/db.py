"""Initialize the database and handle corresponding logical setup."""
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

Base.metadata.create_all(ENGINE)
Session = sessionmaker(bind=ENGINE)
session = scoped_session(Session)
