from sqlmodel import SQLModel, create_engine
import os

sqlite_name = "database.db"
sqlite_path = os.path.join(os.path.dirname(__file__), sqlite_name)
engine = create_engine(f"sqlite:///{sqlite_path}", echo=False)

def crear_bd():

    from models import Estudiante, Curso, Matricula  # noqa: F401
    SQLModel.metadata.create_all(engine)
