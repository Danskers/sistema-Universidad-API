# 🎓 Sistema Universidad API

API REST desarrollada con **FastAPI** y **SQLModel** para la gestión académica de una universidad.  
Permite registrar estudiantes, crear cursos y realizar matrículas controlando cupos, créditos y conflictos de horario.

---

## 🚀 Características principales
- **Gestión completa de estudiantes y cursos** (crear, listar, editar y eliminar).  
- Relación **muchos a muchos (N:M)** entre estudiantes y cursos mediante la tabla `Matricula`.  
- **Validaciones automáticas** con Pydantic: formatos, rangos y unicidad.  
- **Reglas de negocio integradas**:
  1. Cédula única por estudiante.  
  2. Código único por curso.  
  3. Límite máximo de **20 créditos** por semestre.  
  4. Prohibición de horarios sobrepuestos.  
  5. Un curso no puede exceder su **cupo máximo**.  
  6. Eliminación de estudiantes o cursos borra sus matrículas asociadas.  
- **Control de errores HTTP** estandarizado (404, 400, 409, 500).  
- **Filtros** para consultar estudiantes por semestre o por código de curso.

---

## 🧱 Tecnologías usadas
- **Python 3.12+**  
- **FastAPI**  
- **SQLModel**  
- **SQLite**  
- **Uvicorn**

---

## ⚙️ Instalación y ejecución

### 1. Clonar el repositorio
```
git clone https://github.com/Danskers/sistema-Universidad-API.git
cd sistema-Universidad-API
```
### 2. Crear y activar entorno virtual 
```
python3 -m venv .venv
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate      # Windows
```

### 3. Instalar dependencias
```
pip install -r requirements.txt
```

### 4. Ejecutar el servidor
```
uvicorn main:app --reload
```

### 5. Acceder a la documentación interactiva

Swagger UI → http://127.0.0.1:8000/docs

Redoc → http://127.0.0.1:8000/redoc

## 🧩 Estructura del proyecto
```
sistema-Universidad-API/
│
├── main.py           # Endpoints y reglas de negocio
├── models.py         # Modelos SQLModel y validaciones Pydantic
├── database.py       # Configuración y sesión de base de datos SQLite
├── requirements.txt  # Dependencias del proyecto
├── .gitignore
└── README.md

```

## 🧭 Mapa de Endpoints

### 🎓 Estudiantes
| Método   | Endpoint                                         | Descripción                                                                      |
| :------- | :----------------------------------------------- | :------------------------------------------------------------------------------- |
| `POST`   | `/estudiantes`                                   | Crea un nuevo estudiante (valida cédula única).                                  |
| `GET`    | `/estudiantes`                                   | Lista todos los estudiantes, con filtros opcionales por semestre o curso.        |
| `GET`    | `/estudiantes/{estudiante_id}`                   | Muestra la información de un estudiante y sus cursos matriculados.               |
| `PUT`    | `/estudiantes/{estudiante_id}`                   | Actualiza los datos de un estudiante existente.                                  |
| `DELETE` | `/estudiantes/{estudiante_id}`                   | Elimina un estudiante y sus matrículas asociadas.                                |
| `POST`   | `/estudiantes/{estudiante_id}/cancelar-semestre` | Elimina todas las materias inscritas por el estudiante sin borrarlo del sistema. |

---

### 📘 Cursos
| Método   | Endpoint             | Descripción                                                                |
| :------- | :------------------- | :------------------------------------------------------------------------- |
| `POST`   | `/cursos`            | Crea un nuevo curso (valida código único y formato de horario).            |
| `GET`    | `/cursos`            | Lista los cursos disponibles, con filtros por código o número de créditos. |
| `GET`    | `/cursos/{curso_id}` | Muestra la información completa del curso y los estudiantes inscritos.     |
| `PUT`    | `/cursos/{curso_id}` | Actualiza la información de un curso existente.                            |
| `DELETE` | `/cursos/{curso_id}` | Elimina un curso y todas sus matrículas asociadas.                         |

---

### 🧾 Matrículas
| Método   | Endpoint                                       | Descripción                                                                              |
| :------- | :--------------------------------------------- | :--------------------------------------------------------------------------------------- |
| `POST`   | `/matriculas?estudiante_id={id}&curso_id={id}` | Matricula a un estudiante en un curso (verifica duplicados, créditos, cupos y horarios). |
| `DELETE` | `/matriculas?estudiante_id={id}&curso_id={id}` | Retira a un estudiante de un curso específico.                                           |
---

## 📦 Ejemplos de cuerpos JSON

➕ Crear Estudiante (POST /estudiantes)
```
{
  "cedula": "1002003004",
  "nombre": "María López",
  "email": "maria.lopez@example.com",
  "semestre": 4
}
```

➕ Crear Curso (POST /cursos)
```
{
  "codigo": "MAT101",
  "nombre": "Matemáticas Básicas",
  "creditos": 3,
  "horario": "08:00-10:00",
  "cupo_maximo": 30
}
```
---
## ✅ Estado actual

CRUD completo para estudiantes, cursos y matrículas.

Reglas de negocio implementadas.

Base de datos funcional y validada con SQLite.

Documentación automática en /docs.

---

## 👨‍💻 Autor

Danskers
Repositorio: https://github.com/Danskers/sistema-Universidad-API
