import re
import hashlib
import datetime
import pytest
import sys
import os

# Para que pytest encuentre los módulos de src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── FUNCIONES A TESTEAR (copiadas de main.py para pruebas aisladas) ──

def mask_email(email):
    if not email:
        return None
    return hashlib.sha256(str(email).encode()).hexdigest()

def parsear_fecha(s):
    if not s or str(s).strip() in ("N/A", "Desconocida", "Sin fecha", "nan"):
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(str(s).strip(), fmt).date()
        except:
            pass
    return None

def limpiar_texto(s):
    if not s or str(s).strip() in ("nan", ""):
        return None
    return re.sub(r"\s+", " ", str(s).strip()).title()

def validar_email(correo):
    patron = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
    if not correo:
        return False
    return bool(patron.match(str(correo)))

def validar_calificacion(valor, minimo=1, maximo=5):
    try:
        val = float(str(valor).replace("/5", "").strip())
        return minimo <= val <= maximo
    except:
        return False

def validar_cantidad(valor):
    try:
        return int(str(valor)) >= 0
    except:
        return False


# ══════════════════════════════════════════════════════════════
# TESTS — Data Masking (SHA-256)
# ══════════════════════════════════════════════════════════════

class TestDataMasking:

    def test_email_valido_produce_hash(self):
        """Un correo válido debe producir un hash SHA-256 de 64 caracteres."""
        resultado = mask_email("usuario@correo.com")
        assert resultado is not None
        assert len(resultado) == 64

    def test_mismo_email_mismo_hash(self):
        """El mismo correo siempre debe producir el mismo hash (determinista)."""
        hash1 = mask_email("test@biblioteca.com")
        hash2 = mask_email("test@biblioteca.com")
        assert hash1 == hash2

    def test_emails_distintos_hashes_distintos(self):
        """Correos diferentes deben producir hashes distintos."""
        hash1 = mask_email("usuario1@correo.com")
        hash2 = mask_email("usuario2@correo.com")
        assert hash1 != hash2

    def test_email_nulo_retorna_none(self):
        """Un correo nulo debe retornar None."""
        assert mask_email(None) is None

    def test_email_vacio_retorna_none(self):
        """Un correo vacío debe retornar None."""
        assert mask_email("") is None

    def test_hash_es_hexadecimal(self):
        """El hash debe ser una cadena hexadecimal válida."""
        resultado = mask_email("prueba@test.com")
        assert all(c in "0123456789abcdef" for c in resultado)


# ══════════════════════════════════════════════════════════════
# TESTS — Parseo de fechas
# ══════════════════════════════════════════════════════════════

class TestParsearFecha:

    def test_formato_dd_mm_yyyy(self):
        """Debe parsear formato DD/MM/YYYY."""
        resultado = parsear_fecha("25/12/2020")
        assert resultado == datetime.date(2020, 12, 25)

    def test_formato_yyyy_mm_dd(self):
        """Debe parsear formato YYYY-MM-DD."""
        resultado = parsear_fecha("2020-12-25")
        assert resultado == datetime.date(2020, 12, 25)

    def test_fecha_desconocida_retorna_none(self):
        """'Desconocida' debe retornar None."""
        assert parsear_fecha("Desconocida") is None

    def test_fecha_na_retorna_none(self):
        """'N/A' debe retornar None."""
        assert parsear_fecha("N/A") is None

    def test_fecha_vacia_retorna_none(self):
        """Cadena vacía debe retornar None."""
        assert parsear_fecha("") is None

    def test_fecha_none_retorna_none(self):
        """None debe retornar None."""
        assert parsear_fecha(None) is None

    def test_fecha_sin_fecha_retorna_none(self):
        """'Sin fecha' debe retornar None."""
        assert parsear_fecha("Sin fecha") is None

    def test_formato_dd_mm_yy(self):
        """Debe parsear formato DD/MM/YY."""
        resultado = parsear_fecha("25/12/20")
        assert resultado is not None


# ══════════════════════════════════════════════════════════════
# TESTS — Limpieza de texto
# ══════════════════════════════════════════════════════════════

