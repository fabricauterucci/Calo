from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - puede ser SQLite o PostgreSQL
# La base de datos está en el directorio raíz del proyecto
import os
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_db_path = os.path.join(_base_dir, 'propiedades.db')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{_db_path}')

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency para obtener sesión de DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
