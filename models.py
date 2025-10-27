class Matricula(SQLModel, table=True):
    estudiante_id: Optional[int] = Field(default=None, foreign_key="estudiante.id", primary_key=True)
    curso_id: Optional[int] = Field(default=None, foreign_key="curso.id", primary_key=True)


class Estudiante(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("cedula"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    cedula: str
    semestre: int
    cursos: List["Curso"] = Relationship(back_populates="estudiantes", link_model=Matricula, sa_relationship_kwargs={"cascade": "all, delete"})


class Curso(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("codigo"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    codigo: str
    creditos: int
    estudiantes: List[Estudiante] = Relationship(back_populates="cursos", link_model=Matricula, sa_relationship_kwargs={"cascade": "all, delete"})
