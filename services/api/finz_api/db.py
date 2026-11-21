from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def make_engine(url: str):
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 15})

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


def make_sessions(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
