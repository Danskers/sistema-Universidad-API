from sqlmodel import SQLModel, create_engine

sqlite_name = "database.db"
engine = create_engine(f"sqlite:///{sqlite_name}", echo=False)

def crear_bd():
    from models import Estudiante, Curso, Matricula
    SQLModel.metadata.create_all(engine)
