#!/usr/bin/env python3
"""Explainer animado: texto que se ilumina al ritmo de la voz + íconos, listas, gráficos y sellos animados.

Uso:
  python3 explainer/explainer.py trabajo-explainer/plan.json             # final
  python3 explainer/explainer.py trabajo-explainer/plan.json --borrador  # mitad de resolución, rápido
  python3 explainer/explainer.py plan.json --formato 4x5                 # 9x16 (default) o 4x5

Usa SU PROPIA marca: explainer/marca/marca.json (otra marca que la de motor/). Se cambia con --marca.

Plan (rutas relativas a la carpeta del plan):
{
  "salida": "salida/explainer.mp4",
  "voz": "voz.mp3",                 (opcional; sin voz, el ritmo se estima)
  "palabras": "palabras.json",      (tiempos de Whisper: motor/transcribir.py)
  "musica": "musica.mp3", "musica_db": -24,   (opcional)
  "escenas": [
    {"texto": "frase literal que dice la voz", "clave": ["palabra"],
     "visual": {"tipo": "...", ...},
     "sello": {"texto": "SE VA", "en": "va"}}          (opcional)
  ],
  "cierre": true                    (logo + CTA de la marca; o {"dur": 3, "cta": "otro"})
}

Tipos de visual (cada elemento puede llevar "en": "<palabra>" para aparecer cuando la voz la dice):
  iconos     {"items": [{"icono": "persona", "etiqueta": "Cliente", "acento": true, "en": "cliente"}], "separador": "o"}
  grupo      {"centro": {"icono": "casa", "etiqueta": "Tu negocio"}, "alrededor": "persona", "cantidad": 6, "en": "todos"}
  lista      {"items": ["¿Por qué?", "¿Para cuándo?", "¿Cuánto?"], "en": ["uno", "dos", "tres"]}
  etiquetas  {"items": ["Aviso", "Cartel", "Colegas"], "icono": "casa", "en": ["aviso", "cartel", "colegas"]}
  grafico    {"puntos": [90, 60, 45, 40], "etiquetas": ["Ene", "Feb", "Mar", "Abr"], "color": "alerta", "en": "después"}
  numero     {"valor": "+20", "etiqueta": "reuniones por mes", "en": "veinte"}
  titulo     {"texto": "¿Quién?", "icono": "moneda"}
  imagen     {"src": "../mis-imagenes/foto.jpg", "alto": 0.8}
Íconos (dibujados por código): persona casa moneda pregunta check cruz reloj calendario mensaje estrella grafico
  puerta celular lupa rayo. O "icono": "ruta/a/mi-icono.png" para usar uno propio.
"""
import argparse
import difflib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ / "motor"))

FORMATOS = {"9x16": (1080, 1920), "4x5": (1080, 1350)}
COLORES_DEF = {"fondo": "#101418", "resplandor": "#23324A", "texto": "#FFFFFF", "texto_tenue": "#6F7A8C",
               "acento": "#FF8A3D", "secundario": "#2F4B6E", "alerta": "#E5484D"}
ICONOS = ["persona", "casa", "moneda", "pregunta", "check", "cruz", "reloj", "calendario", "mensaje", "estrella",
          "grafico", "puerta", "celular", "lupa", "rayo"]


# ----------------------------------------------------------------------------------------------- utilidades
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(p):
    return 1 - (1 - p) ** 3


def ease_out_back(p):
    c1 = 1.70158
    return 1 + (c1 + 1) * (p - 1) ** 3 + c1 * (p - 1) ** 2


def mezclar(c1, c2, p):
    return tuple(round(a + (b - a) * p) for a, b in zip(c1, c2))


class Ctx:
    """Todo lo que comparten las escenas: tamaño, colores, fuentes, zonas."""

    def __init__(self, w, h, marca, base):
        from comun import archivo_marca, g
        from placa import cargar_fuente, hex_rgb
        self.w, self.h, self.base, self.marca = w, h, base, marca
        self.U = min(w, h * 0.62)                       # unidad de tamaño para los visuales
        self.vc = h * (0.58 if h / w > 1.5 else 0.62)   # centro vertical de la zona visual
        self.hex = hex_rgb
        c = dict(COLORES_DEF)
        c.update({k: v for k, v in (g(marca, "colores", defecto={}) or {}).items() if v})
        self.col = {k: hex_rgb(v) for k, v in c.items()}
        self._ruta_f = archivo_marca(marca, g(marca, "fuentes", "principal"))
        self._ruta_fa = archivo_marca(marca, g(marca, "fuentes", "acento"))
        self._cargar = cargar_fuente
        self._cache = {}

    def fuente(self, tam, acento=False):
        k = (round(tam), acento)
        if k not in self._cache:
            self._cache[k] = self._cargar(self._ruta_fa if acento else self._ruta_f, max(8, round(tam)),
                                          negrita=not acento, italica=acento)
        return self._cache[k]


