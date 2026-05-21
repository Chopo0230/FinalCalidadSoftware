"""
main.py - Orquestador principal
Framework de Calidad, Automatización y Migración de Datos
Biblioteca Universitaria - Unisabaneta
"""

import os
import re
import json
import hashlib
import datetime
import pandas as pd
import psycopg2
import psycopg2.extras
from pymongo import MongoClient
from thefuzz import fuzz
from faker import Faker

# ── CONFIGURACIÓN (lee variables de entorno de Docker) ───────
PG_CONFIG = {
    "host":     os.getenv("PG_HOST", "localhost"),
    "dbname":   os.getenv("PG_DB", "biblioteca_db"),
    "user":     os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", "Admin123*"),
    "port":     5432
}
MONGO_URI     = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = "biblioteca_nosql"
LOG_FILE      = "logs/reporte_calidad.log"
CONFIG_FILE   = "config/config_calidad.json"
EXCEL_FILE    = "config/Biblioteca_Normalizada_Final.xlsx"

fake = Faker("es_CO")

# ── UTILIDADES ───────────────────────────────────────────────
def conectar_postgres():
    return psycopg2.connect(**PG_CONFIG)

def conectar_mongo():
    cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return cliente, cliente[MONGO_DB_NAME]

def cargar_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def escribir_log(lineas):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")

def mask_email(email):
    """Aplica SHA-256 al correo (Data Masking)."""
    if not email:
        return None
    return hashlib.sha256(str(email).encode()).hexdigest()

def parsear_fecha(s):
    """Convierte múltiples formatos de fecha a YYYY-MM-DD."""
    if not s or str(s).strip() in ("N/A", "Desconocida", "Sin fecha", "nan"):
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(str(s).strip(), fmt).date()
        except:
            pass
    return None

def limpiar_texto(s):
    """Limpia espacios, tabs y normaliza mayúsculas."""
    if not s or str(s).strip() in ("nan", ""):
        return None
    return re.sub(r"\s+", " ", str(s).strip()).title()

# ── FASE A: POBLAMIENTO DE TABLAS LEGACY (sucias) ───────────
def fase_a_poblar_legacy(conn):
    print("\n" + "="*55)
    print("  FASE A: POBLAMIENTO TABLAS LEGACY")
    print("="*55)
    cur = conn.cursor()
    estados = ["ACTIVO", "DEVUELTO", "RETRASADO"]

    for _ in range(250):
        # Biblioteca_Data con errores intencionales
        cur.execute("""
            INSERT INTO Biblioteca_Data
                (titulo_libro, autor_nombre, categoria_y_descripcion,
                 editorial_info, fecha_publicacion)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            fake.sentence(nb_words=4),
            fake.name(),
            f"{fake.word().title()}; {fake.word().title()}",
            fake.company(),
            str(fake.date_between("-30y", "today"))
        ))

        # Prestamos_Crudos con correos rotos
        correo = fake.email() if fake.boolean(75) else fake.word()
        cur.execute("""
            INSERT INTO Prestamos_Crudos
                (nombre_usuario, correo_usuario, libros_prestados,
                 fecha_salida, estado_prestamo)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            fake.name(),
            correo,
            ", ".join(fake.sentence(nb_words=3) for _ in range(3)),
            str(fake.date_between("-1y", "today")),
            fake.random_element(estados)
        ))

        # Inventario_Sedes con cantidades inválidas
        cantidad = fake.random_element(
            [str(fake.random_int(1, 50)), "-5", "Diez", None]
        )
        cur.execute("""
            INSERT INTO Inventario_Sedes
                (sede_nombre, ubicacion_sede, libro_asociado, cantidad_total)
            VALUES (%s, %s, %s, %s)
        """, (
            fake.city(),
            fake.address(),
            fake.sentence(nb_words=3),
            cantidad
        ))

        # Resenas_Usuarios con calificaciones inválidas
        calif = fake.random_element(
            [str(fake.random_int(1, 5)), "5/5", "Cinco", "10/5"]
        )
        cur.execute("""
            INSERT INTO Resenas_Usuarios
                (usuario_id, libro_titulo, comentario, calificacion)
            VALUES (%s, %s, %s, %s)
        """, (
            fake.random_element(
                [str(fake.random_int(1, 500)), "Usuario_Desconocido", None]
            ),
            fake.sentence(nb_words=4),
            fake.paragraph(),
            calif
        ))

    conn.commit()
    cur.close()
    print("  ✔  250 registros insertados en tablas legacy.")