class TestLimpiarTexto:

    def test_elimina_espacios_extra(self):
        """Debe eliminar espacios extra al inicio, final y en medio."""
        assert limpiar_texto("  Hola   Mundo  ") == "Hola Mundo"

    def test_normaliza_mayusculas(self):
        """Debe convertir a Title Case."""
        assert limpiar_texto("GABRIEL GARCIA MARQUEZ") == "Gabriel Garcia Marquez"

    def test_normaliza_minusculas(self):
        """Debe convertir minúsculas a Title Case."""
        assert limpiar_texto("gabriel garcia marquez") == "Gabriel Garcia Marquez"

    def test_elimina_tabs(self):
        """Debe eliminar tabulaciones."""
        assert limpiar_texto("Titulo\tLibro") == "Titulo Libro"

    def test_texto_none_retorna_none(self):
        """None debe retornar None."""
        assert limpiar_texto(None) is None

    def test_texto_vacio_retorna_none(self):
        """Cadena vacía debe retornar None."""
        assert limpiar_texto("") is None

    def test_texto_nan_retorna_none(self):
        """'nan' debe retornar None."""
        assert limpiar_texto("nan") is None

    def test_texto_normal_sin_cambios(self):
        """Texto ya limpio no debe cambiar (salvo Title Case)."""
        assert limpiar_texto("Cien Años De Soledad") == "Cien Años De Soledad"


# ══════════════════════════════════════════════════════════════
# TESTS — Validación de email
# ══════════════════════════════════════════════════════════════

class TestValidarEmail:

    def test_email_valido(self):
        """Un correo bien formado debe ser válido."""
        assert validar_email("usuario@biblioteca.com") is True

    def test_email_sin_arroba(self):
        """Sin @ debe ser inválido."""
        assert validar_email("usuariobiblioteca.com") is False

    def test_email_sin_dominio(self):
        """Sin dominio debe ser inválido."""
        assert validar_email("usuario@") is False

    def test_email_nulo(self):
        """None debe ser inválido."""
        assert validar_email(None) is False

    def test_email_vacio(self):
        """Cadena vacía debe ser inválida."""
        assert validar_email("") is False

    def test_email_con_punto(self):
        """Correo con punto en el dominio debe ser válido."""
        assert validar_email("nombre.apellido@correo.co") is True

    def test_email_formato_roto(self):
        """Formato roto debe ser inválido."""
        assert validar_email("usuario_at_email.com") is False


# ══════════════════════════════════════════════════════════════
# TESTS — Validación de calificación
# ══════════════════════════════════════════════════════════════

class TestValidarCalificacion:

    def test_calificacion_valida_1(self):
        assert validar_calificacion(1) is True

    def test_calificacion_valida_5(self):
        assert validar_calificacion(5) is True

    def test_calificacion_valida_3(self):
        assert validar_calificacion(3) is True

    def test_calificacion_texto_valido(self):
        """'3' como texto debe ser válido."""
        assert validar_calificacion("3") is True

    def test_calificacion_cero_invalida(self):
        assert validar_calificacion(0) is False

    def test_calificacion_seis_invalida(self):
        assert validar_calificacion(6) is False

    def test_calificacion_texto_invalido(self):
        """'Cinco' como texto debe ser inválido."""
        assert validar_calificacion("Cinco") is False

    def test_calificacion_formato_fraccion(self):
        """'5/5' debe ser válido (se limpia el /5)."""
        assert validar_calificacion("5/5") is True

    def test_calificacion_negativa_invalida(self):
        assert validar_calificacion(-1) is False

    def test_calificacion_none_invalida(self):
        assert validar_calificacion(None) is False


# ══════════════════════════════════════════════════════════════
# TESTS — Validación de cantidad
# ══════════════════════════════════════════════════════════════

class TestValidarCantidad:

    def test_cantidad_positiva_valida(self):
        assert validar_cantidad(10) is True

    def test_cantidad_cero_valida(self):
        assert validar_cantidad(0) is True

    def test_cantidad_negativa_invalida(self):
        assert validar_cantidad(-5) is False

    def test_cantidad_texto_numero_valido(self):
        assert validar_cantidad("15") is True

    def test_cantidad_texto_invalido(self):
        """'Diez' como texto debe ser inválido."""
        assert validar_cantidad("Diez") is False

    def test_cantidad_none_invalida(self):
        assert validar_cantidad(None) is False