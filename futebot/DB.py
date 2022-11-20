from sqlalchemy import create_engine
from Models import Base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os


# SQLAlchemy requires postgresql:// instead of postgres://
DB_URL = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://")
engine = create_engine(DB_URL)

class DBSession(Session):
    success = False
    db_error = None
    error = None

@contextmanager
def db_session():
    session = DBSession(engine)
    session.success = False
    
    try:
        yield session
        session.commit()
        session.success = True
    except Exception as e:
        session.rollback()
        session.error = e
        if hasattr(e, 'orig'):
            session.db_error = e.orig
        # raise
    finally:
        session.close()

def recreate_database():
    drop_database()
    create_database()

def create_database():
    Base.metadata.create_all(engine)

def drop_database():
    Base.metadata.drop_all(engine)
