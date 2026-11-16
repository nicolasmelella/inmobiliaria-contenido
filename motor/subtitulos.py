#!/usr/bin/env python3
"""Arma los subtítulos (.ass) por frases, sincronizados con los tiempos de Whisper.

Uso:
  python3 motor/subtitulos.py --guion guion.txt --palabras trabajo/palabras.json --salida trabajo/subs.ass
         [--fuente "Montserrat"] [--fuente-acento "Playfair Display"] [--color "#FFFFFF"] [--borde "#000000"]
         [--tam 92] [--pos 0.62] [--hasta 18.5]

Formato del guion: UNA LÍNEA = UN BLOQUE de subtítulo, con el texto literal.
  - "Línea uno | línea dos"  -> dos renglones: el 1.º en MAYÚSCULAS, el 2.º en itálica (fuente de acento).
  - "Una sola línea"         -> un renglón en MAYÚSCULAS.
  - Líneas vacías o que empiezan con # se ignoran.

  - "*palabras*"            -> en itálica (fuente de acento), dentro de cualquier renglón.
  - Mayúsculas en el renglón 1 salvo que marca.json -> placa.mayusculas sea false.

Sin voz (texto + música): --tiempos "0,2.8,5.4" en vez de --palabras (segundo en que arranca cada bloque).

Cómo sincroniza: alinea las palabras del guion con las de Whisper (difflib, tolerante a errores de
transcripción). Cada bloque arranca cuando se dice su primera palabra y termina cuando arranca el siguiente.
"""
import argparse
import difflib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import archivo_marca, cargar_marca, familia_fuente, g, hex_a_ass, normalizar  # noqa: E402


def leer_bloques(ruta):
    bloques = []
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = [p.strip() for p in linea.split("|")]
        bloques.append({"l1": partes[0], "l2": partes[1] if len(partes) > 1 else ""})
    return bloques


def tokens(texto):
    return [t for t in (normalizar(p) for p in texto.split()) if t]


def sincronizar(bloques, palabras, hasta=None):
    w_norm = [normalizar(p["palabra"]) for p in palabras]
    g_norm, dueno = [], []  # token del guion -> índice de bloque
    for i, b in enumerate(bloques):
        for t in tokens(b["l1"] + " " + b["l2"]):
            g_norm.append(t)
            dueno.append(i)

    mapa = {}  # índice token guion -> índice palabra whisper
    sm = difflib.SequenceMatcher(a=g_norm, b=w_norm, autojunk=False)
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and (a2 - a1) == (b2 - b1)):
            for k in range(a2 - a1):
                mapa[a1 + k] = b1 + k

    inicios = []
    for i in range(len(bloques)):
        idx = [k for k, d in enumerate(dueno) if d == i and k in mapa]
        inicios.append(palabras[mapa[idx[0]]]["inicio"] if idx else None)

    # bloques sin coincidencias: interpolar entre vecinos
    fin_total = hasta or (palabras[-1]["fin"] if palabras else 0)
    for i, v in enumerate(inicios):
        if v is None:
            prev = next((inicios[j] for j in range(i - 1, -1, -1) if inicios[j] is not None), 0.0)
            sig_j = next((j for j in range(i + 1, len(inicios)) if inicios[j] is not None), None)
            sig = inicios[sig_j] if sig_j is not None else fin_total
            pasos = (sig_j - i + 1) if sig_j is not None else (len(inicios) - i + 1)
            inicios[i] = prev + (sig - prev) / max(pasos, 2)

    # asegurar orden creciente
    for i in range(1, len(inicios)):
        inicios[i] = max(inicios[i], inicios[i - 1] + 0.3)

    tiempos = []
    for i, ini in enumerate(inicios):
        fin = inicios[i + 1] if i + 1 < len(inicios) else fin_total
        if hasta:
            fin = min(fin, hasta)
        tiempos.append((ini, max(fin, ini + 0.4)))
    return tiempos, len(mapa), len(g_norm)


