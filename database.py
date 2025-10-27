from sqlmodel import SQLModel, Field, Session, create_engine, select, Relationship

sqlite_name = "database.db"
engine = create_engine(f"sqlite:///{sqlite_name}", echo=False)

def crear_bd():
    SQLModel.metadata.create_all(engine)

crear_bd()