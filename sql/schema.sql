-- ============================================================
-- SCHEMA.SQL — Biblioteca Universitaria
-- Tablas legacy (sucias) + Tablas normalizadas
-- ============================================================

-- ── TABLAS LEGACY (sucias) — para demostrar errores ─────────

CREATE TABLE IF NOT EXISTS Biblioteca_Data (
    id_registro         SERIAL PRIMARY KEY,
    titulo_libro        VARCHAR(255),
    autor_nombre        VARCHAR(255),
    categoria_y_descripcion TEXT,          -- viola 1FN (campo combinado)
    editorial_info      VARCHAR(255),
    fecha_publicacion   VARCHAR(50)        -- tipo incorrecto (debería ser DATE)
);

CREATE TABLE IF NOT EXISTS Prestamos_Crudos (
    id_prestamo         SERIAL PRIMARY KEY,
    nombre_usuario      VARCHAR(255),
    correo_usuario      VARCHAR(255),
    libros_prestados    TEXT,              -- viola 1FN (lista separada por comas)
    fecha_salida        VARCHAR(50),       -- tipo incorrecto
    estado_prestamo     VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS Inventario_Sedes (
    id_inventario       SERIAL PRIMARY KEY,
    sede_nombre         VARCHAR(100),
    ubicacion_sede      VARCHAR(255),
    libro_asociado      VARCHAR(255),
    cantidad_total      VARCHAR(20)        -- tipo incorrecto (debería ser INT)
);

CREATE TABLE IF NOT EXISTS Resenas_Usuarios (
    id_resena           SERIAL PRIMARY KEY,
    usuario_id          VARCHAR(50),       -- tipo incorrecto (mezcla INT y texto)
    libro_titulo        VARCHAR(255),
    comentario          TEXT,
    calificacion        VARCHAR(10)        -- tipo incorrecto (debería ser NUMERIC)
);

-- ── TABLAS NORMALIZADAS ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS Autores (
    id_autor    SERIAL PRIMARY KEY,
    nombre      VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Categorias (
    id_categoria    SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS Editoriales (
    id_editorial    SERIAL PRIMARY KEY,
    nombre          VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Libros (
    id_libro            SERIAL PRIMARY KEY,
    titulo              VARCHAR(255) NOT NULL,
    fecha_publicacion   DATE,
    id_autor            INT REFERENCES Autores(id_autor),
    id_categoria        INT REFERENCES Categorias(id_categoria),
    id_editorial        INT REFERENCES Editoriales(id_editorial)
);

CREATE TABLE IF NOT EXISTS Libros_Categorias_Secundarias (
    id_libro        INT REFERENCES Libros(id_libro),
    id_categoria    INT REFERENCES Categorias(id_categoria),
    PRIMARY KEY (id_libro, id_categoria)
);

CREATE TABLE IF NOT EXISTS Log_Calidad (
    id_log          SERIAL PRIMARY KEY,
    tabla_origen    VARCHAR(100),
    campo           VARCHAR(100),
    valor_original  TEXT,
    error_detectado TEXT,
    fecha_registro  TIMESTAMP DEFAULT NOW()
);