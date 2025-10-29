from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Session, select
from database import engine, get_session
from models import Estudiante, Curso, Matricula

# Constantes de reglas de negocio
CREDITOS_MAXIMOS_POR_SEMESTRE = 20

app = FastAPI(
    title="Sistema Universidad API",
    version="1.0",
    description="""
    API REST para la gestión académica de una universidad.

    ## Funcionalidades

    * **Estudiantes**: Registro, consulta, actualización y eliminación de estudiantes
    * **Cursos**: Gestión completa del catálogo de cursos
    * **Matrículas**: Sistema de inscripción y desmatriculación de estudiantes en cursos

    ## Reglas de Negocio

    * Cada estudiante tiene una cédula única
    * Cada curso tiene un código único
    * Un estudiante no puede matricularse dos veces en el mismo curso
    * Un estudiante no puede tener dos cursos a la misma hora
    * Un estudiante no puede matricularse en más de 20 créditos por semestre
    * Cada curso tiene una capacidad máxima de estudiantes
    * La eliminación de estudiantes o cursos elimina sus matrículas asociadas
    """,
    contact={
        "name": "Danskers",
        "url": "https://github.com/Danskers/sistema-Universidad-API",
    }
)


@app.on_event("startup")
def on_startup():
    """Crea las tablas en la base de datos al iniciar la aplicación"""
    SQLModel.metadata.create_all(engine)