# ----------------------------------------------------------------------------------------------- íconos
def icono(nombre, S, linea, relleno, ctx):
    """Ícono plano S×S (RGBA). Se dibuja al doble y se reduce: bordes suaves."""
    if nombre not in ICONOS:
        ruta = Path(nombre) if Path(nombre).is_absolute() else ctx.base / nombre
        if not ruta.exists():
            sys.exit(f"Ícono desconocido: {nombre} (válidos: {', '.join(ICONOS)} o la ruta a un PNG)")
        im = Image.open(ruta).convert("RGBA")
        im.thumbnail((S, S), Image.LANCZOS)
        out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        out.paste(im, ((S - im.width) // 2, (S - im.height) // 2), im)
        return out
    D = S * 2
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = max(4, round(D * 0.06))
    P = lambda x, y: (x * D, y * D)  # noqa: E731
    B = lambda x0, y0, x1, y1: [x0 * D, y0 * D, x1 * D, y1 * D]  # noqa: E731
    f = ctx.fuente(D * 0.42)
    if nombre == "persona":
        d.ellipse(B(0.33, 0.08, 0.67, 0.42), fill=relleno, outline=linea, width=lw)
        d.rounded_rectangle(B(0.16, 0.50, 0.84, 0.94), radius=D * 0.2, fill=relleno, outline=linea, width=lw)
    elif nombre == "casa":
        d.rectangle(B(0.2, 0.44, 0.8, 0.92), fill=relleno, outline=linea, width=lw)
        d.line([P(0.08, 0.50), P(0.5, 0.12), P(0.92, 0.50)], fill=linea, width=lw, joint="curve")
        d.rectangle(B(0.43, 0.64, 0.57, 0.92), fill=linea)
        d.rectangle(B(0.28, 0.54, 0.37, 0.63), fill=linea)
        d.rectangle(B(0.63, 0.54, 0.72, 0.63), fill=linea)
    elif nombre == "moneda":
        d.ellipse(B(0.08, 0.08, 0.92, 0.92), fill=relleno, outline=linea, width=lw)
        d.text(P(0.5, 0.52), "$", font=f, fill=linea, anchor="mm")
    elif nombre == "pregunta":
        d.rounded_rectangle(B(0.12, 0.12, 0.88, 0.88), radius=D * 0.12, fill=relleno, outline=linea, width=lw)
        d.text(P(0.5, 0.52), "?", font=f, fill=linea, anchor="mm")
    elif nombre in ("check", "cruz"):
        d.ellipse(B(0.08, 0.08, 0.92, 0.92), fill=relleno, outline=linea, width=lw)
        if nombre == "check":
            d.line([P(0.3, 0.52), P(0.45, 0.67), P(0.72, 0.36)], fill=linea, width=lw * 2, joint="curve")
        else:
            d.line([P(0.33, 0.33), P(0.67, 0.67)], fill=linea, width=lw * 2)
            d.line([P(0.67, 0.33), P(0.33, 0.67)], fill=linea, width=lw * 2)
    elif nombre == "reloj":
        d.ellipse(B(0.08, 0.08, 0.92, 0.92), fill=relleno, outline=linea, width=lw)
        d.line([P(0.5, 0.5), P(0.5, 0.24)], fill=linea, width=lw)
        d.line([P(0.5, 0.5), P(0.68, 0.6)], fill=linea, width=lw)
    elif nombre == "calendario":
        d.rounded_rectangle(B(0.1, 0.18, 0.9, 0.9), radius=D * 0.08, fill=relleno, outline=linea, width=lw)
        d.rectangle(B(0.1, 0.18, 0.9, 0.36), fill=linea)
        d.line([P(0.3, 0.08), P(0.3, 0.26)], fill=linea, width=lw)
        d.line([P(0.7, 0.08), P(0.7, 0.26)], fill=linea, width=lw)
        for i in range(3):
            for j in range(2):
                x, y = 0.26 + i * 0.24, 0.52 + j * 0.2
                d.rectangle(B(x - 0.05, y - 0.05, x + 0.05, y + 0.05), fill=linea)
    elif nombre == "mensaje":
        d.rounded_rectangle(B(0.08, 0.14, 0.92, 0.72), radius=D * 0.14, fill=relleno, outline=linea, width=lw)
        d.polygon([P(0.26, 0.68), P(0.22, 0.9), P(0.46, 0.7)], fill=linea)
        for x in (0.32, 0.5, 0.68):
            d.ellipse(B(x - 0.05, 0.38, x + 0.05, 0.48), fill=linea)
    elif nombre == "estrella":
        pts = []
        for k in range(10):
            r = 0.44 if k % 2 == 0 else 0.19
            a = -math.pi / 2 + k * math.pi / 5
            pts.append(P(0.5 + r * math.cos(a), 0.54 + r * math.sin(a)))
        d.polygon(pts, fill=relleno, outline=linea, width=lw)
    elif nombre == "grafico":
        d.line([P(0.1, 0.9), P(0.9, 0.9)], fill=linea, width=lw)
        for x, alto in ((0.2, 0.3), (0.42, 0.5), (0.64, 0.72)):
            d.rectangle(B(x, 0.88 - alto, x + 0.16, 0.88), fill=relleno, outline=linea, width=lw)
    elif nombre == "puerta":
        d.rectangle(B(0.24, 0.08, 0.76, 0.94), fill=relleno, outline=linea, width=lw)
        d.ellipse(B(0.6, 0.5, 0.68, 0.58), fill=linea)
    elif nombre == "celular":
        d.rounded_rectangle(B(0.26, 0.06, 0.74, 0.94), radius=D * 0.08, fill=relleno, outline=linea, width=lw)
        d.line([P(0.44, 0.84), P(0.56, 0.84)], fill=linea, width=lw)
    elif nombre == "lupa":
        d.ellipse(B(0.1, 0.1, 0.64, 0.64), fill=relleno, outline=linea, width=lw)
        d.line([P(0.58, 0.58), P(0.88, 0.88)], fill=linea, width=lw * 2)
    elif nombre == "rayo":
        d.polygon([P(0.56, 0.06), P(0.2, 0.56), P(0.46, 0.56), P(0.38, 0.94), P(0.8, 0.4), P(0.52, 0.4)],
                  fill=relleno, outline=linea, width=lw)
    return im.resize((S, S), Image.LANCZOS)


def pildora_sprite(texto, tam, fondo, color_txt, ctx, contorno=None):
    f = ctx.fuente(tam)
    tw = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(texto, font=f)
    alto, ancho = round(tam * 1.9), round(tw + tam * 1.6)
    D = 2
    im = Image.new("RGBA", (ancho * D, alto * D), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, ancho * D - 1, alto * D - 1], radius=alto * D // 2, fill=fondo,
                        outline=contorno, width=(4 if contorno else 0))
    d.text((ancho * D / 2, alto * D / 2), texto, font=ctx.fuente(tam * D), fill=color_txt, anchor="mm")
    return im.resize((ancho, alto), Image.LANCZOS)


def texto_sprite(texto, tam, color, ctx, acento=False):
    f = ctx.fuente(tam, acento)
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), texto, font=f)
    im = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), texto, font=f, fill=color)
    return im


