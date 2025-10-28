from sqlmodel import SQLModel, create_engine, Session
import os

# Configuración de la base de datos SQLite
sqlite_name = "database.db"
sqlite_path = os.path.join(os.path.dirname(__file__), sqlite_name)
engine = create_engine(f"sqlite:///{sqlite_path}", echo=False)


def crear_bd():
    """
    Crea todas las tablas en la base de datos.
    Importa los modelos para que SQLModel los registre.
    """
    from models import Estudiante, Curso, Matricula  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Generador que proporciona una sesión de base de datos.
    Se usa como dependencia en FastAPI.
    La sesión se cierra automáticamente al terminar.
    """
    with Session(engine) as session:
        yield session