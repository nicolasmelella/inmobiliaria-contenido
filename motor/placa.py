#!/usr/bin/env python3
"""Placas estáticas para el feed (1:1, 4:5 y 9:16) con la frase más fuerte del guion.

Uso:
  python3 motor/placa.py --texto "Tus leads *llegan tarde* | y se enfrían" \
      --imagen img/foto.jpg --logo clientes/x/logo.png --cta "Agendá tu reunión" \
      --salida salida/placas/placa1

  Fondo (uno de los tres):
    --imagen foto.jpg              foto de fondo (se recorta para llenar; --foco 0.5,0.4)
    --video clip.mp4 --t 3.2       un cuadro de un clip (usá el CLIP ORIGINAL o el borrador sin texto,
                                   nunca el video final: trae los subtítulos quemados y se pisan con la placa)
    --fondo "#111111"              color liso
  Texto:
    "L1 | L2"   L1 en la fuente principal (MAYÚSCULAS salvo que marca.json -> placa.mayusculas sea false), L2 en itálica.
    --diferenciales "A · B · C"  renglón de ítems cortos entre el texto y el botón.
    --etiqueta "PROPIEDADES SELECCIONADAS"  píldora chica arriba del título (degradado de placa.etiqueta_colores).
    *palabra*   en L1 se resalta: --resaltado color (color de acento), italica (serif itálica) o caja (itálica sobre recuadro).
  Marca:
    --fuente fuentes/Principal-Bold.ttf  --fuente-acento fuentes/Acento-Italic.ttf
    --color "#FFFFFF" --color-acento "#FFC400"  --logo logo.png  --cta "..." [--estilo-cta contorno|rellena]
  Salida:
    --formatos 1x1,4x5[,9x16]  --salida salida/placas/placa1  ->  placa1_1x1.png / .jpg, placa1_4x5.png / .jpg

Cada formato se COMPONE por separado (no se recorta uno del otro). Si el texto no entra, se achica solo hasta un
mínimo; si igual no entra, avisa: la frase es demasiado larga para una placa.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import archivo_marca, cargar_marca, g, tokens_resaltados  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
FORMATOS = {"1x1": (1080, 1080), "4x5": (1080, 1350), "9x16": (1080, 1920)}

# Fuentes de respaldo si no se pasan archivos ni hay nada en fuentes/ (Linux / macOS / Windows).
RESPALDO = {
    "negrita": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
                "C:/Windows/Fonts/arialbd.ttf"],
    "italica": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf",
                "/System/Library/Fonts/Supplemental/Georgia Italic.ttf", "/Library/Fonts/Georgia Italic.ttf",
                "C:/Windows/Fonts/georgiai.ttf"],
}
_avisados = set()


def _fc_match(patron):
    """Pregunta a fontconfig (Linux / Mac con fontconfig) por una fuente instalada que cumpla el patrón."""
    try:
        r = subprocess.run(["fc-match", "-f", "%{file}", patron], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def cargar_fuente(ruta, tam, negrita=False, italica=False):
    """Fuente pedida -> fuentes/ del proyecto -> respaldo del sistema. Avisa si tiene que usar un respaldo."""
    if ruta and not Path(ruta).exists():
        sys.exit(f"No existe la fuente {ruta}")
    candidatos = [ruta] if ruta else []
    candidatos += sorted(str(p) for p in (RAIZ / "fuentes").glob("*.[ot]tf")
                         if (italica and "ital" in p.name.lower()) or (not italica and "ital" not in p.name.lower()))
    candidatos += RESPALDO["italica" if italica else "negrita"]
    candidatos.append(_fc_match("serif:italic" if italica else "sans:bold"))
    for c in candidatos:
        if c and Path(c).exists():
            if not ruta and (italica, c) not in _avisados:
                _avisados.add((italica, c))
                print(f"  (fuente {'de acento' if italica else 'principal'} de respaldo: {Path(c).name}; "
                      f"pasá la de la marca con --fuente{'-acento' if italica else ''})")
            return ImageFont.truetype(c, tam)
    sys.exit("No encontré ninguna fuente .ttf/.otf: poné las de la marca en fuentes/ o pasalas con --fuente")


def hex_rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def luminancia(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def cubrir(im, w, h, foco=(0.5, 0.5)):
    k = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * k)), max(h, round(im.height * k))), Image.LANCZOS)
    x = round((im.width - w) * foco[0])
    y = round((im.height - h) * foco[1])
    return im.crop((x, y, x + w, y + h))


def degradado(w, h, desde=0.35, alfa_max=215, color=(0, 0, 0)):
    """Oscurece de abajo hacia arriba, para que el texto blanco se lea sobre cualquier foto."""
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    y0 = round(h * desde)
    for y in range(y0, h):
        a = round(alfa_max * ((y - y0) / (h - y0)) ** 1.3)
        d.line([(0, y), (w, y)], fill=tuple(color) + (a,))
    return capa


def partir(palabras, fuente, ancho_max, draw):
    """Reparte palabras (texto, resaltada) en renglones que entren en ancho_max."""
    renglones, actual = [], []
    for p in palabras:
        prueba = actual + [p]
        if actual and draw.textlength(" ".join(t for t, _ in prueba), font=fuente) > ancho_max:
            renglones.append(actual)
            actual = [p]
        else:
            actual = prueba
    if actual:
        renglones.append(actual)
    return renglones


def tokens_l1(l1, mayus=True):
    """'Tus leads *llegan tarde*' -> [('TUS', False), ('LEADS', False), ('LLEGAN', True), ('TARDE', True)]"""
    return tokens_resaltados(l1, mayus=mayus)


def partir_mixto(palabras, fuente_de, ancho_max, draw):
    """Como partir(), pero cada palabra puede tener su propia fuente (resaltado en itálica)."""
    def ancho(renglon):
        return (sum(draw.textlength(t, font=fuente_de(r)) for t, r in renglon)
                + sum(draw.textlength(" ", font=fuente_de(r)) for _, r in renglon[:-1]))
    renglones, actual = [], []
    for p in palabras:
        if actual and ancho(actual + [p]) > ancho_max:
            renglones.append(actual)
            actual = [p]
        else:
            actual = actual + [p]
    if actual:
        renglones.append(actual)
    return renglones, ancho


def pildora(draw, lienzo, texto, fuente, x, y_centro, color, estilo, centrada=False, color_texto_rellena=None):
    tw = draw.textlength(texto, font=fuente)
    alto = round(fuente.size * 2.0)
    ancho = round(tw + fuente.size * 2.2)
    x0 = x - ancho // 2 if centrada else x
    y0 = y_centro - alto // 2
    caja = [x0, y0, x0 + ancho, y0 + alto]
    rgb = hex_rgb(color)
    if estilo == "rellena":
        draw.rounded_rectangle(caja, radius=alto // 2, fill=rgb)
        col_txt = hex_rgb(color_texto_rellena) if color_texto_rellena else (
            (17, 17, 17) if luminancia(rgb) > 140 else (255, 255, 255))
    else:
        draw.rounded_rectangle(caja, radius=alto // 2, outline=rgb, width=max(3, fuente.size // 10))
        col_txt = rgb
    draw.text((x0 + ancho / 2, y_centro), texto, font=fuente, fill=col_txt, anchor="mm")
    return caja


def etiqueta_degradada(lienzo, texto, fuente, x, y, colores):
    """Píldora con degradado horizontal (colores[0] -> colores[-1]) y texto blanco, arriba a la izquierda en (x, y)."""
    d = ImageDraw.Draw(lienzo)
    tw = d.textlength(texto, font=fuente)
    alto = round(fuente.size * 1.75)
    ancho = round(tw + fuente.size * 1.4)
    c0, c1 = hex_rgb(colores[0]), hex_rgb(colores[-1])
    grad = Image.new("RGBA", (ancho, alto))
    gd = ImageDraw.Draw(grad)
    for i in range(ancho):
        k = i / max(1, ancho - 1)
        gd.line([(i, 0), (i, alto)], fill=tuple(round(c0[j] + (c1[j] - c0[j]) * k) for j in range(3)) + (255,))
    mascara = Image.new("L", (ancho, alto), 0)
    ImageDraw.Draw(mascara).rounded_rectangle([0, 0, ancho - 1, alto - 1], radius=alto // 2, fill=255)
    grad.putalpha(mascara)
    lienzo.alpha_composite(grad, (round(x), round(y)))
    d.text((x + fuente.size * 0.7, y + alto / 2), texto, font=fuente, fill=(255, 255, 255), anchor="lm")
    return alto


def componer(a, fondo_img, w, h):
    margen = round(w * a.margen)
    ancho_txt = w - 2 * margen

    # Fondo
    if fondo_img is not None:
        lienzo = cubrir(fondo_img, w, h, a.foco).convert("RGBA")
        if a.tinte:   # tinte parejo de color sobre la foto (marca.json -> placa.tinte: {"color", "alfa"})
            lienzo.alpha_composite(Image.new("RGBA", (w, h), hex_rgb(a.tinte["color"]) + (int(a.tinte.get("alfa", 60)),)))
        lienzo.alpha_composite(degradado(w, h, desde=0.30 if h > w else 0.25, alfa_max=a.oscurecer,
                                         color=hex_rgb(a.velo) if a.velo else (0, 0, 0)))
        color_txt = a.color or (a.texto_marca if a.texto_marca and luminancia(hex_rgb(a.texto_marca)) > 150
                                else "#FFFFFF")
    else:
        rgb = hex_rgb(a.fondo)
        lienzo = Image.new("RGBA", (w, h), rgb + (255,))
        # Sin --color: el texto de la marca si contrasta con el fondo; si no, el fondo de la marca; si no, auto
        color_txt = a.color or next(
            (c for c in (a.texto_marca, a.fondo_marca)
             if c and abs(luminancia(hex_rgb(c)) - luminancia(rgb)) > 100),
            "#111111" if luminancia(rgb) > 150 else "#FFFFFF")
    draw = ImageDraw.Draw(lienzo)

    partes = [p.strip() for p in a.texto.split("|")]
    l1, l2 = partes[0], (partes[1].replace("*", "") if len(partes) > 1 else "")  # L2 ya va toda en itálica
    toks = tokens_l1(l1, mayus=a.mayus)
    italica = a.resaltado in ("italica", "caja")
    caja = a.resaltado == "caja"

    # Zona del texto: tercio inferior, arriba del CTA
    alto_cta = round(w * 0.10) if a.cta else 0
    base_y = h - margen - alto_cta - (round(w * 0.04) if a.cta else 0)

    # Diferenciales: un renglón corto entre el texto y el botón ("Sin contrato · Sin mínimo · Equipado")
    r_dif, f_dif, inter_dif = [], None, 0
    if a.diferenciales:
        f_dif = cargar_fuente(a.fuente, round(w * 0.034), negrita=True)
        items = [x.strip() for x in a.diferenciales.split("·") if x.strip()]
        sep = "  ·  "
        actual = ""
        for it in items:
            prueba = (actual + sep + it) if actual else it
            if actual and draw.textlength(prueba, font=f_dif) > ancho_txt:
                r_dif.append(actual)
                actual = it
            else:
                actual = prueba
        if actual:
            r_dif.append(actual)
        inter_dif = round(f_dif.size * 1.45)
        base_y -= len(r_dif) * inter_dif + round(w * 0.035)
    f_et, alto_et = None, 0
    if a.etiqueta:
        f_et = cargar_fuente(a.fuente_etiqueta or a.fuente, round(w * 0.026), negrita=True)
        alto_et = round(f_et.size * 1.75) + round(w * 0.025)
    zona_alta = h * (0.45 if h > w else 0.55)
    if a.posicion == "centro":
        zona_alta = h * 0.24   # texto en el medio: puede ocupar más alto

    # Tamaño: el más grande que entra (renglones ≤ 4, ancho ≤ 84 %)
    tam_max = round(w * a.tam_max)
    tam_min = round(w * 0.05)
    elegido = None
    for tam in range(tam_max, tam_min - 1, -2):
        f1 = cargar_fuente(a.fuente, tam, negrita=True)
        f2 = cargar_fuente(a.fuente_l2 or a.fuente_acento, round(tam * a.l2_ratio), italica=not a.fuente_l2)
        fi = cargar_fuente(a.fuente_acento, round(tam * 1.08), italica=True) if italica else f1
        fuente_de = (lambda r, f1=f1, fi=fi: fi if r else f1)
        r1, ancho1 = partir_mixto(toks, fuente_de, ancho_txt, draw)
        r2 = partir([(t, False) for t in l2.split()], f2, ancho_txt, draw) if l2 else []
        inter1 = round(tam * (a.interlineado or (1.12 if italica else 1.02)))
        inter2 = round(f2.size * a.l2_interlineado)
        alto_bloque = len(r1) * inter1 + (round(tam * 0.25) + len(r2) * inter2 if r2 else 0)
        # Una palabra sola más ancha que la caja no se parte: hay que achicar
        ancho_ok = (all(ancho1(r) <= ancho_txt for r in r1)
                    and all(draw.textlength(" ".join(t for t, _ in r), font=f2) <= ancho_txt for r in r2))
        if ancho_ok and len(r1) <= 4 and len(r2) <= 3 and alto_bloque + alto_et <= base_y - zona_alta:
            elegido = (f1, f2, fi, r1, r2, inter1, inter2, alto_bloque)
            break
    aviso = None
    if not elegido:
        aviso = "el texto no entra ni al tamaño mínimo: acortá la frase"
        f1 = cargar_fuente(a.fuente, tam_min, negrita=True)
        f2 = cargar_fuente(a.fuente_l2 or a.fuente_acento, round(tam_min * a.l2_ratio), italica=not a.fuente_l2)
        fi = cargar_fuente(a.fuente_acento, round(tam_min * 1.08), italica=True) if italica else f1
        r1, _ = partir_mixto(toks, lambda r: fi if r else f1, ancho_txt, draw)
        r2 = partir([(t, False) for t in l2.split()], f2, ancho_txt, draw) if l2 else []
        inter1 = round(tam_min * (a.interlineado or (1.12 if italica else 1.02)))
        inter2 = round(f2.size * a.l2_interlineado)
        elegido = (f1, f2, fi, r1, r2, inter1, inter2, len(r1) * inter1 + len(r2) * inter2)
    f1, f2, fi, r1, r2, inter1, inter2, alto_bloque = elegido

    # Dibujo (alineado a la izquierda: se lee mejor y no queda "apilado al centro")
    y = base_y - alto_bloque
    if a.posicion == "centro":
        # Como los posteos de la marca: el bloque (texto + diferenciales) centrado a la altura de los ojos
        alto_dif = (len(r_dif) * inter_dif + round(w * 0.035)) if r_dif else 0
        arriba = margen + w * 0.2                                   # debajo del logo
        abajo = h - margen - alto_cta - (round(w * 0.06) if a.cta else 0)  # encima del botón
        y = round(arriba + max(0, (abajo - arriba - alto_bloque - alto_dif) / 2))
        base_y = y + alto_bloque
    if fondo_img is not None and a.posicion == "centro":
        # velo parejo en toda la foto (no degradado) para que el texto se lea en el medio
        tinte = Image.new("RGBA", (w, h), (hex_rgb(a.velo) if a.velo else (0, 0, 0)) + (round(a.oscurecer * 0.42),))
        lienzo.alpha_composite(tinte)
    elif fondo_img is not None:
        # Velo extra que arranca un poco arriba del texto: con copys largos el bloque sube a zonas claras de la foto
        desde = max(0.05, (y - w * 0.15) / h)
        lienzo.alpha_composite(degradado(w, h, desde=desde, alfa_max=round(a.oscurecer * 0.6),
                                         color=hex_rgb(a.velo) if a.velo else (0, 0, 0)))
    if a.etiqueta:
        etiqueta_degradada(lienzo, a.etiqueta, f_et, margen, y - alto_et, a.etiqueta_colores)
    col = hex_rgb(color_txt)
    if italica:   # resaltado en itálica: mismo color que el texto salvo que la marca pida otro
        acento = hex_rgb(a.color_resaltado) if a.color_resaltado else col
    else:
        acento = hex_rgb(a.color_acento) if a.color_acento else col
    # El texto va en su propia capa para poder ponerle sombra suave sobre fotos
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dt = ImageDraw.Draw(capa)
    asc = f1.getmetrics()[0]
    cajas = Image.new("RGBA", (w, h), (0, 0, 0, 0))   # recuadros detrás del resaltado (variante "caja")
    dc = ImageDraw.Draw(cajas)
    col_caja = hex_rgb(a.color_caja or a.color_acento or "#C06A46")
    for renglon in r1:
        x = margen
        # Un recuadro por cada tramo seguido de palabras resaltadas en el renglón
        if caja:
            xx, tramo = margen, None
            for t, res in renglon + [("", False)]:
                f = fi if res else f1
                if res and tramo is None:
                    tramo = xx
                if not res and tramo is not None:
                    pad = round(f1.size * 0.18)
                    dc.rectangle([tramo - pad, y + asc - round(f1.size * 0.86), xx - draw.textlength(" ", font=fi) + pad,
                                  y + asc + round(f1.size * 0.24)], fill=col_caja + (round(255 * 0.85),))
                    tramo = None
                xx += draw.textlength(t, font=f) + (draw.textlength(" ", font=f) if t else 0)
        for t, res in renglon:
            f = fi if res else f1
            dt.text((x, y + asc), t, font=f, fill=(acento if res else col) + (255,), anchor="ls")
            x += draw.textlength(t, font=f) + draw.textlength(" ", font=f)
        y += inter1
    if r2:
        y += round(f1.size * 0.25)
        for renglon in r2:
            dt.text((margen, y), " ".join(t for t, _ in renglon), font=f2, fill=col + (255,))
            y += inter2
    if r_dif:
        y = base_y + round(w * 0.035)
        for linea in r_dif:
            # el separador va en el color de acento para que se lean como ítems sueltos
            x = margen
            for k, trozo in enumerate(linea.split("  ·  ")):
                if k:
                    dt.text((x, y), "  ·  ", font=f_dif, fill=(acento if not italica else col) + (255,))
                    x += draw.textlength("  ·  ", font=f_dif)
                dt.text((x, y), trozo, font=f_dif, fill=col + (255,))
                x += draw.textlength(trozo, font=f_dif)
            y += inter_dif
    lienzo.alpha_composite(cajas)
    if a.sombra and fondo_img is not None:
        sombra = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sombra.putalpha(capa.getchannel("A").point(lambda v: v * 0.55))
        sombra = sombra.filter(ImageFilter.GaussianBlur(round(w * 0.006)))
        lienzo.alpha_composite(sombra, (round(w * 0.002), round(w * 0.004)))
    lienzo.alpha_composite(capa)

    # CTA
    if a.cta:
        fc = cargar_fuente(a.fuente, round(w * a.tam_cta), negrita=True)
        col_cta = a.color_cta or color_txt
        # Texto del botón relleno: el de la marca (o su fondo) si contrasta con el botón
        txt_cta = next((c for c in (a.texto_marca, a.fondo_marca)
                        if c and abs(luminancia(hex_rgb(c)) - luminancia(hex_rgb(col_cta))) > 90), None)
        pildora(draw, lienzo, a.cta, fc, w // 2 if a.cta_centrado else margen, h - margen - alto_cta // 2,
                col_cta, a.estilo_cta, centrada=a.cta_centrado, color_texto_rellena=txt_cta)

    # Logo arriba a la izquierda
    if a.logo:
        logo = Image.open(a.logo).convert("RGBA")
        ancho_logo = round(w * a.ancho_logo)
        logo = logo.resize((ancho_logo, max(1, round(logo.height * ancho_logo / logo.width))), Image.LANCZOS)
        x_logo = w - margen - logo.width if a.logo_pos == "arriba-derecha" else margen
        lienzo.alpha_composite(logo, (x_logo, margen))

    return lienzo.convert("RGB"), {"tam_l1": f1.size, "renglones_l1": len(r1), "renglones_l2": len(r2),
                                   "aviso": aviso}


def cuadro_de_video(video, t):
    tmp = Path(tempfile.mkdtemp(prefix="placa-")) / "cuadro.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(t), "-i", video, "-frames:v", "1", str(tmp)],
                   check=True, stdin=subprocess.DEVNULL)
    return Image.open(tmp).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texto", required=True)
    fondo_grupo = ap.add_mutually_exclusive_group()
    fondo_grupo.add_argument("--imagen")
    fondo_grupo.add_argument("--video")
    ap.add_argument("--t", type=float, default=0.0, help="segundo del cuadro si se usa --video")
    ap.add_argument("--fondo", help="color liso de fondo (default: colores.fondo de marca.json)")
    ap.add_argument("--foco", default="0.5,0.5", help="x,y (0 a 1) del punto que queda centrado al recortar")
    ap.add_argument("--fuente")
    ap.add_argument("--fuente-acento")
    ap.add_argument("--color", help="color del texto (default: blanco sobre foto, automático sobre color)")
    ap.add_argument("--color-acento", help="color de las *palabras resaltadas*")
    ap.add_argument("--logo")
    ap.add_argument("--ancho-logo", type=float, default=None)
    ap.add_argument("--cta")
    ap.add_argument("--color-cta")
    ap.add_argument("--estilo-cta", choices=["contorno", "rellena"])
    ap.add_argument("--sin-logo", action="store_true")
    ap.add_argument("--sin-cta", action="store_true")
    ap.add_argument("--posicion", choices=["abajo", "centro"], default=None,
                    help="dónde va el bloque de texto (default: marca.json -> placa.posicion o abajo)")
    ap.add_argument("--diferenciales", help='renglón de ítems cortos sobre el botón: "Sin contrato · Sin mínimo · Equipado"')
    ap.add_argument("--etiqueta", help='píldora chica arriba del título: "PROPIEDADES SELECCIONADAS"')
    ap.add_argument("--resaltado", choices=["color", "italica", "caja"],
                    help="cómo se marcan las *palabras*: color, itálica, o itálica sobre recuadro (default: marca.json)")
    ap.add_argument("--formatos", default="1x1,4x5")
    ap.add_argument("--salida", required=True, help="ruta base sin extensión, ej. salida/placas/placa1")
    a = ap.parse_args()

    # Lo que no se pasa por línea de comando sale de marca/marca.json
    m = cargar_marca()
    # Estilo de la placa (marca.json -> "placa"): mayúsculas, resaltado en color o en itálica, logo, CTA, sombra
    a.mayus = g(m, "placa", "mayusculas", defecto=True)
    a.resaltado = a.resaltado or g(m, "placa", "resaltado", defecto="color")
    a.posicion = a.posicion or g(m, "placa", "posicion", defecto="abajo")
    a.color_caja = g(m, "placa", "color_caja")
    a.color_resaltado = g(m, "placa", "color_resaltado")
    a.logo_pos = g(m, "placa", "logo", defecto="arriba-izquierda")
    a.cta_centrado = g(m, "placa", "cta", defecto="izquierda") == "centro"
    a.sombra = g(m, "placa", "sombra", defecto=False)
    a.oscurecer = g(m, "placa", "oscurecer", defecto=215)
    a.velo = g(m, "placa", "velo")              # color del degradado sobre fotos (default negro)
    a.tam_cta = g(m, "placa", "tam_cta", defecto=0.036)
    a.ancho_logo = a.ancho_logo if a.ancho_logo is not None else g(m, "placa", "ancho_logo", defecto=0.22)
    a.texto_marca = g(m, "colores", "texto")
    a.fondo_marca = g(m, "colores", "fondo")
    a.fondo = a.fondo or g(m, "colores", "fondo", defecto="#111111")
    a.fuente = a.fuente or archivo_marca(m, g(m, "fuentes", "principal"))
    a.fuente_acento = a.fuente_acento or archivo_marca(m, g(m, "fuentes", "acento"))
    a.color_acento = a.color_acento or g(m, "colores", "acento")
    a.logo = None if a.sin_logo else (a.logo or archivo_marca(m, g(m, "logo")))
    a.cta = None if a.sin_cta else (a.cta or g(m, "cta", "texto"))
    a.color_cta = a.color_cta or g(m, "cta", "color") or g(m, "colores", "acento")
    a.estilo_cta = a.estilo_cta or g(m, "cta", "estilo", defecto="contorno")
    a.foco = tuple(float(v) for v in a.foco.split(","))
    # Opcionales de marca.json (si no están, la placa queda como siempre)
    a.tam_max = g(m, "placa", "tam_max", defecto=0.13)                    # tamaño máx. del título (fracción del ancho)
    a.l2_ratio = g(m, "placa", "l2_ratio", defecto=0.62)                  # tamaño de L2 respecto de L1
    a.l2_interlineado = g(m, "placa", "l2_interlineado", defecto=1.2)
    a.interlineado = g(m, "placa", "interlineado")                        # interlineado del título (× tamaño)
    a.margen = g(m, "placa", "margen", defecto=0.08)                      # margen lateral (fracción del ancho)
    a.fuente_l2 = archivo_marca(m, g(m, "fuentes", "secundaria")) if g(m, "fuentes", "secundaria") else None
    a.fuente_etiqueta = archivo_marca(m, g(m, "fuentes", "etiqueta")) if g(m, "fuentes", "etiqueta") else None
    a.etiqueta_colores = g(m, "placa", "etiqueta_colores", defecto=[a.color_acento or "#FFFFFF"] * 2)
    a.tinte = g(m, "placa", "tinte")
    if a.etiqueta and g(m, "placa", "etiqueta_mayusculas", defecto=True):
        a.etiqueta = a.etiqueta.upper()
    if a.cta and g(m, "placa", "cta_mayusculas", defecto=False):
        a.cta = a.cta.upper()

    fondo = None
    if a.imagen:
        fondo = Image.open(a.imagen).convert("RGB")
    elif a.video:
        fondo = cuadro_de_video(a.video, a.t)

    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    reporte = {}
    for f in a.formatos.split(","):
        if f not in FORMATOS:
            sys.exit(f"Formato desconocido: {f} (válidos: {', '.join(FORMATOS)})")
        w, h = FORMATOS[f]
        im, info = componer(a, fondo, w, h)
        png = f"{a.salida}_{f}.png"
        im.save(png)
        im.save(f"{a.salida}_{f}.jpg", quality=95)
        reporte[f] = info
        print(f"OK {png} ({w}x{h}) · L1 a {info['tam_l1']} px en {info['renglones_l1']} renglones"
              + (f" · AVISO: {info['aviso']}" if info["aviso"] else ""))
    Path(f"{a.salida}_placa.json").write_text(json.dumps(reporte, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
