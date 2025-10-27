🧩 Archivo: README.md
# 🎓 Sistema Universidad API

API REST desarrollada con **FastAPI** y **SQLModel** para la gestión de **estudiantes, cursos y matrículas** en una universidad.

---

## 🚀 Características principales
- Registro, consulta, actualización y eliminación de **estudiantes** y **cursos**.
- Relación **N:M** entre estudiantes y cursos mediante una tabla de matrículas.
- **Validaciones Pydantic** y control de errores HTTP.
- Búsqueda filtrada de cursos y estudiantes.
- Reglas de negocio implementadas:
  1. Cédula única por estudiante.
  2. Código único por curso.
  3. Un estudiante no puede estar matriculado dos veces en el mismo curso.
  4. Eliminación en cascada (borra matrículas asociadas).

---

## 🧱 Tecnologías usadas
- Python 3.12+
- FastAPI
- SQLModel
- SQLite
- Uvicorn

---

## ⚙️ Instalación y ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/Danskers/sistema-Universidad-API.git
cd sistema-Universidad-API

2. Crear y activar entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux / macOS
# .venv\Scripts\activate   # Windows

3. Instalar dependencias
pip install -r requirements.txt

4. Ejecutar el servidor
uvicorn main:app --reload

5. Acceder a la documentación interactiva

Swagger UI → http://127.0.0.1:8000/docs

Redoc → http://127.0.0.1:8000/redoc

🧩 Estructura del proyecto
sistema-Universidad-API/
│
├── main.py           # Endpoints principales (FastAPI)
├── models.py         # Modelos y relaciones SQLModel
├── database.py       # Conexión y creación de la base de datos
├── requirements.txt  # Dependencias
├── .gitignore
└── README.md

✅ Estado actual

CRUD completo de estudiantes y cursos.

Relación N:M funcional.

Validaciones y reglas en desarrollo.

Pendiente: documentación extendida y validaciones avanzadas.

👨‍💻 Autor

Danskers
Repositorio: https://github.com/Danskers/sistema-Universidad-API