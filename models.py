from datetime import time
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr, validator

class Matricula(SQLModel, table=True):
    estudiante_id: Optional[int] = Field(default=None, foreign_key="estudiante.id", primary_key=True)
    curso_id: Optional[int] = Field(default=None, foreign_key="curso.id", primary_key=True)


class EstudianteBase(SQLModel):
    cedula: str = Field(index=True, unique=True, min_length=5, max_length=15)
    nombre: str = Field(min_length=2, max_length=50)
    email: EmailStr
    semestre: int = Field(gt=0, le=10, description="Debe estar entre 1 y 10")

    @validator("nombre")
    def nombre_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v


class Estudiante(EstudianteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cursos: List["Curso"] = Relationship(back_populates="estudiantes", link_model=Matricula)


class CursoBase(SQLModel):
    codigo: str = Field(index=True, unique=True, min_length=4, max_length=10)
    nombre: str = Field(min_length=2, max_length=50)
    creditos: int = Field(gt=0, le=10, description="Debe ser mayor que 0 y menor o igual a 10")
    horario: str = Field(min_length=3, max_length=30, description="Formato: HH:MM-HH:MM (ej. 07:00-09:00)")

    @validator("horario")
    def validar_horario(cls, v):
        try:
            inicio_str, fin_str = v.split("-")
            h_inicio = int(inicio_str.split(":")[0])
            h_fin = int(fin_str.split(":")[0])
        except Exception:
            raise ValueError("Formato de horario inválido. Use HH:MM-HH:MM")

        if h_inicio < 7 or h_fin > 22:
            raise ValueError("El horario debe estar entre 07:00 y 22:00")
        if h_fin - h_inicio != 2:
            raise ValueError("Cada clase debe durar exactamente 2 horas")
        return v


class Curso(CursoBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    estudiantes: List[Estudiante] = Relationship(back_populates="cursos", link_model=Matricula)