def t_ass(s):
    s = max(0, s)
    h = int(s // 3600)
    m = int(s % 3600 // 60)
    return f"{h}:{m:02d}:{s % 60:05.2f}"


def escapar(t):
    return t.replace("{", "(").replace("}", ")").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guion", required=True)
    fuente_t = ap.add_mutually_exclusive_group(required=True)
    fuente_t.add_argument("--palabras", help="tiempos por palabra de Whisper (transcribir.py)")
    fuente_t.add_argument("--tiempos", help='sin voz: segundo de inicio de cada bloque, ej. "0,2.8,5.4"')
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ancho", type=int, default=1080)
    ap.add_argument("--alto", type=int, default=1920)
    ap.add_argument("--fuente", help="familia de la línea 1 (default: la principal de marca/marca.json)")
    ap.add_argument("--fuente-acento", help="familia de la línea 2 (default: la de acento de marca.json)")
    ap.add_argument("--color", help="color del texto (default: colores.texto de marca.json)")
    ap.add_argument("--color-acento", default=None, help="color de la línea 2 (default: el mismo)")
    ap.add_argument("--borde", help="color del borde (default: colores.borde de marca.json o negro)")
    ap.add_argument("--grosor-borde", type=float, default=None, help="default: marca.json -> subtitulos.borde o 4")
    ap.add_argument("--entrada", choices=["bloque", "palabras"], default=None,
                    help="bloque: aparece entero; palabras: cada palabra entra con un fundido (default: marca.json o bloque)")
    ap.add_argument("--sombra", type=float, default=None, help="sombra en px (default: marca.json -> subtitulos.sombra o 0)")
    ap.add_argument("--tam", type=int, default=88, help="tamaño de la línea 1 (a 1080 de ancho)")
    ap.add_argument("--pos", type=float, default=0.62, help="altura del centro del bloque (0 arriba, 1 abajo)")
    ap.add_argument("--hasta", type=float, default=None, help="segundo en que terminan los subtítulos (ej. inicio del cierre)")
    a = ap.parse_args()

    # Lo que no se pasa por línea de comando sale de marca/marca.json
    m = cargar_marca()
    a.fuente = a.fuente or familia_fuente(archivo_marca(m, g(m, "fuentes", "principal")) or "") or "DejaVu Sans"
    a.fuente_acento = (a.fuente_acento or familia_fuente(archivo_marca(m, g(m, "fuentes", "acento")) or "")
                       or "DejaVu Serif")
    a.color = a.color or g(m, "colores", "texto", defecto="#FFFFFF")
    a.borde = a.borde or g(m, "colores", "borde", defecto="#000000")

    a.grosor_borde = a.grosor_borde if a.grosor_borde is not None else g(m, "subtitulos", "borde", defecto=4)
    a.sombra = a.sombra if a.sombra is not None else g(m, "subtitulos", "sombra", defecto=0)
    mayus = g(m, "placa", "mayusculas", defecto=True)
    a.entrada = a.entrada or g(m, "subtitulos", "entrada", defecto="bloque")

    bloques = leer_bloques(a.guion)
    if not bloques:
        sys.exit("El guion no tiene bloques")
    if a.tiempos:
        inicios = [float(v) for v in a.tiempos.split(",")]
        if len(inicios) != len(bloques):
            sys.exit(f"--tiempos tiene {len(inicios)} valores y el guion {len(bloques)} bloques")
        if not a.hasta:
            sys.exit("Sin voz hace falta --hasta (segundo en que termina el último bloque)")
        tiempos = [(ini, (inicios[i + 1] if i + 1 < len(inicios) else a.hasta)) for i, ini in enumerate(inicios)]
        ok = total = 0
    else:
        palabras = json.loads(Path(a.palabras).read_text(encoding="utf-8"))
        tiempos, ok, total = sincronizar(bloques, palabras, a.hasta)

    tam2 = round(a.tam * 0.78)
    margen = round(a.ancho * 0.08)
    col1 = hex_a_ass(a.color)
    col2 = hex_a_ass(a.color_acento or a.color)
    borde = hex_a_ass(a.borde)
    x, y = a.ancho // 2, round(a.alto * a.pos)

    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {a.ancho}
PlayResY: {a.alto}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Principal,{a.fuente},{a.tam},{col1},{col1},{borde},&H8C000000,-1,0,0,0,100,100,0,0,1,{a.grosor_borde},{a.sombra},5,{margen},{margen},0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    eventos = []
    for b, (ini, fin) in zip(bloques, tiempos):
        ita = r"{\fn" + a.fuente_acento + r"\i1\b0}"
        nor = r"{\fn" + a.fuente + r"\i0\b1}"

        paso = [0]  # ms acumulados para la entrada palabra por palabra

        def aparece():
            if a.entrada != "palabras":
                return ""
            t0 = paso[0]
            paso[0] += 110
            return r"{\alpha&HFF&\t(" + f"{t0},{t0 + 220}" + r",\alpha&H00&)}"

        def con_italica(t, mayus_ok):
            # *palabras* -> itálica de acento; el resto en la principal
            out = []
            for k, p in enumerate(escapar(t).split("*")):
                palabras = [w for w in p.split(" ")]
                trozo = " ".join((aparece() + w) if w else w for w in palabras)
                out.append((ita + trozo + nor) if k % 2 else (trozo.upper() if mayus_ok else trozo))
            return "".join(out)
        txt = con_italica(b["l1"], mayus)
        if b["l2"]:
            txt += (r"\N{\fn" + a.fuente_acento + r"\fs" + str(tam2) + r"\i1\b0\c" + col2 + "}"
                    + " ".join(aparece() + w for w in escapar(b["l2"]).replace("*", "").split(" ")))
        anim = r"{\an5\pos(" + f"{x},{y}" + r")\fad(90,60)\fscx92\fscy92\t(0,140,\fscx100\fscy100)}"
        eventos.append(f"Dialogue: 0,{t_ass(ini)},{t_ass(fin)},Principal,,0,0,0,,{anim}{txt}")

    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(cab + "\n".join(eventos) + "\n", encoding="utf-8")
    print(f"OK {len(bloques)} bloques -> {a.salida}" + (f" · palabras del guion encontradas en Whisper: {ok}/{total}"
                                                        if total else " · tiempos fijos (sin voz)"))
    if total and ok / total < 0.7:
        print("AVISO: menos del 70 % del guion coincide con lo que se escucha. ¿La voz dice el mismo texto?")
    for i, (b, (ini, fin)) in enumerate(zip(bloques, tiempos), 1):
        print(f"  {i:02d}  {ini:6.2f}-{fin:6.2f}  {b['l1']}" + (f" | {b['l2']}" if b["l2"] else ""))


if __name__ == "__main__":
    main()
