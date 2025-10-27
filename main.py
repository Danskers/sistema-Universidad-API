from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Session, select
from database import engine, get_session
from models import Estudiante, Curso, Matricula

app = FastAPI(title="Sistema Universidad API", version="1.0")


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# ----------------- ESTUDIANTES -----------------
@app.post("/estudiantes", status_code=201)
def crear_estudiante(estudiante: Estudiante, session: Session = Depends(get_session)):
    existente = session.exec(select(Estudiante).where(Estudiante.cedula == estudiante.cedula)).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un estudiante con esa cédula")
    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)
    return {"message": "Estudiante creado correctamente", "data": estudiante}


@app.get("/estudiantes")
def listar_estudiantes(semestre: int | None = None, session: Session = Depends(get_session)):
    query = select(Estudiante)
    if semestre:
        query = query.where(Estudiante.semestre == semestre)
    estudiantes = session.exec(query).all()
    return {"count": len(estudiantes), "data": estudiantes}


@app.get("/estudiantes/{estudiante_id}")
def obtener_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    session.refresh(estudiante)
    cursos = session.exec(
        select(Curso).join(Matricula).where(Matricula.estudiante_id == estudiante_id)
    ).all()
    return {"estudiante": estudiante, "cursos_matriculados": cursos}


@app.put("/estudiantes/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, data: Estudiante, session: Session = Depends(get_session)):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(estudiante, key, value)

    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)
    return {"message": "Estudiante actualizado", "data": estudiante}


@app.delete("/estudiantes/{estudiante_id}")
def eliminar_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    # Eliminación en cascada: borra sus matrículas
    matriculas = session.exec(select(Matricula).where(Matricula.estudiante_id == estudiante_id)).all()
    for m in matriculas:
        session.delete(m)

    session.delete(estudiante)
    session.commit()
    return {"message": "Estudiante eliminado junto con sus matrículas"}


@app.delete("/estudiantes/{estudiante_id}/cancelar-semestre")
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
    return {"message": f"El estudiante {estudiante.nombre} ha cancelado el semestre y se eliminaron todas sus matrículas."}


# ----------------- CURSOS -----------------
@app.post("/cursos", status_code=201)
def crear_curso(curso: Curso, session: Session = Depends(get_session)):
    existente = session.exec(select(Curso).where(Curso.codigo == curso.codigo)).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un curso con ese código")
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return {"message": "Curso creado correctamente", "data": curso}


@app.get("/cursos")
def listar_cursos(codigo: str | None = None, creditos: int | None = None, session: Session = Depends(get_session)):
    query = select(Curso)
    if codigo:
        query = query.where(Curso.codigo == codigo)
    if creditos:
        query = query.where(Curso.creditos == creditos)
    cursos = session.exec(query).all()
    return {"count": len(cursos), "data": cursos}


@app.get("/cursos/{curso_id}")
def obtener_curso(curso_id: int, session: Session = Depends(get_session)):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    session.refresh(curso)
    estudiantes = session.exec(
        select(Estudiante).join(Matricula).where(Matricula.curso_id == curso_id)
    ).all()
    return {"curso": curso, "estudiantes_inscritos": estudiantes}


@app.put("/cursos/{curso_id}")
def actualizar_curso(curso_id: int, data: Curso, session: Session = Depends(get_session)):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(curso, key, value)

    session.add(curso)
    session.commit()
    session.refresh(curso)
    return {"message": "Curso actualizado", "data": curso}


@app.delete("/cursos/{curso_id}")
def eliminar_curso(curso_id: int, session: Session = Depends(get_session)):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    # Eliminación en cascada: borra matrículas asociadas
    matriculas = session.exec(select(Matricula).where(Matricula.curso_id == curso_id)).all()
    for m in matriculas:
        session.delete(m)

    session.delete(curso)
    session.commit()
    return {"message": "Curso y sus matrículas eliminados correctamente"}


# ----------------- MATRÍCULAS -----------------
@app.post("/matriculas", status_code=201)
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

    ya_matriculado = session.exec(
        select(Matricula).where(Matricula.estudiante_id == estudiante_id)
    ).first()
    if ya_matriculado:
        raise HTTPException(status_code=400, detail="El estudiante ya está matriculado en un curso y no puede tener más de uno a la vez")

    matricula = Matricula(estudiante_id=estudiante_id, curso_id=curso_id)
    session.add(matricula)
    session.commit()
    return {"message": "Estudiante matriculado correctamente", "estudiante_id": estudiante_id, "curso_id": curso_id}


@app.delete("/matriculas")
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
    return {"message": "Estudiante desmatriculado del curso correctamente"}
