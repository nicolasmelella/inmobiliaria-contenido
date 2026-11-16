"""Utilidades compartidas: .env, ejecución de comandos y normalización de texto."""
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def cargar_env(ruta=None):
    """Lee un .env simple (CLAVE=valor) sin dependencias externas. No pisa variables ya definidas."""
    ruta = Path(ruta) if ruta else RAIZ / ".env"
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def correr(cmd, silencioso=True):
    """Corre un comando; si falla, muestra el error y corta."""
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=silencioso, text=True)
    if r.returncode != 0:
        if silencioso:
            sys.stderr.write((r.stderr or "")[-3000:])
        raise SystemExit(f"ERROR al correr: {' '.join(map(str, cmd))[:300]}")
    return r


def duracion(archivo):
    r = correr(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1", str(archivo)])
    return float(r.stdout.strip())


def normalizar(palabra):
    """minúsculas, sin tildes ni puntuación: para comparar el guion con Whisper."""
    s = unicodedata.normalize("NFD", palabra.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ]", "", s)


def hex_a_ass(color, alfa=0):
    """#RRGGBB -> &HAABBGGRR (formato de color de ASS)."""
    c = color.lstrip("#")
    r, g, b = c[0:2], c[2:4], c[4:6]
    return f"&H{alfa:02X}{b}{g}{r}".upper()


def ruta_marca():
    """marca/marca.json del proyecto (o la que diga la variable MOTOR_MARCA)."""
    return Path(os.environ.get("MOTOR_MARCA") or RAIZ / "marca" / "marca.json")


def cargar_marca():
    """Lee la configuración de marca. Si no existe, devuelve {} y los scripts usan sus valores neutros."""
    r = ruta_marca()
    if not r.exists():
        return {}
    m = json.loads(r.read_text(encoding="utf-8"))
    m["_base"] = str(r.parent)
    return m


def archivo_marca(m, ruta):
    """Ruta de un archivo nombrado en marca.json -> absoluta, o None si no existe.
    Se busca relativa a la raíz del proyecto (ej. "fuentes/Marca-Bold.ttf") y a la carpeta de marca.json."""
    if not ruta:
        return None
    p = Path(ruta)
    candidatos = [p] if p.is_absolute() else [RAIZ / p, Path(m.get("_base", RAIZ)) / p]
    return next((str(c) for c in candidatos if c.exists()), None)


def familia_fuente(ruta):
    """Nombre de familia de un .ttf/.otf (lo que necesita libass para los subtítulos)."""
    try:
        from PIL import ImageFont
        return ImageFont.truetype(ruta, 10).getname()[0]
    except Exception:
        return None


def g(m, *claves, defecto=None):
    """g(marca, "colores", "acento") -> valor anidado o defecto."""
    for k in claves:
        if not isinstance(m, dict) or k not in m or m[k] in ("", None):
            return defecto
        m = m[k]
    return m


def tokens_resaltados(texto, mayus=False):
    """'Antes, *preguntá*: ya' -> [('Antes,', False), ('preguntá:', True), ('ya', False)].
    El resaltado se marca con *...* y puede abarcar varias palabras; la puntuación pegada queda con su palabra."""
    out, activo = [], False
    for w in texto.split():
        resaltada = activo or w.startswith("*")
        activo = activo ^ (w.count("*") % 2 == 1)
        w = w.replace("*", "")
        if w:
            out.append((w.upper() if mayus else w, resaltada))
    return out