# ── FASE B: VALIDACIÓN CON config_calidad.json ───────────────
def fase_b_validar(conn, config):
    print("\n" + "="*55)
    print("  FASE B: VALIDACIÓN DE CALIDAD")
    print("="*55)
    cur = conn.cursor()
    errores = []
    reglas  = config["reglas"]

    # Validar Biblioteca_Data
    cur.execute("SELECT id_registro, titulo_libro, autor_nombre, fecha_publicacion FROM Biblioteca_Data")
    for fila in cur.fetchall():
        id_, titulo, autor, fecha = fila
        if not titulo or len(str(titulo).strip()) < 3:
            errores.append(f"[TITULO] Biblioteca_Data id={id_} titulo muy corto o nulo")
        if not autor:
            errores.append(f"[AUTOR] Biblioteca_Data id={id_} autor nulo")

    # Validar Resenas_Usuarios — calificación 1-5
    cur.execute("SELECT id_resena, calificacion FROM Resenas_Usuarios")
    for fila in cur.fetchall():
        id_, calif = fila
        try:
            val = float(str(calif).replace("/5","").strip())
            if not (1 <= val <= 5):
                raise ValueError
        except:
            errores.append(f"[CALIF] Resenas_Usuarios id={id_} calificacion invalida: '{calif}'")

    # Validar Prestamos_Crudos — correos
    patron_email = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
    cur.execute("SELECT id_prestamo, correo_usuario FROM Prestamos_Crudos")
    for fila in cur.fetchall():
        id_, correo = fila
        if not correo or not patron_email.match(str(correo)):
            errores.append(f"[EMAIL] Prestamos_Crudos id={id_} correo invalido: '{correo}'")

    # Validar Inventario_Sedes — cantidad_total >= 0
    cur.execute("SELECT id_inventario, cantidad_total FROM Inventario_Sedes")
    for fila in cur.fetchall():
        id_, cantidad = fila
        try:
            if int(str(cantidad)) < 0:
                raise ValueError
        except:
            errores.append(f"[CANTIDAD] Inventario_Sedes id={id_} cantidad invalida: '{cantidad}'")

    cur.close()
    print(f"  ✔  Validación completada — {len(errores)} errores encontrados.")

    # Guardar log
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lineas = [f"\n{'='*55}", f"  REPORTE DE CALIDAD — {ts}", f"{'='*55}"]
    log_lineas += errores[:100] if errores else ["  Sin errores detectados."]
    if len(errores) > 100:
        log_lineas.append(f"  ... y {len(errores)-100} errores más.")
    escribir_log(log_lineas)
    return errores

# ── FASE C: INSERTAR DATOS LIMPIOS DEL EXCEL ─────────────────
def fase_c_insertar_limpios(conn, config):
    print("\n" + "="*55)
    print("  FASE C: INSERTAR DATOS LIMPIOS (Excel normalizado)")
    print("="*55)

    UMBRAL = config["fuzzy_matching"]["umbral_similitud"]
    cur = conn.cursor()

    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name="Datos_Limpios")
    except FileNotFoundError:
        print("  ADVERTENCIA: Excel no encontrado, generando datos con Faker.")
        df = None

    # Insertar Autores
    autores_map = {}
    if df is not None:
        autores_unicos = df["autor_nombre"].dropna().unique()
    else:
        autores_unicos = [fake.name() for _ in range(10)]

    for nombre in autores_unicos:
        cur.execute(
            "INSERT INTO Autores(nombre) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id_autor",
            (nombre,)
        )
        res = cur.fetchone()
        if res:
            autores_map[nombre] = res[0]

    # Insertar Categorias
    cats_map = {}
    if df is not None:
        cats = pd.concat([
            df["categoria_principal"].dropna(),
            df["categoria_secundaria"].dropna()
        ]).unique()
    else:
        cats = ["Tecnología", "Historia", "Literatura", "Ciencia", "Arte"]

    for cat in cats:
        cur.execute(
            "INSERT INTO Categorias(nombre) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id_categoria",
            (cat,)
        )
        res = cur.fetchone()
        if res:
            cats_map[cat] = res[0]

    # Insertar Editoriales
    edits_map = {}
    if df is not None:
        editoriales = df["editorial_info"].dropna().unique()
    else:
        editoriales = [fake.company() for _ in range(5)]

    for edit in editoriales:
        cur.execute(
            "INSERT INTO Editoriales(nombre) VALUES (%s) ON CONFLICT DO NOTHING RETURNING id_editorial",
            (edit,)
        )
        res = cur.fetchone()
        if res:
            edits_map[edit] = res[0]

    # Insertar Libros con Fuzzy Matching
    titulos_insertados = []
    insertados = 0
    fuzzy_descartados = 0

    if df is not None:
        filas = df.itertuples(index=False)
    else:
        filas = []

    for fila in filas:
        titulo  = limpiar_texto(getattr(fila, "titulo_libro", None))
        if not titulo:
            continue

        # Fuzzy matching — evitar duplicados similares
        es_duplicado = False
        for t_prev in titulos_insertados:
            if fuzz.ratio(titulo, t_prev) >= UMBRAL:
                es_duplicado = True
                fuzzy_descartados += 1
                break
        if es_duplicado:
            continue

        titulos_insertados.append(titulo)
        autor    = limpiar_texto(getattr(fila, "autor_nombre", None))
        fecha    = parsear_fecha(getattr(fila, "fecha_publicacion", None))
        cat_p    = limpiar_texto(getattr(fila, "categoria_principal", None))
        editorial = limpiar_texto(getattr(fila, "editorial_info", None))

        id_autor    = autores_map.get(autor)
        id_cat      = cats_map.get(cat_p)
        id_editorial = edits_map.get(editorial)

        cur.execute("""
            INSERT INTO Libros(titulo, fecha_publicacion, id_autor, id_categoria, id_editorial)
            VALUES (%s, %s, %s, %s, %s)
        """, (titulo, fecha, id_autor, id_cat, id_editorial))
        insertados += 1

    conn.commit()
    cur.close()
    print(f"  ✔  {insertados} libros insertados.")
    print(f"  ✔  {fuzzy_descartados} duplicados descartados por Fuzzy Matching.")

