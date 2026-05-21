# 📚 Framework de Calidad, Automatización y Migración de Datos
### Sistema de Gestión de Biblioteca Universitaria — Unisabaneta

Proyecto desarrollado para la materia de Calidad de Software. Consiste en un framework en Python que toma una base de datos PostgreSQL con diseño deficiente, la normaliza, la puebla masivamente, valida su integridad y migra todos los datos a MongoDB de forma automática.

---

## 🗂️ Estructura del Proyecto

```
Taller_framework_calidad/
├── main.py                   # Orquestador principal — ejecuta todas las fases
├── requirements.txt          # Dependencias del proyecto
├── config/
│   ├── config_calidad.json   # Reglas de validación de integridad
│   └── mapping_mongo.json    # Mapeo de columnas PostgreSQL → campos MongoDB
├── logs/
│   └── reporte_calidad.log   # Log generado automáticamente al correr el proyecto
└── src/
    ├── conexion_postgres.py  # Conexión a PostgreSQL
    ├── generador_datos.py    # Fase A: Poblamiento masivo con Faker
    ├── validator.py          # Fase B: Validación de calidad con JSON
    ├── executor_sql.py       # Fase C: Ejecución de objetos SQL (SP, Vista, Función)
    └── migracion_mongo.py    # Fase D: Migración automática a MongoDB
```

---

## ⚙️ Requisitos

- Python 3.13+
- PostgreSQL 17 con la base de datos `biblioteca_framework` restaurada
- MongoDB corriendo en `localhost:27017` (o MongoDB Atlas)

Instalar dependencias:
```bash
pip install psycopg2-binary pymongo faker
```

---

## 🚀 Cómo ejecutar

1. Clona el repositorio:
```bash
git clone https://github.com/Chopo0230/Taller_framework_calidad.git
cd Taller_framework_calidad
```

2. Asegúrate de que PostgreSQL y MongoDB estén corriendo.

3. Verifica que la contraseña en `src/conexion_postgres.py` coincida con tu instalación local.

4. Ejecuta el orquestador **desde la raíz del proyecto**:
```bash
python main.py
```

---

## 🔄 Fases del Framework

### Fase A — Poblamiento Masivo
Genera e inserta **250 registros** en cada tabla normalizada usando la librería `Faker` con localización en español colombiano. Pobla autores, categorías, editoriales, usuarios, libros, sedes, inventario, préstamos y reseñas.

### Fase B — Validación de Calidad
Lee las reglas definidas en `config/config_calidad.json` y valida:
- Que el correo de cada usuario contenga `@`
- Que la calificación de las reseñas esté entre 1 y 5
- Que el título de cada libro tenga mínimo 3 caracteres

Los errores se registran en `logs/reporte_calidad.log`.

### Fase C — Objetos de Base de Datos
Ejecuta desde Python los objetos SQL implementados en PostgreSQL:
- **Stored Procedures:** `insertar_libro`, `actualizar_libro`, `eliminar_libro`, `auditar_prestamos`
- **Vista:** `vista_libros_prestados` — muestra usuario, libro y fecha de préstamo
- **Función:** `calcular_multa(fecha)` — calcula la multa por retraso según la fecha actual

### Fase D — Migración a MongoDB
Lee `config/mapping_mongo.json` y migra las 10 tablas normalizadas de PostgreSQL a colecciones en MongoDB:

| PostgreSQL | MongoDB |
|---|---|
| autores | authors |
| categorias | categories |
| editoriales | publishers |
| usuarios | users |
| libros | books |
| sedes | branches |
| inventario | inventory |
| prestamos | loans |
| prestamo_detalle | loan_details |
| resenas | reviews |

Al finalizar genera un reporte con el total de registros extraídos e insertados.

---

## 📊 Resultado de la Migración

```
Total extraídos de PostgreSQL : 1825
Total insertados en MongoDB   : 1825
Registros con error           : 0
```

---

## 👨‍💻 Autores

- **Mateo Cardona Cañaveral**
- **Emmanuel Correa**

Tutor: Manolo Pájaro Borras  
Ingeniería Informática — Unisabaneta, 2026
