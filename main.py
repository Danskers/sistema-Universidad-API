from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Session, select
from database import engine, get_session
from models import Estudiante, Curso, Matricula

app = FastAPI(
    title="Sistema Universidad API",
    version="1.0",
    description=(
        "API académica para la gestión de estudiantes, cursos y matrículas. "
        "Permite registrar, listar, actualizar y eliminar estudiantes y cursos, "
        "además de gestionar la relación muchos a muchos entre ellos."
    ),
)


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# ----------------- ESTUDIANTES -----------------
@app.post(
    "/estudiantes",
    status_code=201,
    tags=["Estudiantes"],
    summary="Registrar un nuevo estudiante",
    description="Crea un estudiante con su cédula, nombre, correo y semestre. La cédula y el correo deben ser únicos.",
)
def crear_estudiante(estudiante: Estudiante, session: Session = Depends(get_session)):
    existente = session.exec(select(Estudiante).where(Estudiante.cedula == estudiante.cedula)).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un estudiante con esa cédula")

    email_existente = session.exec(select(Estudiante).where(Estudiante.email == estudiante.email)).first()
    if email_existente:
        raise HTTPException(status_code=409, detail="Ya existe un estudiante con ese correo")

    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)
    return {"status": 201, "message": "Estudiante creado correctamente", "data": estudiante}


@app.get(
    "/estudiantes",
    tags=["Estudiantes"],
    summary="Listar estudiantes",
    description="Devuelve todos los estudiantes registrados. Se puede filtrar por semestre.",
)
def listar_estudiantes(semestre: int | None = None, session: Session = Depends(get_session)):
    query = select(Estudiante)
    if semestre:
        query = query.where(Estudiante.semestre == semestre)
    estudiantes = session.exec(query).all()
    return {"status": 200, "count": len(estudiantes), "data": estudiantes}


@app.get(
    "/estudiantes/{estudiante_id}",
    tags=["Estudiantes"],
    summary="Obtener estudiante con cursos",
    description="Devuelve la información del estudiante y los cursos en los que está matriculado.",
)
def obtener_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    session.refresh(estudiante)
    cursos = session.exec(
        select(Curso).join(Matricula).where(Matricula.estudiante_id == estudiante_id)
    ).all()
    return {"status": 200, "estudiante": estudiante, "cursos_matriculados": cursos}


@app.put(
    "/estudiantes/{estudiante_id}",
    tags=["Estudiantes"],
    summary="Actualizar estudiante",
    description="Actualiza los datos del estudiante existente.",
)
def actualizar_estudiante(estudiante_id: int, data: Estudiante, session: Session = Depends(get_session)):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(estudiante, key, value)

    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)
    return {"status": 200, "message": "Estudiante actualizado", "data": estudiante}


@app.delete(
    "/estudiantes/{estudiante_id}",
    tags=["Estudiantes"],
    summary="Eliminar estudiante",
    description="Elimina un estudiante y todas sus matrículas asociadas.",
)
def eliminar_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    matriculas = session.exec(select(Matricula).where(Matricula.estudiante_id == estudiante_id)).all()
    for m in matriculas:
        session.delete(m)

    session.delete(estudiante)
    session.commit()
    return {"status": 200, "message": "Estudiante eliminado junto con sus matrículas"}


@app.delete(
    "/estudiantes/{estudiante_id}/cancelar-semestre",
    tags=["Estudiantes"],
    summary="Cancelar semestre",
    description="Elimina todas las matrículas del estudiante, pero mantiene su registro en el sistema.",
)
def cancelar_semestre(estudiante_id: int, session: Session = Depends(get_session)):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    matriculas = session.exec(select(Matricula).where(Matricula.estudiante_id == estudiante_id)).all()
    if not matriculas:
        raise HTTPException(status_code=400, detail="El estudiante no tiene materias matriculadas")

    for m in matriculas:
        session.delete(m)

    session.commit()
    return {"status": 200, "message": f"El estudiante {estudiante.nombre} ha cancelado el semestre."}


# ----------------- CURSOS -----------------
@app.post(
    "/cursos",
    status_code=201,
    tags=["Cursos"],
    summary="Registrar curso",
    description="Crea un curso nuevo con su código, nombre, créditos y horario.",
)
def crear_curso(curso: Curso, session: Session = Depends(get_session)):
    existente = session.exec(select(Curso).where(Curso.codigo == curso.codigo)).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un curso con ese código")
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return {"status": 201, "message": "Curso creado correctamente", "data": curso}


