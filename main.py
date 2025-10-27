from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from typing import Optional
from database import engine, crear_bd
from models import Estudiante, Curso

app = FastAPI()

crear_bd()

# ---------- ESTUDIANTES ----------
@app.post("/estudiantes/")
def crear_estudiante(estudiante: Estudiante):
    with Session(engine) as session:
        existe = session.exec(select(Estudiante).where(Estudiante.cedula == estudiante.cedula)).first()
        if existe:
            raise HTTPException(status_code=400, detail="Cédula ya registrada")
        session.add(estudiante)
        session.commit()
        session.refresh(estudiante)
        return estudiante


@app.get("/estudiantes/")
def listar_estudiantes(semestre: Optional[int] = None):
    with Session(engine) as session:
        query = select(Estudiante)
        if semestre:
            query = query.where(Estudiante.semestre == semestre)
        return session.exec(query).all()


@app.get("/estudiantes/{id}")
def obtener_estudiante(id: int):
    with Session(engine) as session:
        estudiante = session.get(Estudiante, id)
        if not estudiante:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return {"estudiante": estudiante, "cursos": estudiante.cursos}


@app.put("/estudiantes/{id}")
def actualizar_estudiante(id: int, data: Estudiante):
    with Session(engine) as session:
        estudiante = session.get(Estudiante, id)
        if not estudiante:
            raise HTTPException(status_code=404, detail="No encontrado")
        existe = session.exec(select(Estudiante).where(Estudiante.cedula == data.cedula, Estudiante.id != id)).first()
        if existe:
            raise HTTPException(status_code=400, detail="Cédula ya registrada en otro estudiante")
        estudiante.nombre = data.nombre
        estudiante.cedula = data.cedula
        estudiante.semestre = data.semestre
        session.add(estudiante)
        session.commit()
        session.refresh(estudiante)
        return estudiante


@app.delete("/estudiantes/{id}")
def eliminar_estudiante(id: int):
    with Session(engine) as session:
        estudiante = session.get(Estudiante, id)
        if not estudiante:
            raise HTTPException(status_code=404, detail="No encontrado")
        session.delete(estudiante)
        session.commit()
        return {"mensaje": "Estudiante eliminado y matrículas borradas"}


# ---------- CURSOS ----------
@app.post("/cursos/")
def crear_curso(curso: Curso):
    with Session(engine) as session:
        existe = session.exec(select(Curso).where(Curso.codigo == curso.codigo)).first()
        if existe:
            raise HTTPException(status_code=400, detail="Código de curso ya existente")
        session.add(curso)
        session.commit()
        session.refresh(curso)
        return curso


@app.get("/cursos/")
def listar_cursos(creditos: Optional[int] = None, codigo: Optional[str] = None):
    with Session(engine) as session:
        query = select(Curso)
        if creditos:
            query = query.where(Curso.creditos == creditos)
        if codigo:
            query = query.where(Curso.codigo == codigo)
        return session.exec(query).all()


@app.get("/cursos/{id}")
def obtener_curso(id: int):
    with Session(engine) as session:
        curso = session.get(Curso, id)
        if not curso:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
        return {"curso": curso, "estudiantes": curso.estudiantes}


@app.put("/cursos/{id}")
def actualizar_curso(id: int, data: Curso):
    with Session(engine) as session:
        curso = session.get(Curso, id)
        if not curso:
            raise HTTPException(status_code=404, detail="No encontrado")
        existe = session.exec(select(Curso).where(Curso.codigo == data.codigo, Curso.id != id)).first()
        if existe:
            raise HTTPException(status_code=400, detail="Código ya registrado en otro curso")
        curso.nombre = data.nombre
        curso.codigo = data.codigo
        curso.creditos = data.creditos
        session.add(curso)
        session.commit()
        session.refresh(curso)
        return curso


@app.delete("/cursos/{id}")
def eliminar_curso(id: int):
    with Session(engine) as session:
        curso = session.get(Curso, id)
        if not curso:
            raise HTTPException(status_code=404, detail="No encontrado")
        session.delete(curso)
        session.commit()
        return {"mensaje": "Curso eliminado y matrículas borradas"}


# ---------- MATRÍCULAS ----------
@app.post("/matricular/{id_estudiante}/{id_curso}")
def matricular_estudiante(id_estudiante: int, id_curso: int):
    with Session(engine) as session:
        est = session.get(Estudiante, id_estudiante)
        cur = session.get(Curso, id_curso)
        if not est or not cur:
            raise HTTPException(status_code=404, detail="Estudiante o curso no encontrado")
        if cur in est.cursos:
            raise HTTPException(status_code=400, detail="Ya está matriculado en este curso")
        est.cursos.append(cur)
        session.add(est)
        session.commit()
        return {"mensaje": f"{est.nombre} matriculado en {cur.nombre}"}


@app.delete("/desmatricular/{id_estudiante}/{id_curso}")
def desmatricular_estudiante(id_estudiante: int, id_curso: int):
    with Session(engine) as session:
        est = session.get(Estudiante, id_estudiante)
        cur = session.get(Curso, id_curso)
        if not est or not cur:
            raise HTTPException(status_code=404, detail="No encontrado")
        if cur in est.cursos:
            est.cursos.remove(cur)
            session.commit()
        return {"mensaje": "Desmatriculado correctamente"}


@app.delete("/cancelar_semestre/{id_estudiante}")
def cancelar_semestre(id_estudiante: int):
    with Session(engine) as session:
        est = session.get(Estudiante, id_estudiante)
        if not est:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        est.cursos.clear()
        session.commit()
        return {"mensaje": "Semestre cancelado"}


@app.get("/cursos_estudiante/{id_estudiante}")
def cursos_estudiante(id_estudiante: int):
    with Session(engine) as session:
        est = session.get(Estudiante, id_estudiante)
        if not est:
            raise HTTPException(status_code=404, detail="No encontrado")
        return est.cursos


@app.get("/estudiantes_curso/{id_curso}")
def estudiantes_curso(id_curso: int):
    with Session(engine) as session:
        cur = session.get(Curso, id_curso)
        if not cur:
            raise HTTPException(status_code=404, detail="No encontrado")
        return cur.estudiantes
