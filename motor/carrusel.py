#!/usr/bin/env python3
"""Carruseles: varias placas con un mismo diseño, numeradas, con portada y cierre. Sale PNG + JPG por placa,
un PDF (para LinkedIn) y una vista previa.

Uso:
  python3 motor/carrusel.py trabajo/carrusel.json                      # 4:5 (default)
  python3 motor/carrusel.py trabajo/carrusel.json --formato 1x1
  python3 motor/carrusel.py trabajo/carrusel.json --marca explainer/marca/marca.json   # con la otra marca

Plan (rutas relativas a la carpeta del plan; modelo completo en ejemplo/carrusel.json):
{
  "nombre": "errores-comunes",            -> salida/carruseles/errores-comunes/
  "placas": [
    {"tipo": "portada", "titulo": "5 errores que *te hacen perder* clientes", "bajada": "El 3 es el más común",
     "imagen": "../mis-imagenes/foto.jpg"},                                   (imagen opcional)
    {"tipo": "texto", "numero": "01", "titulo": "Responder tarde", "cuerpo": "El 78 % compra al primero que contesta."},
    {"tipo": "lista", "titulo": "Antes de cotizar, preguntá:", "items": ["¿Qué necesita?", "¿Para cuándo?"]},
    {"tipo": "dato", "valor": "+20", "etiqueta": "reuniones por mes", "nota": "Promedio de nuestros clientes", "fondo": "acento"},
    {"tipo": "imagen", "imagen": "../mis-imagenes/equipo.jpg", "titulo": "Así trabajamos", "cuerpo": "..."},
    {"tipo": "cita", "texto": "Desde que ordenamos el seguimiento, cerramos el doble.", "autor": "Cliente, rubro X"},
    {"tipo": "cierre", "titulo": "¿Te sirvió?", "cta": "Escribinos", "bajada": "Guardalo para después"}
  ]
}
- En títulos, *palabras* van en el color de acento (y en itálica si marca.json -> placa.resaltado es "italica").
- Mayúsculas en portada y cierre salvo que marca.json -> placa.mayusculas sea false.
- "fondo" por placa (opcional): "acento", "claro" o un "#hex" — para cortar el ritmo en una placa clave.
- Colores, fuentes, logo y CTA salen de la marca. En marca.json es opcional "fuentes": {"cuerpo": "..."} (texto corrido)
  y "logo_sobre_claro" (versión del logo para fondos claros).
"""
import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))