@app.get(
    "/cursos",
    tags=["Cursos"],
    summary="Listar cursos",
    description="Devuelve todos los cursos. Permite filtrar por código o número de créditos.",
)
def listar_cursos(codigo: str | None = None, creditos: int | None = None, session: Session = Depends(get_session)):
    query = select(Curso)
    if codigo:
        query = query.where(Curso.codigo == codigo)
    if creditos:
        query = query.where(Curso.creditos == creditos)
    cursos = session.exec(query).all()
    return {"status": 200, "count": len(cursos), "data": cursos}


@app.get(
    "/cursos/{curso_id}",
    tags=["Cursos"],
    summary="Obtener curso con estudiantes",
    description="Devuelve la información de un curso y la lista de estudiantes inscritos.",
)
def obtener_curso(curso_id: int, session: Session = Depends(get_session)):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    session.refresh(curso)
    estudiantes = session.exec(
        select(Estudiante).join(Matricula).where(Matricula.curso_id == curso_id)
    ).all()
    return {"status": 200, "curso": curso, "estudiantes_inscritos": estudiantes}


@app.put(
    "/cursos/{curso_id}",
    tags=["Cursos"],
    summary="Actualizar curso",
    description="Actualiza los datos de un curso existente.",
)
def actualizar_curso(curso_id: int, data: Curso, session: Session = Depends(get_session)):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(curso, key, value)

    session.add(curso)
    session.commit()
    session.refresh(curso)
    return {"status": 200, "message": "Curso actualizado", "data": curso}


@app.delete(
    "/cursos/{curso_id}",
    tags=["Cursos"],
    summary="Eliminar curso",
    description="Elimina un curso y todas las matrículas asociadas a él.",
)
def eliminar_curso(curso_id: int, session: Session = Depends(get_session)):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    matriculas = session.exec(select(Matricula).where(Matricula.curso_id == curso_id)).all()
    for m in matriculas:
        session.delete(m)

    session.delete(curso)
    session.commit()
    return {"status": 200, "message": "Curso y sus matrículas eliminados correctamente"}


# ----------------- MATRÍCULAS -----------------
@app.post(
    "/matriculas",
    status_code=201,
    tags=["Matrículas"],
    summary="Matricular estudiante en curso",
    description="Asocia un estudiante a un curso. Verifica duplicados y límites de estudiantes.",
)
def matricular_estudiante(estudiante_id: int, curso_id: int, session: Session = Depends(get_session)):
    estudiante = session.get(Estudiante, estudiante_id)
    curso = session.get(Curso, curso_id)
    if not estudiante or not curso:
        raise HTTPException(status_code=404, detail="Estudiante o curso no encontrado")

    existe = session.exec(
        select(Matricula).where(
            (Matricula.estudiante_id == estudiante_id) & (Matricula.curso_id == curso_id)
        )
    ).first()
    if existe:
        raise HTTPException(status_code=409, detail="El estudiante ya está matriculado en este curso")

    matriculas_curso = session.exec(select(Matricula).where(Matricula.curso_id == curso_id)).all()
    if len(matriculas_curso) >= 30:
        raise HTTPException(status_code=400, detail="El curso ya alcanzó el máximo de 30 estudiantes")

    cursos_estudiante = session.exec(
        select(Curso).join(Matricula).where(Matricula.estudiante_id == estudiante_id)
    ).all()
    for c in cursos_estudiante:
        if c.horario == curso.horario:
            raise HTTPException(status_code=400, detail="El estudiante ya tiene una materia en ese horario")

    matricula = Matricula(estudiante_id=estudiante_id, curso_id=curso_id)
    session.add(matricula)
    session.commit()
    return {"status": 201, "message": "Estudiante matriculado correctamente", "estudiante_id": estudiante_id, "curso_id": curso_id}


@app.delete(
    "/matriculas",
    tags=["Matrículas"],
    summary="Desmatricular estudiante de un curso",
    description="Elimina la matrícula específica entre un estudiante y un curso.",
)
def desmatricular_estudiante(estudiante_id: int, curso_id: int, session: Session = Depends(get_session)):
    matricula = session.exec(
        select(Matricula).where(
            (Matricula.estudiante_id == estudiante_id) & (Matricula.curso_id == curso_id)
        )
    ).first()
    if not matricula:
        raise HTTPException(status_code=404, detail="La matrícula no existe")

    session.delete(matricula)
    session.commit()
    return {"status": 200, "message": "Estudiante desmatriculado del curso correctamente"}
