from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr, field_validator


class Matricula(SQLModel, table=True):
    """Tabla intermedia para la relación N:M entre Estudiante y Curso"""
    estudiante_id: Optional[int] = Field(default=None, foreign_key="estudiante.id", primary_key=True)
    curso_id: Optional[int] = Field(default=None, foreign_key="curso.id", primary_key=True)


class EstudianteBase(SQLModel):
    """Modelo base para Estudiante con validaciones"""
    cedula: str = Field(index=True, unique=True, min_length=5, max_length=15)
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    semestre: int = Field(gt=0, le=10, description="Debe estar entre 1 y 10")

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v):
        """Valida que el nombre no esté vacío después de quitar espacios"""
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v.strip()


class Estudiante(EstudianteBase, table=True):
    """Modelo de Estudiante con relación a Cursos"""
    id: Optional[int] = Field(default=None, primary_key=True)
    cursos: List["Curso"] = Relationship(back_populates="estudiantes", link_model=Matricula)


class CursoBase(SQLModel):
    """Modelo base para Curso con validaciones"""
    codigo: str = Field(index=True, unique=True, min_length=4, max_length=10)
    nombre: str = Field(min_length=2, max_length=100)
    creditos: int = Field(gt=0, le=10, description="Debe ser mayor que 0 y menor o igual a 10")
    horario: str = Field(min_length=5, max_length=30, description="Formato: HH:MM-HH:MM (ej. 07:00-09:00)")

    @field_validator("horario")
    @classmethod
    def validar_horario(cls, v):
        """
        Valida que el horario tenga el formato correcto y esté dentro del rango permitido.
        - Formato: HH:MM-HH:MM
        - Rango: 07:00 a 22:00
        - Duración: 1 a 4 horas
        """
        try:
            inicio_str, fin_str = v.split("-")
            h_inicio, m_inicio = map(int, inicio_str.split(":"))
            h_fin, m_fin = map(int, fin_str.split(":"))
        except Exception:
            raise ValueError("Formato de horario inválido. Use HH:MM-HH:MM")

        if h_inicio < 7 or h_fin > 22:
            raise ValueError("El horario debe estar entre 07:00 y 22:00")

        # Calcular duración en minutos
        duracion = (h_fin * 60 + m_fin) - (h_inicio * 60 + m_inicio)
        if duracion <= 0:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        if duracion < 60:
            raise ValueError("La clase debe durar al menos 1 hora")
        if duracion > 240:
            raise ValueError("La clase no puede durar más de 4 horas")

        return v


class Curso(CursoBase, table=True):
    """Modelo de Curso con relación a Estudiantes"""
    id: Optional[int] = Field(default=None, primary_key=True)
    estudiantes: List[Estudiante] = Relationship(back_populates="cursos", link_model=Matricula)