def apilar(sprites, sep):
    """Une sprites uno debajo del otro, centrados."""
    W = max(s.width for s in sprites)
    H = sum(s.height for s in sprites) + sep * (len(sprites) - 1)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = 0
    for s in sprites:
        out.paste(s, ((W - s.width) // 2, y), s)
        y += s.height + sep
    return out


# ----------------------------------------------------------------------------------------------- elementos
class Sprite:
    def __init__(self, im, cx, cy, t0, anim="pop"):
        self.im, self.cx, self.cy, self.t0, self.anim = im, cx, cy, t0, anim

    def pintar(self, frame, t, t_fin):
        if t < self.t0:
            return
        dur = 0.28 if self.anim == "slam" else 0.38
        p = clamp((t - self.t0) / dur)
        if self.anim == "slam":
            s, a = 1.7 - 0.7 * ease_out(p), clamp(p * 3)
        elif self.anim == "fade":
            s, a = 1.0, ease_out(p)
        else:
            s, a = max(0.05, ease_out_back(p)), clamp(p * 2.5)
        a *= clamp((t_fin - t) / 0.16)
        if a <= 0.01:
            return
        im = self.im
        if abs(s - 1) > 0.01:
            im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.BILINEAR)
        if a < 0.99:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: round(v * a)))
        frame.paste(im, (round(self.cx - im.width / 2), round(self.cy - im.height / 2)), im)