# ---------- MANEJO GLOBAL DE ERRORES ----------
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    """Maneja las excepciones HTTP de forma estandarizada"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail},
    )


@app.exception_handler(Exception)
def general_exception_handler(request: Request, exc: Exception):
    """Maneja cualquier excepción no controlada"""
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": str(exc)},
    )


# ---------- FUNCIONES AUXILIARES ----------
def horarios_conflicto(horario1: str, horario2: str) -> bool:
    """
    Verifica si dos horarios se sobreponen.

    Args:
        horario1: Horario en formato "HH:MM-HH:MM"
        horario2: Horario en formato "HH:MM-HH:MM"

    Returns:
        True si hay conflicto, False si no hay sobreposicion
    """

    def a_minutos(hora_str: str) -> int:
        """Convierte HH:MM a minutos desde medianoche"""
        h, m = map(int, hora_str.split(":"))
        return h * 60 + m

    # Parsear horario1
    inicio1_str, fin1_str = horario1.split("-")
    inicio1 = a_minutos(inicio1_str)
    fin1 = a_minutos(fin1_str)

    # Parsear horario2
    inicio2_str, fin2_str = horario2.split("-")
    inicio2 = a_minutos(inicio2_str)
    fin2 = a_minutos(fin2_str)

    # Verificar solapamiento: hay conflicto si inicio1 < fin2 AND inicio2 < fin1
    return inicio1 < fin2 and inicio2 < fin1


# ----------------- ESTUDIANTES -----------------
@app.post(
    "/estudiantes",
    status_code=201,
    summary="Crear un nuevo estudiante",
    description="Registra un nuevo estudiante en el sistema. La cédula debe ser única.",
    response_description="Estudiante creado exitosamente",
    tags=["Estudiantes"]
)
def crear_estudiante(estudiante: Estudiante, session: Session = Depends(get_session)):
    """
    Crea un nuevo estudiante con la siguiente información:

    - **cedula**: Número de identificación único (5-15 caracteres)
    - **nombre**: Nombre completo del estudiante (mínimo 2 caracteres)
    - **email**: Correo electrónico válido
    - **semestre**: Semestre actual (1-10)

    **Validaciones:**
    - La cédula no puede estar duplicada
    - Todos los campos son obligatorios
    """
    existente = session.exec(select(Estudiante).where(Estudiante.cedula == estudiante.cedula)).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un estudiante con esa cédula")
    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)
    return {"status": "success", "message": "Estudiante creado correctamente", "data": estudiante}


@app.get(
    "/estudiantes",
    summary="Listar estudiantes",
    description="Obtiene la lista de todos los estudiantes. Permite filtrar por semestre o código de curso.",
    response_description="Lista de estudiantes",
    tags=["Estudiantes"]
)
def listar_estudiantes(
        semestre: int | None = None,
        codigo: str | None = None,
        session: Session = Depends(get_session)
):
    """
    Retorna todos los estudiantes registrados en el sistema.

    **Parámetros opcionales:**
    - **semestre**: Filtra estudiantes por semestre específico (1-10)
    - **codigo**: Filtra estudiantes matriculados en un curso con ese código

    **Ejemplos:**
    - `/estudiantes?semestre=3` - Estudiantes de 3er semestre
    - `/estudiantes?codigo=MAT101` - Estudiantes matriculados en el curso MAT101
    - `/estudiantes?semestre=3&codigo=MAT101` - Estudiantes de 3er semestre en MAT101
    """
    query = select(Estudiante)

    # Filtro por semestre
    if semestre:
        query = query.where(Estudiante.semestre == semestre)

    # Filtro por código de curso
    if codigo:
        # Primero buscar el curso por código
        curso = session.exec(select(Curso).where(Curso.codigo == codigo)).first()
        if not curso:
            raise HTTPException(status_code=404, detail=f"No existe un curso con código {codigo}")

        # Filtrar estudiantes matriculados en ese curso
        query = query.join(Matricula).where(Matricula.curso_id == curso.id)

    estudiantes = session.exec(query).all()
    return {"status": "success", "count": len(estudiantes), "data": estudiantes}


@app.get(
    "/estudiantes/{estudiante_id}",
    summary="Obtener un estudiante",
    description="Obtiene la información detallada de un estudiante incluyendo sus cursos matriculados.",
    response_description="Información del estudiante y sus cursos",
    tags=["Estudiantes"]
)
def obtener_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    """
    Busca un estudiante por su ID y retorna:
    - Información personal del estudiante
    - Lista de cursos en los que está matriculado

    **Parámetros:**
    - **estudiante_id**: ID del estudiante a buscar
    """
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    cursos = session.exec(
        select(Curso).join(Matricula).where(Matricula.estudiante_id == estudiante_id)
    ).all()
    return {"status": "success", "estudiante": estudiante, "cursos_matriculados": cursos}


@app.put(
    "/estudiantes/{estudiante_id}",
    summary="Actualizar un estudiante",
    description="Actualiza la información de un estudiante existente. Solo se actualizan los campos enviados.",
    response_description="Estudiante actualizado",
    tags=["Estudiantes"]
)
def actualizar_estudiante(
        estudiante_id: int,
        data: Estudiante,
        session: Session = Depends(get_session)
):
    """
    Actualiza parcial o totalmente la información de un estudiante.

    **Parámetros:**
    - **estudiante_id**: ID del estudiante a actualizar

    **Nota:** Solo envía los campos que deseas modificar. Los campos no enviados
    permanecerán sin cambios.
    """
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(estudiante, key, value)
    session.add(estudiante)
    session.commit()
    session.refresh(estudiante)
    return {"status": "success", "message": "Estudiante actualizado", "data": estudiante}


@app.delete(
    "/estudiantes/{estudiante_id}",
    summary="Eliminar un estudiante",
    description="Elimina un estudiante y todas sus matrículas asociadas del sistema.",
    response_description="Estudiante eliminado exitosamente",
    tags=["Estudiantes"]
)
def eliminar_estudiante(estudiante_id: int, session: Session = Depends(get_session)):
    """
    Elimina permanentemente un estudiante del sistema.

    **Advertencia:** Esta acción también eliminará todas las matrículas del estudiante
    y es irreversible.

    **Parámetros:**
    - **estudiante_id**: ID del estudiante a eliminar
    """
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    matriculas = session.exec(select(Matricula).where(Matricula.estudiante_id == estudiante_id)).all()
    for m in matriculas:
        session.delete(m)
    session.delete(estudiante)
    session.commit()
    return {"status": "success", "message": "Estudiante y matrículas eliminados"}


@app.post(
    "/estudiantes/{estudiante_id}/cancelar-semestre",
    summary="Cancelar semestre de un estudiante",
    description="Desmatricula al estudiante de todos sus cursos actuales (cancelación de semestre).",
    response_description="Semestre cancelado exitosamente",
    tags=["Estudiantes"]
)
def cancelar_semestre(estudiante_id: int, session: Session = Depends(get_session)):
    """
    Cancela el semestre actual del estudiante eliminando todas sus matrículas.

    Esta operación es útil cuando un estudiante decide retirarse temporalmente
    o cancelar su inscripción semestral completa.

    **Parámetros:**
    - **estudiante_id**: ID del estudiante que cancela el semestre

    **Nota:** El estudiante permanece en el sistema, solo se eliminan sus matrículas.
    """
    estudiante = session.get(Estudiante, estudiante_id)
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    matriculas = session.exec(select(Matricula).where(Matricula.estudiante_id == estudiante_id)).all()
    if not matriculas:
        raise HTTPException(status_code=400, detail="El estudiante no tiene materias matriculadas")
    for m in matriculas:
        session.delete(m)
    session.commit()
    return {"status": "success", "message": f"El estudiante {estudiante.nombre} canceló el semestre"}


# ----------------- CURSOS -----------------
@app.post(
    "/cursos",
    status_code=201,
    summary="Crear un nuevo curso",
    description="Registra un nuevo curso en el catálogo académico. El código debe ser único.",
    response_description="Curso creado exitosamente",
    tags=["Cursos"]
)
def crear_curso(curso: Curso, session: Session = Depends(get_session)):
    """
    Crea un nuevo curso con la siguiente información:

    - **codigo**: Código único del curso (4-10 caracteres, ej: MAT101)
    - **nombre**: Nombre descriptivo del curso
    - **creditos**: Número de créditos académicos (1-10)
    - **horario**: Horario de clase en formato HH:MM-HH:MM (ej: 07:00-09:00)
    - **cupo_maximo**: Capacidad máxima de estudiantes (1-100)

    **Validaciones del horario:**
    - Debe estar entre 07:00 y 22:00
    - Duración mínima: 1 hora
    - Duración máxima: 4 horas
    """
    existente = session.exec(select(Curso).where(Curso.codigo == curso.codigo)).first()
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe un curso con ese código")
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return {"status": "success", "message": "Curso creado correctamente", "data": curso}


@app.get(
    "/cursos",
    summary="Listar cursos",
    description="Obtiene el catálogo de cursos. Permite filtrar por código o créditos.",
    response_description="Lista de cursos",
    tags=["Cursos"]
)
def listar_cursos(
        codigo: str | None = None,
        creditos: int | None = None,
        session: Session = Depends(get_session)
):
    """
    Retorna todos los cursos disponibles en el catálogo.

    **Parámetros opcionales:**
    - **codigo**: Filtra por código exacto del curso
    - **creditos**: Filtra cursos por número de créditos

    **Ejemplos:**
    - `/cursos?codigo=MAT101` - Busca el curso con código MAT101
    - `/cursos?creditos=4` - Lista todos los cursos de 4 créditos
    """
    query = select(Curso)
    if codigo:
        query = query.where(Curso.codigo == codigo)
    if creditos:
        query = query.where(Curso.creditos == creditos)
    cursos = session.exec(query).all()
    return {"status": "success", "count": len(cursos), "data": cursos}


@app.get(
    "/cursos/{curso_id}",
    summary="Obtener un curso",
    description="Obtiene la información detallada de un curso incluyendo los estudiantes inscritos.",
    response_description="Información del curso y sus estudiantes",
    tags=["Cursos"]
)
def obtener_curso(curso_id: int, session: Session = Depends(get_session)):
    """
    Busca un curso por su ID y retorna:
    - Información completa del curso
    - Lista de estudiantes inscritos actualmente

    **Parámetros:**
    - **curso_id**: ID del curso a buscar
    """
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    estudiantes = session.exec(
            select(Estudiante).join(Matricula).where(Matricula.curso_id == curso_id)
    ).all()
    return {"status": "success", "curso": curso, "estudiantes_inscritos": estudiantes}


@app.put(
    "/cursos/{curso_id}",
    summary="Actualizar un curso",
    description="Actualiza la información de un curso existente. Solo se actualizan los campos enviados.",
    response_description="Curso actualizado",
    tags=["Cursos"]
)
def actualizar_curso(
        curso_id: int,
        data: Curso,
        session: Session = Depends(get_session)
):
    """
    Actualiza parcial o totalmente la información de un curso.

    **Parámetros:**
    - **curso_id**: ID del curso a actualizar

    **Nota:** Solo envía los campos que deseas modificar. Los campos no enviados
    permanecerán sin cambios.
    """
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(curso, key, value)
    session.add(curso)
    session.commit()
    session.refresh(curso)
    return {"status": "success", "message": "Curso actualizado", "data": curso}


@app.delete(
    "/cursos/{curso_id}",
    summary="Eliminar un curso",
    description="Elimina un curso y todas las matrículas asociadas del sistema.",
    response_description="Curso eliminado exitosamente",
    tags=["Cursos"]
)
def eliminar_curso(curso_id: int, session: Session = Depends(get_session)):
    """
    Elimina permanentemente un curso del catálogo.

    **Advertencia:** Esta acción también eliminará todas las matrículas de estudiantes
    en este curso y es irreversible.

    **Parámetros:**
    - **curso_id**: ID del curso a eliminar
    """
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    matriculas = session.exec(select(Matricula).where(Matricula.curso_id == curso_id)).all()
    for m in matriculas:
        session.delete(m)
    session.delete(curso)
    session.commit()
    return {"status": "success", "message": "Curso eliminado correctamente"}


# ----------------- MATRÍCULAS -----------------
@app.post(
    "/matriculas",
    status_code=201,
    summary="Matricular estudiante en curso",
    description="Inscribe a un estudiante en un curso específico con múltiples validaciones.",
    response_description="Matrícula realizada exitosamente",
    tags=["Matrículas"]
)
def matricular_estudiante(
        estudiante_id: int,
        curso_id: int,
        session: Session = Depends(get_session)
):
    """
    Matricula (inscribe) a un estudiante en un curso.

    **Parámetros de consulta:**
    - **estudiante_id**: ID del estudiante a matricular
    - **curso_id**: ID del curso en el que se inscribirá

    **Validaciones:**
    - El estudiante y el curso deben existir
    - El estudiante no puede estar matriculado dos veces en el mismo curso
    - El estudiante no puede exceder 20 créditos por semestre
    - El curso no puede exceder su capacidad máxima
    - El estudiante no puede tener dos cursos a la misma hora (conflicto de horario)

    **Ejemplo de uso:**
    ```
    POST /matriculas?estudiante_id=1&curso_id=5
    ```
    """
    # Validación : Verificar que estudiante y curso existan
    estudiante = session.get(Estudiante, estudiante_id)
    curso_nuevo = session.get(Curso, curso_id)

    if not estudiante or not curso_nuevo:
        raise HTTPException(status_code=404, detail="Estudiante o curso no encontrado")

    # Validación : Verificar si ya está matriculado
    existe = session.exec(
        select(Matricula).where(
            (Matricula.estudiante_id == estudiante_id) & (Matricula.curso_id == curso_id)
        )
    ).first()

    if existe:
        raise HTTPException(status_code=409, detail="El estudiante ya está matriculado en este curso")

    # Validación 3: NUEVA - Verificar límite de créditos por semestre
    cursos_actuales = session.exec(
        select(Curso).join(Matricula).where(Matricula.estudiante_id == estudiante_id)
    ).all()

    creditos_actuales = sum(curso.creditos for curso in cursos_actuales)
    creditos_totales = creditos_actuales + curso_nuevo.creditos

    if creditos_totales > CREDITOS_MAXIMOS_POR_SEMESTRE:
        raise HTTPException(
            status_code=400,
            detail=f"Límite de créditos excedido. Actualmente tienes {creditos_actuales} créditos, "
        )

    # Validación: Verificar capacidad máxima del curso
    matriculas_curso = session.exec(
        select(Matricula).where(Matricula.curso_id == curso_id)
    ).all()

    estudiantes_inscritos = len(matriculas_curso)

    if estudiantes_inscritos >= curso_nuevo.cupo_maximo:
        raise HTTPException(
            status_code=409,
            detail=f"El curso '{curso_nuevo.nombre}' está lleno. "
                   f"Capacidad: {estudiantes_inscritos}/{curso_nuevo.cupo_maximo} estudiantes."
        )

    # Validación: Verificar conflictos de horario
    for curso_actual in cursos_actuales:
        if horarios_conflicto(curso_actual.horario, curso_nuevo.horario):
            raise HTTPException(
                status_code=409,
                detail=f"Conflicto de horario: el estudiante ya tiene el curso '{curso_actual.nombre}' "
                       f"en el horario {curso_actual.horario}, que se solapa con {curso_nuevo.horario}"
            )

    # Si pasa validaciones, crear matrícula
    matricula = Matricula(estudiante_id=estudiante_id, curso_id=curso_id)
    session.add(matricula)
    session.commit()
    return {"status": "success", "message": "Estudiante matriculado correctamente"}


@app.delete(
    "/matriculas",
    summary="Desmatricular estudiante de curso",
    description="Retira a un estudiante de un curso específico.",
    response_description="Desmatrícula realizada exitosamente",
    tags=["Matrículas"]
)
def desmatricular_estudiante(
        estudiante_id: int,
        curso_id: int,
        session: Session = Depends(get_session)
):
    """
    Desmatricula (retira) a un estudiante de un curso específico.

    **Parámetros de consulta:**
    - **estudiante_id**: ID del estudiante a desmatricular
    - **curso_id**: ID del curso del que se retirará

    **Nota:** Esta operación solo elimina la matrícula específica. El estudiante
    y el curso permanecen en el sistema.

    **Ejemplo de uso:**
    ```
    DELETE /matriculas?estudiante_id=1&curso_id=5
    ```
    """
    matricula = session.exec(
        select(Matricula).where(
            (Matricula.estudiante_id == estudiante_id) & (Matricula.curso_id == curso_id)
        )
    ).first()

    if not matricula:
        raise HTTPException(status_code=404, detail="La matrícula no existe")

    session.delete(matricula)
    session.commit()
    return {"status": "success", "message": "Estudiante desmatriculado correctamente"}