# ── FASE D: MIGRACIÓN A MONGODB con Data Masking ─────────────
def fase_d_migrar_mongo(conn, config):
    print("\n" + "="*55)
    print("  FASE D: MIGRACIÓN A MONGODB")
    print("="*55)

    try:
        mongo_cliente, mongo_db = conectar_mongo()
        print("  Conexión a MongoDB exitosa.")
    except Exception as e:
        print(f"  ERROR conectando a MongoDB: {e}")
        return {}

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    reporte = {}

    tablas = {
        "autores":     ("Autores",     "authors"),
        "categorias":  ("Categorias",  "categories"),
        "editoriales": ("Editoriales", "publishers"),
        "libros":      ("Libros",      "books"),
    }

    for clave, (tabla_pg, coleccion_mg) in tablas.items():
        print(f"  → {tabla_pg} → {coleccion_mg} ...", end=" ", flush=True)
        try:
            cur.execute(f"SELECT * FROM {tabla_pg}")
            filas = [dict(f) for f in cur.fetchall()]
        except Exception as e:
            print(f"ERROR PG: {e}")
            reporte[clave] = {"estado": "ERROR_PG", "insertados": 0}
            continue

        if not filas:
            print("sin datos.")
            reporte[clave] = {"estado": "OMITIDO", "insertados": 0}
            continue

        # Convertir fechas
        for doc in filas:
            for k, v in doc.items():
                if isinstance(v, datetime.date):
                    doc[k] = v.isoformat()

        col = mongo_db[coleccion_mg]
        col.drop()
        resultado = col.insert_many(filas, ordered=False)
        insertados = len(resultado.inserted_ids)
        print(f"{insertados}/{len(filas)} docs OK.")
        reporte[clave] = {"estado": "OK", "registros": len(filas), "insertados": insertados}

    # Migrar Prestamos con Data Masking en correo
    print(f"  → Prestamos_Crudos → loans (con Data Masking) ...", end=" ", flush=True)
    try:
        cur.execute("SELECT * FROM Prestamos_Crudos")
        filas = [dict(f) for f in cur.fetchall()]
        campos_mask = config["data_masking"]["campos"]
        for doc in filas:
            for campo in campos_mask:
                if campo in doc:
                    doc[campo] = mask_email(doc[campo])
            for k, v in doc.items():
                if isinstance(v, datetime.date):
                    doc[k] = v.isoformat()
        col = mongo_db["loans"]
        col.drop()
        resultado = col.insert_many(filas, ordered=False)
        print(f"{len(resultado.inserted_ids)}/{len(filas)} docs OK (correos hasheados).")
        reporte["prestamos"] = {"estado": "OK", "insertados": len(resultado.inserted_ids)}
    except Exception as e:
        print(f"ERROR: {e}")
        reporte["prestamos"] = {"estado": "ERROR", "insertados": 0}

    cur.close()
    mongo_cliente.close()

    # Reporte final
    total_mg = sum(v["insertados"] for v in reporte.values())
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_lineas = [
        f"\n{'='*55}",
        f"  FASE D: MIGRACIÓN MONGODB — {ts}",
        f"{'='*55}",
    ]
    for k, v in reporte.items():
        log_lineas.append(f"  {k:15s} | {v['estado']:8s} | {v['insertados']} docs")
    log_lineas.append(f"  TOTAL insertados en MongoDB: {total_mg}")
    escribir_log(log_lineas)
    print(f"\n  ✔  Total migrado a MongoDB: {total_mg} documentos.")
    return reporte

# ── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  FRAMEWORK DE CALIDAD — BIBLIOTECA UNIVERSITARIA")
    print("="*55)

    config = cargar_config()

    try:
        conn = conectar_postgres()
        print("\n  ✔  Conexión a PostgreSQL exitosa.")
    except Exception as e:
        print(f"\n  ERROR conectando a PostgreSQL: {e}")
        exit(1)

    try:
        fase_a_poblar_legacy(conn)
        errores = fase_b_validar(conn, config)
        fase_c_insertar_limpios(conn, config)
        reporte = fase_d_migrar_mongo(conn, config)
    finally:
        conn.close()

    print(f"\n{'='*55}")
    print(f"  ✔  Framework completado.")
    print(f"  ✔  Errores de calidad detectados: {len(errores)}")
    print(f"  ✔  Log guardado en: {LOG_FILE}")
    print(f"{'='*55}\n")