class Grafico:
    def __init__(self, vis, ctx, t0):
        self.ctx, self.t0 = ctx, t0
        v = [float(x) for x in vis["puntos"]]
        self.etq = vis.get("etiquetas", [])
        baja = v[-1] < v[0]
        self.color = ctx.col.get(vis.get("color") or ("alerta" if baja else "acento"), ctx.col["acento"])
        w, U, vc = ctx.w, ctx.U, ctx.vc
        self.x0, self.x1 = w / 2 - U * 0.4, w / 2 + U * 0.4
        self.y0, self.y1 = vc - U * 0.26, vc + U * 0.18
        lo, hi = min(v), max(v)
        rng = (hi - lo) or 1
        n = len(v)
        self.pts = [(self.x0 + (self.x1 - self.x0) * i / max(n - 1, 1),
                     self.y1 - (self.y1 - self.y0) * (0.1 + 0.85 * (x - lo) / rng)) for i, x in enumerate(v)]

    def pintar(self, frame, t, t_fin):
        if t < self.t0:
            return
        d = ImageDraw.Draw(frame)
        ctx = self.ctx
        lw = max(4, round(ctx.U * 0.012))
        d.line([(self.x0, self.y1 + lw * 2), (self.x1, self.y1 + lw * 2)], fill=ctx.col["secundario"], width=lw // 2)
        f = ctx.fuente(ctx.U * 0.04)
        for i, (x, _) in enumerate(self.pts):
            if i < len(self.etq):
                d.text((x, self.y1 + lw * 5), str(self.etq[i]), font=f, fill=ctx.col["texto_tenue"], anchor="mt")
        p = ease_out(clamp((t - self.t0) / 1.4)) * (len(self.pts) - 1)
        k = int(p)
        recorrido = self.pts[:k + 1]
        if k < len(self.pts) - 1:
            (ax, ay), (bx, by) = self.pts[k], self.pts[k + 1]
            q = p - k
            recorrido = recorrido + [(ax + (bx - ax) * q, ay + (by - ay) * q)]
        if len(recorrido) > 1:
            d.line(recorrido, fill=self.color, width=lw, joint="curve")
        r = lw * 1.6
        for x, y in self.pts[:k + 1]:
            d.ellipse([x - r, y - r, x + r, y + r], fill=self.color)


class Numero:
    def __init__(self, vis, ctx, t0):
        self.ctx, self.t0 = ctx, t0
        m = re.match(r"^(\D*)(\d+(?:[.,]\d+)?)(.*)$", str(vis["valor"]))
        self.pre, self.num, self.suf = (m.group(1), m.group(2), m.group(3)) if m else (str(vis["valor"]), None, "")
        self.etq = vis.get("etiqueta", "")

    def pintar(self, frame, t, t_fin):
        if t < self.t0:
            return
        ctx = self.ctx
        p = clamp((t - self.t0) / 0.9)
        if self.num:
            dec = len(self.num.replace(",", ".").split(".")[1]) if re.search(r"[.,]", self.num) else 0
            val = float(self.num.replace(",", ".")) * ease_out(p)
            txt = f"{self.pre}{val:.{dec}f}{self.suf}"
        else:
            txt = self.pre
        s = max(0.3, ease_out_back(clamp((t - self.t0) / 0.38)))
        d = ImageDraw.Draw(frame)
        d.text((ctx.w / 2, ctx.vc - ctx.U * 0.05), txt, font=ctx.fuente(ctx.U * 0.26 * s), fill=ctx.col["acento"],
               anchor="mm")
        if self.etq and p > 0.3:
            d.text((ctx.w / 2, ctx.vc + ctx.U * 0.17), self.etq, font=ctx.fuente(ctx.U * 0.06),
                   fill=mezclar(ctx.col["fondo"], ctx.col["texto"], clamp((p - 0.3) * 3)), anchor="mm")


# ----------------------------------------------------------------------------------------------- visuales
def construir_visual(vis, ctx, cue, t_ini, t_fin):
    """Devuelve la lista de elementos (Sprite / Grafico / Numero) de una escena."""
    tipo = vis.get("tipo")
    w, U, vc, C = ctx.w, ctx.U, ctx.vc, ctx.col
    dur = max(0.6, t_fin - t_ini)
    els = []

    def t_de(item, i, n, en=None):
        en = en if en is not None else (item.get("en") if isinstance(item, dict) else None)
        return cue(en, t_ini + 0.25 + i * min(0.45, dur * 0.7 / max(n, 1)))

    if tipo == "iconos":
        items = vis["items"]
        n = len(items)
        S = round(min(U * 0.30, U * 0.84 / n * 0.72))
        gap = S * 0.55
        total = n * S + (n - 1) * gap
        x = w / 2 - total / 2 + S / 2
        for i, it in enumerate(items):
            ac = it.get("acento", False)
            partes = [icono(it["icono"], S, C["acento"] if ac else C["texto"], C["secundario"], ctx)]
            if it.get("etiqueta"):
                partes.append(pildora_sprite(it["etiqueta"].upper(), S * 0.11, C["acento"] if ac else C["secundario"],
                                             C["fondo"] if ac else C["texto"], ctx))
            ti = t_de(it, i, n)
            els.append(Sprite(apilar(partes, round(S * 0.1)), x, vc, ti))
            if vis.get("separador") and i < n - 1:
                els.append(Sprite(texto_sprite(vis["separador"], S * 0.3, C["texto_tenue"], ctx),
                                  x + S / 2 + gap / 2, vc - S * 0.12, ti + 0.15, "fade"))
            x += S + gap
    elif tipo == "grupo":
        t0 = cue(vis.get("en"), t_ini + 0.25)
        c = vis.get("centro", {"icono": "persona"})
        S = round(U * 0.24)
        anillo = Image.new("RGBA", (round(U * 0.95), round(U * 0.95)), (0, 0, 0, 0))
        da = ImageDraw.Draw(anillo)
        for r in (0.47, 0.32):
            m = anillo.width * (0.5 - r)
            da.ellipse([m, m, anillo.width - m, anillo.width - m], outline=C["secundario"], width=3)
        els.append(Sprite(anillo, w / 2, vc, t_ini + 0.1, "fade"))
        partes = [icono(c["icono"], S, C["acento"], C["secundario"], ctx)]
        if c.get("etiqueta"):
            partes.append(pildora_sprite(c["etiqueta"].upper(), S * 0.12, C["acento"], C["fondo"], ctx))
        els.append(Sprite(apilar(partes, round(S * 0.08)), w / 2, vc, t_ini + 0.2))
        n = int(vis.get("cantidad", 6))
        s = round(U * 0.1)
        chico = icono(vis.get("alrededor", "persona"), s, C["texto"], C["secundario"], ctx)
        for k in range(n):
            a = -math.pi / 2 + (k + 0.5) * 2 * math.pi / n
            els.append(Sprite(chico, w / 2 + math.cos(a) * U * 0.40, vc + math.sin(a) * U * 0.40, t0 + 0.07 * k))
    elif tipo == "lista":
        items = vis["items"]
        n = len(items)
        ens = vis.get("en") or [None] * n
        fila = U * 0.15
        y = vc - fila * (n - 1) / 2
        # Mismo tamaño para todos los ítems, achicado si el más largo no entra en el renglón
        disponible = U * 0.84 - fila * 0.62 * 1.35
        tam_item = U * 0.055
        mas_ancho = max(texto_sprite(t, tam_item, C["texto"], ctx).width for t in items)
        if mas_ancho > disponible:
            tam_item *= disponible / mas_ancho
        for i, txt in enumerate(items):
            num = Image.new("RGBA", (round(fila * 0.62),) * 2, (0, 0, 0, 0))
            dn = ImageDraw.Draw(num)
            dn.ellipse([0, 0, num.width - 1, num.height - 1], fill=C["acento"])
            dn.text((num.width / 2, num.height / 2), str(i + 1), font=ctx.fuente(num.width * 0.55), fill=C["fondo"],
                    anchor="mm")
            t_s = texto_sprite(txt, tam_item, C["texto"], ctx)
            row = Image.new("RGBA", (round(U * 0.84), round(fila)), (0, 0, 0, 0))
            row.paste(num, (0, (row.height - num.height) // 2), num)
            row.paste(t_s, (round(num.width * 1.35), (row.height - t_s.height) // 2), t_s)
            els.append(Sprite(row, w / 2, y, t_de({}, i, n, ens[i] if i < len(ens) else None)))
            y += fila
    elif tipo == "etiquetas":
        items = vis["items"]
        n = len(items)
        ens = vis.get("en") or [None] * n
        pills = [pildora_sprite(t.upper(), U * 0.045, C["acento"], C["fondo"], ctx) for t in items]
        y = vc - U * 0.22 if vis.get("icono") else vc
        gap = U * 0.03
        filas, actual, ancho = [], [], 0
        for p in pills:
            if actual and ancho + gap + p.width > U * 0.9:
                filas.append(actual)
                actual, ancho = [], 0
            actual.append(p)
            ancho += p.width + (gap if len(actual) > 1 else 0)
        filas.append(actual)
        i = 0
        for fila_p in filas:
            total = sum(p.width for p in fila_p) + gap * (len(fila_p) - 1)
            x = w / 2 - total / 2
            for p in fila_p:
                els.append(Sprite(p, x + p.width / 2, y, t_de({}, i, n, ens[i] if i < len(ens) else None)))
                x += p.width + gap
                i += 1
            y += pills[0].height + gap
        if vis.get("icono"):
            S = round(U * 0.3)
            els.append(Sprite(icono(vis["icono"], S, C["acento"], C["secundario"], ctx), w / 2, vc + U * 0.12,
                              t_ini + 0.2))
    elif tipo == "grafico":
        els.append(Grafico(vis, ctx, cue(vis.get("en"), t_ini + 0.3)))
    elif tipo == "numero":
        els.append(Numero(vis, ctx, cue(vis.get("en"), t_ini + 0.25)))
    elif tipo == "titulo":
        tam = U * 0.13
        t_s = texto_sprite(vis["texto"].upper(), tam, C["acento"], ctx)
        while t_s.width > w * 0.86 and tam > U * 0.05:  # se achica hasta entrar
            tam *= 0.92
            t_s = texto_sprite(vis["texto"].upper(), tam, C["acento"], ctx)
        t0 = cue(vis.get("en"), t_ini + 0.25)
        if vis.get("icono"):
            S = round(U * 0.26)
            ic = icono(vis["icono"], S, C["acento"], C["secundario"], ctx)
            els.append(Sprite(ic, w / 2, vc - U * 0.12, t0))
            els.append(Sprite(t_s, w / 2, vc + U * 0.14, t0 + 0.15))
        else:
            els.append(Sprite(t_s, w / 2, vc, t0))
    elif tipo == "imagen":
        ruta = ctx.base / vis["src"]
        if not ruta.exists():
            sys.exit(f"No existe {ruta}")
        cw = round(U * 0.78)
        ch = round(cw * float(vis.get("alto", 0.9)))
        foto = ImageOps.fit(Image.open(ruta).convert("RGB"), (cw, ch), centering=tuple(vis.get("foco", (0.5, 0.5))))
        mask = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=round(cw * 0.05), fill=255)
        card = Image.new("RGBA", (cw + 12, ch + 12), (0, 0, 0, 0))
        ImageDraw.Draw(card).rounded_rectangle([0, 0, cw + 11, ch + 11], radius=round(cw * 0.05) + 6,
                                               fill=C["secundario"])
        card.paste(foto, (6, 6), mask)
        els.append(Sprite(card, w / 2, vc, cue(vis.get("en"), t_ini + 0.25)))
    elif tipo:
        sys.exit(f"Tipo de visual desconocido: {tipo}")
    return els


def sello_sprite(sello, ctx):
    color = ctx.col.get(sello.get("color", "alerta"), ctx.col["alerta"])
    tam = ctx.U * 0.075
    f = ctx.fuente(tam)
    txt = sello["texto"].upper()
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), txt, font=f)
    pad = tam * 0.35
    W, H = round(bb[2] - bb[0] + pad * 2), round(bb[3] - bb[1] + pad * 2)
    im = Image.new("RGBA", (W + 10, H + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([5, 5, W + 4, H + 4], radius=round(tam * 0.18), fill=ctx.col["fondo"] + (235,),
                        outline=color, width=max(4, round(tam * 0.09)))
    d.text((5 + pad - bb[0], 5 + pad - bb[1]), txt, font=f, fill=color)
    return im.rotate(float(sello.get("giro", 6)), resample=Image.BICUBIC, expand=True)


# ----------------------------------------------------------------------------------------------- texto
class Texto:
    """Frase de arriba: cada palabra pasa de tenue a blanca cuando la voz la dice; las clave, con recuadro."""

    def __init__(self, palabras, tiempos, claves, ctx):
        self.ctx = ctx
        from comun import normalizar
        tam = ctx.w * 0.058
        self.f = ctx.fuente(tam)
        d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        esp = d.textlength(" ", font=self.f)
        ancho_max = ctx.w * 0.84
        renglones, actual, ancho = [], [], 0
        for i, p in enumerate(palabras):
            pw = d.textlength(p, font=self.f)
            if actual and ancho + esp + pw > ancho_max:
                renglones.append((actual, ancho))
                actual, ancho = [], 0
            ancho += (esp if actual else 0) + pw
            actual.append((p, pw, i))
        if actual:
            renglones.append((actual, ancho))
        claves_n = {normalizar(c) for clave in claves for c in clave.split()}
        self.items = []
        alto_r = tam * 1.28
        y = ctx.h * (0.085 if ctx.h / ctx.w > 1.5 else 0.06)
        for fila, ancho in renglones:
            x = (ctx.w - ancho) / 2
            for p, pw, i in fila:
                self.items.append((p, x, y, pw, tiempos[i], normalizar(p) in claves_n))
                x += pw + esp
            y += alto_r
        self.tam = tam

    def pintar(self, frame, t):
        d = ImageDraw.Draw(frame)
        C = self.ctx.col
        for p, x, y, pw, tw, clave in self.items:
            q = clamp((t - tw) / 0.12)
            if clave and q > 0:
                pad = self.tam * 0.14
                d.rounded_rectangle([x - pad, y - pad * 0.6, x + pw + pad, y + self.tam * 1.12 + pad * 0.2],
                                    radius=round(pad), outline=mezclar(C["fondo"], C["acento"], q),
                                    width=max(3, round(self.tam * 0.05)))
            d.text((x, y), p, font=self.f, fill=mezclar(C["texto_tenue"], C["texto"], q))


# ----------------------------------------------------------------------------------------------- tiempos
def tiempos_palabras(tokens, palabras):
    """Inicio de cada palabra del guion según Whisper (alineación tolerante; las que faltan se interpolan)."""
    from comun import normalizar
    g_n = [normalizar(t) for t in tokens]
    w_n = [normalizar(p["palabra"]) for p in palabras]
    t = [None] * len(tokens)
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(a=g_n, b=w_n, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace" and a2 - a1 == b2 - b1):
            for k in range(a2 - a1):
                t[a1 + k] = palabras[b1 + k]["inicio"]
    ok = sum(1 for x in t if x is not None)
    fin = palabras[-1]["fin"] if palabras else 0
    for i in range(len(t)):
        if t[i] is None:
            prev_i = next((j for j in range(i - 1, -1, -1) if t[j] is not None), None)
            sig_i = next((j for j in range(i + 1, len(t)) if t[j] is not None), None)
            a = t[prev_i] if prev_i is not None else 0.0
            b = t[sig_i] if sig_i is not None else fin
            ia = prev_i if prev_i is not None else -1
            ib = sig_i if sig_i is not None else len(t)
            t[i] = a + (b - a) * (i - ia) / (ib - ia)
    for i in range(1, len(t)):
        t[i] = max(t[i], t[i - 1])
    return t, ok, fin


def tiempos_estimados(escenas_tokens):
    """Sin voz: ritmo de lectura cómodo."""
    t, out = 0.4, []
    for toks in escenas_tokens:
        for p in toks:
            out.append(t)
            t += 0.26 + 0.03 * len(p)
        t += 0.9
    return out, t


# ----------------------------------------------------------------------------------------------- render
def fondo_base(ctx):
    w, h, C = ctx.w, ctx.h, ctx.col
    bg = Image.new("RGB", (w, h), C["fondo"])
    lado = round(w * 1.5)
    m = ImageOps.invert(Image.radial_gradient("L")).resize((lado, lado), Image.BICUBIC)
    m = m.point(lambda v: round(215 * (v / 255) ** 2.2))
    bg.paste(Image.new("RGB", (lado, lado), C["resplandor"]), (round(w / 2 - lado / 2), round(ctx.vc - lado / 2)), m)
    return bg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--borrador", action="store_true")
    ap.add_argument("--formato", default="9x16", choices=list(FORMATOS))
    ap.add_argument("--marca", default=str(AQUI / "marca" / "marca.json"),
                    help="marca del explainer (default explainer/marca/marca.json)")
    a = ap.parse_args()

    os.environ["MOTOR_MARCA"] = str(Path(a.marca).resolve())
    from comun import archivo_marca, cargar_marca, duracion, g
    from placa import pildora
    marca = cargar_marca()
    if not marca:
        print(f"AVISO: no encontré {a.marca}: uso colores neutros")

    ruta_plan = Path(a.plan).resolve()
    base = ruta_plan.parent
    plan = json.loads(ruta_plan.read_text(encoding="utf-8"))
    W, H = FORMATOS[a.formato]
    w, h = (W // 2, H // 2) if a.borrador else (W, H)
    ctx = Ctx(w, h, marca, base)
    fps = plan.get("fps", 30)

    # --- tiempos de cada palabra
    escenas = plan["escenas"]
    toks_por_escena = [e["texto"].split() for e in escenas]
    tokens = [p for toks in toks_por_escena for p in toks]
    if plan.get("palabras") and (base / plan["palabras"]).exists():
        palabras = json.loads((base / plan["palabras"]).read_text(encoding="utf-8"))
        tiempos, ok, fin_voz = tiempos_palabras(tokens, palabras)
        print(f"Palabras del guion encontradas en la voz: {ok}/{len(tokens)}")
        if tokens and ok / len(tokens) < 0.7:
            print("AVISO: menos del 70 % coincide. ¿La voz dice el mismo texto que las escenas?")
    else:
        tiempos, fin_voz = tiempos_estimados(toks_por_escena)
        print("Sin palabras.json: ritmo estimado")
    if plan.get("voz"):
        fin_voz = max(fin_voz, duracion(base / plan["voz"]))

    # --- escenas: inicio, fin, texto, elementos
    from comun import normalizar
    idx, inicios = 0, []
    rangos = []
    for toks in toks_por_escena:
        rangos.append((idx, idx + len(toks)))
        inicios.append(tiempos[idx] if toks else 0)
        idx += len(toks)
    inicios[0] = 0.0
    fin_contenido = fin_voz + 0.5
    render = []
    for i, e in enumerate(escenas):
        t_ini = inicios[i]
        t_fin = inicios[i + 1] if i + 1 < len(escenas) else fin_contenido
        r0, r1 = rangos[i]

        def cue(palabra, defecto, r0=r0, r1=r1, n=i):
            if not palabra:
                return defecto
            objetivo = normalizar(str(palabra).split()[0])
            for k in range(r0, r1):
                if normalizar(tokens[k]) == objetivo or normalizar(tokens[k]).startswith(objetivo):
                    return tiempos[k]
            print(f"  AVISO escena {n + 1}: «{palabra}» no está en su texto; aparece por defecto")
            return defecto

        texto = Texto(tokens[r0:r1], tiempos[r0:r1], e.get("clave", []), ctx)
        els = construir_visual(e.get("visual", {}), ctx, cue, t_ini, t_fin)
        if e.get("sello"):
            pos = e["sello"].get("pos", "abajo")
            y = ctx.vc + ctx.U * 0.40 if pos == "abajo" else ctx.vc
            els.append(Sprite(sello_sprite(e["sello"], ctx), w / 2, y, cue(e["sello"].get("en"), t_ini + 0.6), "slam"))
        render.append((t_ini, t_fin, texto, els))
        print(f"  escena {i + 1:02d}  {t_ini:6.2f}-{t_fin:6.2f}  {e.get('visual', {}).get('tipo', '-'):9s} {e['texto'][:50]}")

    # --- cierre
    cierre_els, t_cierre, total = [], fin_contenido, fin_contenido
    if plan.get("cierre"):
        c = plan["cierre"] if isinstance(plan["cierre"], dict) else {}
        logo = archivo_marca(marca, c.get("logo") or g(marca, "logo"))
        if not logo:
            print("AVISO: sin logo en la marca del explainer: no hay cierre")
        else:
            dur_c = float(c.get("dur", 2.5))
            total = t_cierre + dur_c
            lg = Image.open(logo).convert("RGBA")
            lw_ = round(w * 0.5)
            lg = lg.resize((lw_, max(1, round(lg.height * lw_ / lg.width))), Image.LANCZOS)
            cierre_els.append(Sprite(lg, w / 2, ctx.vc - ctx.U * 0.08, t_cierre + 0.1))
            cta = c.get("cta") or g(marca, "cta", "texto")
            if cta:
                lienzo = Image.new("RGBA", (w, round(w * 0.2)), (0, 0, 0, 0))
                caja = pildora(ImageDraw.Draw(lienzo), lienzo, cta, ctx.fuente(w * 0.045), w // 2, lienzo.height // 2,
                               g(marca, "cta", "color") or "#%02x%02x%02x" % ctx.col["acento"],
                               g(marca, "cta", "estilo", defecto="rellena"), centrada=True)
                spr = lienzo.crop(tuple(round(v) for v in caja))
                cierre_els.append(Sprite(spr, w / 2, ctx.vc + ctx.U * 0.16, t_cierre + 0.45))

    # --- salida
    salida = base / plan.get("salida", "salida/explainer.mp4")
    salida = salida.with_name(f"{salida.stem}_{a.formato}{'_borrador' if a.borrador else ''}{salida.suffix}")
    salida.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
           "-r", str(fps), "-i", "-"]
    filtros, mezcla, n = [], [], 1
    if plan.get("voz"):
        cmd += ["-i", str(base / plan["voz"])]
        filtros.append(f"[{n}:a]loudnorm=I=-16:TP=-1.5:LRA=11,apad[voz]")
        mezcla.append("[voz]")
        n += 1
    if plan.get("musica"):
        cmd += ["-stream_loop", "-1", "-i", str(base / plan["musica"])]
        filtros.append(f"[{n}:a]volume={plan.get('musica_db', -24)}dB,afade=t=in:d=0.8,"
                       f"afade=t=out:st={max(total - 1.2, 0):.2f}:d=1.2[mus]")
        mezcla.append("[mus]")
    if mezcla:
        filtros.append(f"{mezcla[0]}anull[a]" if len(mezcla) == 1 else
                       f"{''.join(mezcla)}amix=inputs={len(mezcla)}:duration=longest:normalize=0[a]")
        cmd += ["-filter_complex", ";".join(filtros), "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast" if a.borrador else "medium",
            "-crf", "28" if a.borrador else "18", "-t", f"{total:.3f}", "-movflags", "+faststart", str(salida)]

    bg = fondo_base(ctx)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n_frames = math.ceil(total * fps)
    try:
        for fi in range(n_frames):
            t = fi / fps
            frame = bg.copy()
            if t >= t_cierre and cierre_els:
                for el in cierre_els:
                    el.pintar(frame, t, total + 1)
            else:
                for t_ini, t_fin, texto, els in render:
                    if t_ini <= t < t_fin:
                        texto.pintar(frame, t)
                        for el in els:
                            el.pintar(frame, t, t_fin)
                        break
            proc.stdin.write(frame.tobytes())
            if fi % (fps * 5) == 0:
                print(f"  {t:5.1f}s / {total:.1f}s", flush=True)
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        sys.exit("ffmpeg falló al armar el explainer")
    print(f"OK {salida} · {w}x{h} · {total:.2f}s")


if __name__ == "__main__":
    main()