FORMATOS = {"4x5": (1080, 1350), "1x1": (1080, 1080)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--formato", default="4x5", choices=list(FORMATOS))
    ap.add_argument("--marca", help="otra marca.json (default: marca/marca.json)")
    ap.add_argument("--salida", help="carpeta de salida (default: salida/carruseles/<nombre> junto al plan)")
    a = ap.parse_args()
    if a.marca:
        os.environ["MOTOR_MARCA"] = str(Path(a.marca).resolve())

    from comun import archivo_marca, cargar_marca, g, tokens_resaltados
    from placa import cargar_fuente, cubrir, degradado, hex_rgb, luminancia, partir, partir_mixto, pildora

    m = cargar_marca()
    ruta_plan = Path(a.plan).resolve()
    base = ruta_plan.parent
    plan = json.loads(ruta_plan.read_text(encoding="utf-8"))
    placas = plan["placas"]
    N = len(placas)
    W, H = FORMATOS[a.formato]
    M = round(W * 0.08)
    salida = Path(a.salida) if a.salida else base / "salida" / "carruseles" / plan.get("nombre", ruta_plan.stem)
    salida.mkdir(parents=True, exist_ok=True)

    FONDO = hex_rgb(g(m, "colores", "fondo", defecto="#111111"))
    TEXTO = hex_rgb(g(m, "colores", "texto", defecto="#FFFFFF"))
    ACENTO = hex_rgb(g(m, "colores", "acento", defecto="#FFC400"))
    f_princ = archivo_marca(m, g(m, "fuentes", "principal"))
    f_acento = archivo_marca(m, g(m, "fuentes", "acento"))
    f_cuerpo = archivo_marca(m, g(m, "fuentes", "cuerpo")) or f_princ
    logo_osc = archivo_marca(m, g(m, "logo"))
    logo_cla = archivo_marca(m, g(m, "logo_sobre_claro")) or logo_osc
    cta_def = g(m, "cta", "texto")
    # Estilo de la marca (marca.json -> "placa"): títulos en mayúsculas o no, resaltado en color o en itálica
    MAYUS = g(m, "placa", "mayusculas", defecto=True)
    ITAL = g(m, "placa", "resaltado", defecto="color") in ("italica", "caja")
    estilo_cta = g(m, "cta", "estilo", defecto="rellena")
    cache = {}
    avisos = []

    def fuente(ruta, tam, italica=False):
        k = (ruta, round(tam), italica)
        if k not in cache:
            cache[k] = cargar_fuente(ruta, max(10, round(tam)), negrita=not italica, italica=italica)
        return cache[k]

    def hexs(rgb):
        return "#%02x%02x%02x" % rgb

    def mezcla(c1, c2, p):
        return tuple(round(x + (y - x) * p) for x, y in zip(c1, c2))

    def tokens(texto, mayus):
        return tokens_resaltados(texto, mayus)

    D = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def ajustar(texto, ruta, ancho, alto_max, tam_max, tam_min, mayus=False, inter=1.1, italica=False, que=""):
        toks = tokens(texto, mayus and MAYUS)
        mixto = ITAL and not italica and f_acento and any(r for _, r in toks)
        tam = tam_max
        while True:
            f = fuente(ruta, tam, italica)
            fi = fuente(f_acento, tam * 1.06, True) if mixto else f
            r, ancho_r = partir_mixto(toks, lambda res, f=f, fi=fi: fi if res else f, ancho, D)
            alto = len(r) * tam * inter
            entra = all(ancho_r(x) <= ancho for x in r)
            if (alto <= alto_max and entra) or tam <= tam_min:
                if alto > alto_max or not entra:
                    avisos.append(f"{que}: el texto no entra ni al tamaño mínimo, acortalo")
                return {"f": f, "fi": fi, "r": r, "alto": alto, "paso": tam * inter, "ancho": ancho_r}
            tam -= 2

    def dibujar(d, b, x, y, color, resalte, centrado=False):
        asc = b["f"].getmetrics()[0]
        for renglon in b["r"]:
            ancho = b["ancho"](renglon)
            xx = x - ancho / 2 if centrado else x
            for t, res in renglon:
                f = b["fi"] if res else b["f"]
                d.text((xx, y + asc), t, font=f, fill=resalte if res else color, anchor="ls")
                xx += d.textlength(t, font=f) + d.textlength(" ", font=f)
            y += b["paso"]
        return y

    def colores_de(fondo_pedido, hay_foto):
        """Fondo, texto, resalte y tenue según el fondo de la placa (contraste automático)."""
        if hay_foto:
            # Sobre foto: con resaltado en itálica va en el color de texto de la marca (se lee mejor que el acento)
            return FONDO, (TEXTO if ITAL else (255, 255, 255)), (TEXTO if ITAL else ACENTO), (220, 220, 220), False
        if fondo_pedido == "acento":
            bg = ACENTO
        elif fondo_pedido == "claro":
            bg = (245, 243, 238)
        elif fondo_pedido and fondo_pedido.startswith("#"):
            bg = hex_rgb(fondo_pedido)
        else:
            bg = FONDO
        claro = luminancia(bg) > 150
        txt = (FONDO if luminancia(FONDO) < 90 else (17, 17, 17)) if claro else TEXTO
        if claro and luminancia(TEXTO) < 90:
            txt = TEXTO
        res = ACENTO
        if bg == ACENTO or abs(luminancia(ACENTO) - luminancia(bg)) < 60:
            res = txt  # acento sobre acento no se ve: se resalta con el color del texto
        return bg, txt, res, mezcla(txt, bg, 0.4), claro

    def pegar_logo(lienzo, ruta, ancho, x, y, centrado=False):
        if not ruta:
            return 0
        lg = Image.open(ruta).convert("RGBA")
        lg = lg.resize((ancho, max(1, round(lg.height * ancho / lg.width))), Image.LANCZOS)
        lienzo.alpha_composite(lg, (round(x - lg.width / 2) if centrado else x, y))
        return lg.height

    zona_top = M + round(H * 0.09)
    zona_bot = H - M - round(H * 0.07)
    ancho_txt = W - 2 * M
    hojas = []

    for i, p in enumerate(placas, 1):
        tipo = p.get("tipo", "texto")
        foto = None
        if p.get("imagen"):
            ruta = base / p["imagen"]
            if not ruta.exists():
                sys.exit(f"Placa {i}: no existe {ruta}")
            foco = tuple(p.get("foco", (0.5, 0.5)))
            foto = cubrir(Image.open(ruta).convert("RGB"), W, H, foco)
        bg, txt, res, tenue, claro = colores_de(p.get("fondo"), foto is not None)
        lienzo = Image.new("RGBA", (W, H), bg + (255,))
        if foto is not None:
            lienzo = foto.convert("RGBA")
            lienzo.alpha_composite(degradado(W, H, desde=0.15 if tipo == "portada" else 0.3, alfa_max=230))
        d = ImageDraw.Draw(lienzo)
        que = f"Placa {i} ({tipo})"

        # --- encabezado: logo chico (menos en el cierre)
        if tipo != "cierre":
            pegar_logo(lienzo, logo_cla if claro else logo_osc, round(W * 0.16), M, M)

        alto_util = zona_bot - zona_top
        if tipo == "portada":
            bajada = None
            if p.get("bajada"):
                bajada = ajustar(p["bajada"], f_acento, ancho_txt, H * 0.14, W * 0.05, W * 0.035, italica=True, que=que)
            tit = ajustar(p["titulo"], f_princ, ancho_txt, alto_util * 0.62, W * 0.13, W * 0.06, mayus=True,
                          inter=1.04, que=que)
            total = tit["alto"] + ((bajada["alto"] + W * 0.03) if bajada else 0)
            y = zona_bot - total - H * 0.02
            y = dibujar(d, tit, M, y, txt, res)
            if bajada:
                dibujar(d, bajada, M, y + W * 0.03, res, res)
        elif tipo in ("texto", "imagen"):
            bloques = []
            if p.get("numero"):
                bloques.append(("num", ajustar(p["numero"], f_princ, ancho_txt, W * 0.2, W * 0.16, W * 0.1, que=que)))
            if p.get("titulo"):
                bloques.append(("tit", ajustar(p["titulo"], f_princ, ancho_txt, alto_util * 0.4, W * 0.085, W * 0.05,
                                               que=que)))
            if p.get("cuerpo"):
                bloques.append(("cue", ajustar(p["cuerpo"], f_cuerpo, ancho_txt, alto_util * 0.45, W * 0.048,
                                               W * 0.034, inter=1.35, que=que)))
            sep = W * 0.035
            total = sum(b["alto"] for _, b in bloques) + sep * (len(bloques) - 1)
            y = (zona_bot - total) if tipo == "imagen" else zona_top + (alto_util - total) / 2
            for k, b in bloques:
                color = res if k == "num" else (tenue if k == "cue" and foto is None else txt)
                if k == "cue" and foto is not None:
                    color = (235, 235, 235)
                y = dibujar(d, b, M, y, color, res) + sep
        elif tipo == "lista":
            tit = ajustar(p.get("titulo", ""), f_princ, ancho_txt, alto_util * 0.3, W * 0.075, W * 0.05,
                          que=que) if p.get("titulo") else None
            items = p["items"]
            r_num = W * 0.04
            tam_it = W * 0.048
            its = []
            while True:
                its = [ajustar(t, f_cuerpo, ancho_txt - r_num * 3, H, tam_it, tam_it, inter=1.25, que=que)
                       for t in items]
                total = (tit["alto"] + W * 0.05 if tit else 0) + sum(b["alto"] for b in its) + W * 0.035 * len(its)
                if total <= alto_util or tam_it <= W * 0.032:
                    break
                tam_it -= 2
            if total > alto_util:
                avisos.append(f"{que}: demasiados ítems o muy largos, dividí en dos placas")
            y = zona_top + (alto_util - total) / 2
            if tit:
                y = dibujar(d, tit, M, y, txt, res) + W * 0.05
            for n, b in enumerate(its, 1):
                cy = y + b["paso"] / 2
                d.ellipse([M, cy - r_num, M + 2 * r_num, cy + r_num], fill=res)
                d.text((M + r_num, cy), str(n), font=fuente(f_princ, r_num * 1.1), anchor="mm",
                       fill=bg if res != txt else (FONDO if not claro else (255, 255, 255)))
                y = dibujar(d, b, M + r_num * 3, y, txt, res) + W * 0.035
        elif tipo == "dato":
            val = ajustar(str(p["valor"]), f_princ, ancho_txt, H * 0.3, W * 0.36, W * 0.12, inter=1.0, que=que)
            et = ajustar(p.get("etiqueta", ""), f_princ, ancho_txt, H * 0.2, W * 0.07, W * 0.045, que=que) \
                if p.get("etiqueta") else None
            total = val["alto"] + ((et["alto"] + W * 0.02) if et else 0)
            y = zona_top + (alto_util - total) / 2
            y = dibujar(d, val, W / 2, y, res, res, centrado=True)
            if et:
                dibujar(d, et, W / 2, y + W * 0.02, txt, res, centrado=True)
            if p.get("nota"):
                d.text((W / 2, zona_bot - W * 0.01), p["nota"], font=fuente(f_cuerpo, W * 0.03), fill=tenue,
                       anchor="md")
        elif tipo == "cita":
            d.text((M - W * 0.01, zona_top - W * 0.02), "“", font=fuente(f_princ, W * 0.3), fill=res)
            cit = ajustar(p["texto"], f_acento, ancho_txt, alto_util * 0.6, W * 0.075, W * 0.045, inter=1.25,
                          italica=True, que=que)
            y = zona_top + (alto_util - cit["alto"]) / 2 + W * 0.04
            y = dibujar(d, cit, M, y, txt, res)
            if p.get("autor"):
                d.text((M, y + W * 0.04), "— " + p["autor"], font=fuente(f_cuerpo, W * 0.04), fill=tenue)
        elif tipo == "cierre":
            partes_alto = 0
            tit = ajustar(p["titulo"], f_princ, ancho_txt, alto_util * 0.3, W * 0.1, W * 0.055, mayus=True,
                          que=que) if p.get("titulo") else None
            y = zona_top + alto_util * 0.05
            if tit:
                y = dibujar(d, tit, W / 2, y, txt, res, centrado=True) + W * 0.06
            alto_logo = pegar_logo(lienzo, logo_cla if claro else logo_osc, round(W * 0.3), W / 2, round(y),
                                   centrado=True)
            if not alto_logo:
                avisos.append(f"{que}: no hay logo en la marca")
            y += alto_logo + W * 0.08
            cta = p.get("cta") or cta_def
            if cta:
                color_cta = g(m, "cta", "color") or hexs(ACENTO)
                if hex_rgb(color_cta) == bg:
                    color_cta = hexs(txt)
                pildora(d, lienzo, cta, fuente(f_princ, W * 0.045), W // 2, round(y), color_cta, estilo_cta,
                        centrada=True)
                y += W * 0.1
            if p.get("bajada"):
                d.text((W / 2, y + W * 0.02), p["bajada"], font=fuente(f_cuerpo, W * 0.038), fill=tenue, anchor="mt")
            del partes_alto
        else:
            sys.exit(f"Placa {i}: tipo desconocido «{tipo}» (portada, texto, lista, dato, imagen, cita, cierre)")

        # --- pie: barra de progreso + contador / «Deslizá»
        if N > 1:
            seg = W * 0.05
            gap = W * 0.012
            yb = H - M + W * 0.005
            for k in range(N):
                x0 = M + k * (seg + gap)
                d.rounded_rectangle([x0, yb - 5, x0 + seg, yb + 5], radius=5,
                                    fill=res if k == i - 1 else mezcla(txt, bg, 0.75))
            pie = fuente(f_princ, W * 0.032)
            if i == 1:
                # la flecha se dibuja con líneas: muchas fuentes de marca no traen el carácter →
                largo, alto_f = pie.size * 0.9, pie.size * 0.28
                x1 = W - M
                d.line([(x1 - largo, yb), (x1, yb)], fill=res, width=max(2, pie.size // 9))
                d.line([(x1 - alto_f, yb - alto_f), (x1, yb), (x1 - alto_f, yb + alto_f)], fill=res,
                       width=max(2, pie.size // 9), joint="curve")
                d.text((x1 - largo - pie.size * 0.4, yb), "Deslizá", font=pie, fill=res, anchor="rm")
            elif i < N:
                d.text((W - M, yb), f"{i:02d} / {N:02d}", font=pie, fill=tenue, anchor="rm")

        final = lienzo.convert("RGB")
        nombre = salida / f"{i:02d}"
        final.save(f"{nombre}.png")
        final.save(f"{nombre}.jpg", quality=95)
        hojas.append(final)
        print(f"OK {nombre}.png · {tipo}")

    hojas[0].save(salida / "carrusel.pdf", save_all=True, append_images=hojas[1:], resolution=150)
    # vista previa: todas las placas en fila(s)
    cw = 300
    ch = round(cw * H / W)
    cols = min(5, N)
    filas = (N + cols - 1) // cols
    vista = Image.new("RGB", (cols * (cw + 12) + 12, filas * (ch + 12) + 12), "white")
    for k, im in enumerate(hojas):
        vista.paste(im.resize((cw, ch), Image.LANCZOS), (12 + (k % cols) * (cw + 12), 12 + (k // cols) * (ch + 12)))
    vista.save(salida / "vista.jpg", quality=88)
    print(f"OK {salida / 'carrusel.pdf'} ({N} páginas) · vista previa {salida / 'vista.jpg'}")
    for av in avisos:
        print("AVISO:", av)


if __name__ == "__main__":
    main()
