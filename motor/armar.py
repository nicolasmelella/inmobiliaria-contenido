#!/usr/bin/env python3
"""Arma el video a partir de un plan JSON: escenas (fotos animadas o clips) + cierre + voz + música + subtítulos.

Uso:
  python3 motor/armar.py plan.json                    # final en los formatos del plan (default 9:16 y 4:5)
  python3 motor/armar.py plan.json --borrador         # mitad de resolución y calidad baja, para revisar rápido
  python3 motor/armar.py plan.json --formatos 9x16    # solo un formato

Plan (rutas relativas a la carpeta del plan):
{
  "salida": "salida/video.mp4",             -> video_9x16.mp4 y video_4x5.mp4
  "formatos": ["9x16", "4x5"],              (opcional; default los dos)
  "fps": 30,
  "voz": "trabajo/voz.mp3",                 (opcional)
  "musica": "musica.mp3", "musica_db": -22,   (opcional)
  "subtitulos": "trabajo/subs.ass",         (opcional; se arma para 9:16 y se adapta solo al 4:5)
  "fuentes": "../fuentes",                  (carpeta con .ttf/.otf para los subtítulos, opcional)
  "escenas": [
    {"src": "img/foto1.jpg", "dur": 3.0, "mov": "acercar", "foco": [0.5, 0.4]},
    {"src": "clips/toma.mp4", "dur": 2.5, "desde": 1.0},
    {"color": "#111111", "dur": 1.5}
  ],
  "transicion": "fundido",   (opcional: fundido | deslizar | barrido | zoom | desenfoque | circulo;
                              también por escena: {"src": ..., "transicion": "zoom"} = cómo ENTRA la siguiente)
  "transicion_dur": 0.35,    (segundos; los tiempos de las escenas y los subtítulos no cambian)
  "cierre": true      -> logo, fondo, CTA y fuente salen de marca/marca.json
  (o un objeto para pisar algo: {"dur": 3, "cta": "Otro CTA", "logo": "otro.png", "fondo": "#hex"})
}
mov (fotos): acercar | alejar | izquierda | derecha | fijo.
foco [x, y] (0 a 1): qué punto de la imagen queda en el centro al recortar. Importa sobre todo en 4:5, donde el
cuadro es más bajo: si la cara o el producto quedan cortados, se corrige el foco de esa escena.
Las fotos y los clips se recortan para LLENAR el cuadro (sin franjas). El 4:5 se ARMA (escenas reencuadradas y
cierre propio), no se recorta del 9:16.
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import RAIZ, archivo_marca, cargar_marca, correr, duracion, g  # noqa: E402

EXT_VIDEO = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast"]
FORMATOS = {"9x16": (1080, 1920), "4x5": (1080, 1350), "1x1": (1080, 1080)}


def cubrir(w, h, foco=None):
    fx, fy = foco or (0.5, 0.5)
    return (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h}:(iw-{w})*{fx}:(ih-{h})*{fy},setsar=1")


def escena_foto(src, dur, mov, foco, w, h, fps, out):
    n = max(1, round(dur * fps))
    W, H = w * 2, h * 2  # se trabaja al doble para que el movimiento no tiemble
    z = {"acercar": f"1+0.12*on/{n}", "alejar": f"1.12-0.12*on/{n}"}.get(
        mov, "1.08" if mov in ("izquierda", "derecha") else "1")
    cx = "iw/2-(iw/zoom/2)"
    if mov == "izquierda":
        cx = f"(iw-iw/zoom)*(1-on/{n})"
    elif mov == "derecha":
        cx = f"(iw-iw/zoom)*on/{n}"
    vf = (f"{cubrir(W, H, foco)},zoompan=z='{z}':x='{cx}':y='ih/2-(ih/zoom/2)':d={n}:s={w}x{h}:fps={fps},"
          f"format=yuv420p")
    correr(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-vf", vf, "-frames:v", str(n), "-r", str(fps),
            *ENC, "-an", str(out)])


def escena_clip(src, dur, desde, foco, w, h, fps, out):
    correr(["ffmpeg", "-y", "-ss", str(desde), "-i", str(src), "-t", str(dur),
            "-vf", f"{cubrir(w, h, foco)},fps={fps},format=yuv420p", *ENC, "-an", str(out)])
    real = duracion(out)
    if real < dur - 0.05:  # el clip era más corto: se congela el último cuadro
        tmp = out.with_suffix(".tmp.mp4")
        correr(["ffmpeg", "-y", "-i", str(out), "-vf", f"tpad=stop_mode=clone:stop_duration={dur - real:.3f}",
                *ENC, str(tmp)])
        tmp.replace(out)


def escena_color(color, dur, w, h, fps, out):
    correr(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color.replace('#', '0x')}:s={w}x{h}:r={fps}:d={dur}",
            *ENC, str(out)])


def imagen_cierre(c, base, w, h, ruta):
    """Cuadro del cierre (logo + CTA) como PNG transparente, compuesto para ESTE formato."""
    from PIL import Image, ImageDraw
    from placa import cargar_fuente, pildora
    lienzo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    logo = Image.open(base / c["logo"]).convert("RGBA")
    ancho_logo = round(w * c.get("ancho_logo", 0.55))
    logo = logo.resize((ancho_logo, max(1, round(logo.height * ancho_logo / logo.width))), Image.LANCZOS)
    cta = c.get("cta")
    alto_cta = round(w * 0.11) if cta else 0
    sep = round(w * 0.06) if cta else 0
    y0 = (h - (logo.height + sep + alto_cta)) // 2
    lienzo.alpha_composite(logo, ((w - logo.width) // 2, y0))
    if cta:
        fuente = cargar_fuente(c.get("fuente_cta") and str(base / c["fuente_cta"]), round(w * 0.045), negrita=True)
        pildora(ImageDraw.Draw(lienzo), lienzo, cta, fuente, w // 2, y0 + logo.height + sep + alto_cta // 2,
                c.get("color_cta", "#FFFFFF"), c.get("estilo_cta", "contorno"), centrada=True)
    lienzo.save(ruta)


def escena_cierre(c, base, w, h, fps, out, tmp):
    dur = c.get("dur", 2.5)
    fondo = c.get("fondo", "#000000").replace("#", "0x")
    png = tmp / f"cierre_{w}x{h}.png"
    imagen_cierre(c, base, w, h, png)
    filtro = "[1:v]format=rgba,fade=in:st=0.15:d=0.5:alpha=1[l];[0:v][l]overlay=0:0,format=yuv420p"
    correr(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={fondo}:s={w}x{h}:r={fps}:d={dur}",
            "-loop", "1", "-i", str(png), "-filter_complex", filtro, "-t", str(dur), *ENC, str(out)])


def cierre_con_marca(c):
    """Completa el cierre con lo de marca/marca.json (lo que trae el plan manda)."""
    c = dict(c) if isinstance(c, dict) else {}
    m = cargar_marca()
    c.setdefault("logo", archivo_marca(m, g(m, "logo")))
    if not c["logo"]:
        sys.exit("El cierre necesita un logo: poné \"logo\" en marca/marca.json o en el cierre del plan")
    c.setdefault("fondo", g(m, "colores", "fondo", defecto="#000000"))
    if "cta" not in c and g(m, "cta", "texto"):
        c["cta"] = g(m, "cta", "texto")
    c.setdefault("color_cta", g(m, "cta", "color") or g(m, "colores", "acento") or "#FFFFFF")
    c.setdefault("estilo_cta", g(m, "cta", "estilo", defecto="contorno"))
    c.setdefault("fuente_cta", archivo_marca(m, g(m, "fuentes", "principal")))
    return c


def ass_para_formato(texto, alto_nuevo):
    """Adapta un .ass hecho para 9:16 a otro alto: mantiene tamaños y escala la posición vertical."""
    m = re.search(r"PlayResY:\s*(\d+)", texto)
    alto_viejo = int(m.group(1)) if m else 1920
    if alto_viejo == alto_nuevo:
        return texto
    k = alto_nuevo / alto_viejo
    texto = re.sub(r"PlayResY:\s*\d+", f"PlayResY: {alto_nuevo}", texto)
    return re.sub(r"\\pos\(([\d.]+),([\d.]+)\)",
                  lambda mm: f"\\pos({mm.group(1)},{round(float(mm.group(2)) * k)})", texto)


XFADE = {"fundido": "fade", "deslizar": "slideleft", "barrido": "smoothleft", "zoom": "zoomin",
         "desenfoque": "hblur", "circulo": "circleopen", "corte": None}


def render(plan, base, w, h, fps, salida, borrador, tmp):
    partes, durs, trans = [], [], []
    T = float(plan.get("transicion_dur", 0.35))
    n_esc = len(plan["escenas"])
    hay_cierre = bool(plan.get("cierre"))
    for i, e in enumerate(plan["escenas"], 1):
        out = tmp / f"e{i:02d}_{w}x{h}.mp4"
        dur = float(e["dur"])
        tr = XFADE.get(e.get("transicion", plan.get("transicion", "corte")), "fade")
        es_ultima = i == n_esc and not hay_cierre
        durs.append(dur)
        trans.append(None if es_ultima else tr)
        if tr and not es_ultima:
            dur += T  # se estira para que el fundido no corra los tiempos de lo que sigue
        if "color" in e:
            escena_color(e["color"], dur, w, h, fps, out)
        else:
            src = base / e["src"]
            if not src.exists():
                sys.exit(f"No existe {src}")
            foco = e.get("foco")
            if src.suffix.lower() in EXT_VIDEO:
                escena_clip(src, dur, e.get("desde", 0), foco, w, h, fps, out)
            else:
                escena_foto(src, dur, e.get("mov", "acercar"), foco, w, h, fps, out)
        partes.append(out)
    if plan.get("cierre"):
        out = tmp / f"cierre_{w}x{h}.mp4"
        c_cierre = cierre_con_marca(plan["cierre"])
        escena_cierre(c_cierre, base, w, h, fps, out, tmp)
        partes.append(out)
        durs.append(float(c_cierre.get("dur", 2.5)))
        trans.append(None)

    video_base = tmp / f"base_{w}x{h}.mp4"
    if any(trans):
        # Encadena con xfade donde haya transición; donde no, concat directo
        entradas, filtro, prev, t_acum = [], [], "[n0]", 0.0
        norm = f"settb=AVTB,fps={fps},format=yuv420p"  # misma base de tiempo en todo (xfade lo exige)
        for k, p in enumerate(partes):
            entradas += ["-i", str(p)]
            filtro.append(f"[{k}:v]{norm}[n{k}]")
        for k in range(1, len(partes)):
            t_acum += durs[k - 1]
            sal = f"[v{k}]"
            if trans[k - 1]:
                filtro.append(f"{prev}[n{k}]xfade=transition={trans[k - 1]}:duration={T}:offset={t_acum:.3f}{sal}")
            else:
                # corte seco: se recorta lo anterior a su duración y se concatena
                filtro.append(f"{prev}trim=0:{t_acum:.3f},setpts=PTS-STARTPTS[a{k}];"
                              f"[n{k}]setpts=PTS-STARTPTS[b{k}];[a{k}][b{k}]concat=n=2:v=1:a=0,{norm}{sal}")
            prev = sal
        correr(["ffmpeg", "-y", *entradas, "-filter_complex", ";".join(filtro), "-map", prev,
                "-r", str(fps), *ENC, str(video_base)])
    else:
        lista = tmp / f"lista_{w}x{h}.txt"
        lista.write_text("".join(f"file '{p}'\n" for p in partes))
        correr(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(video_base)])
    total = duracion(video_base)

    entradas = ["-i", str(video_base)]
    filtros, mezcla = [], []
    n = 1
    if plan.get("voz"):
        entradas += ["-i", str(base / plan["voz"])]
        filtros.append(f"[{n}:a]loudnorm=I=-16:TP=-1.5:LRA=11,apad[voz]")
        mezcla.append("[voz]")
        n += 1
    if plan.get("musica"):
        entradas += ["-stream_loop", "-1", "-i", str(base / plan["musica"])]
        filtros.append(f"[{n}:a]volume={plan.get('musica_db', -22)}dB,"
                       f"afade=t=in:d=0.8,afade=t=out:st={max(total - 1.2, 0):.2f}:d=1.2[mus]")
        mezcla.append("[mus]")
        n += 1

    vf = "null"
    if plan.get("subtitulos"):
        alto_real = h * 2 if borrador else h
        ass = tmp / f"subs_{alto_real}.ass"
        ass.write_text(ass_para_formato((base / plan["subtitulos"]).read_text(encoding="utf-8"), alto_real),
                       encoding="utf-8")
        vf = f"subtitles='{str(ass).replace(':', chr(92) + ':')}'"
        carpeta_fuentes = (base / plan["fuentes"]) if plan.get("fuentes") else RAIZ / "fuentes"
        if carpeta_fuentes.exists():
            fd = str(carpeta_fuentes.resolve()).replace(":", r"\:")
            vf += f":fontsdir='{fd}'"
        if borrador:  # el .ass está pensado a resolución completa: se escala el video al revés
            vf = f"scale={w * 2}:{h * 2},{vf},scale={w}:{h}"
    filtros.append(f"[0:v]{vf}[v]")

    mapa = ["-map", "[v]"]
    if mezcla:
        if len(mezcla) == 1:
            filtros.append(f"{mezcla[0]}anull[a]")
        else:
            filtros.append(f"{''.join(mezcla)}amix=inputs={len(mezcla)}:duration=longest:normalize=0[a]")
        mapa += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]

    correr(["ffmpeg", "-y", *entradas, "-filter_complex", ";".join(filtros), *mapa,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast" if borrador else "medium",
            "-crf", "28" if borrador else "18", "-r", str(fps), "-t", f"{total:.3f}", "-movflags", "+faststart",
            str(salida)])
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--borrador", action="store_true", help="mitad de resolución y calidad baja, para revisar rápido")
    ap.add_argument("--formatos", help="ej. 9x16,4x5 (pisa lo del plan)")
    a = ap.parse_args()

    ruta_plan = Path(a.plan).resolve()
    base = ruta_plan.parent
    plan = json.loads(ruta_plan.read_text(encoding="utf-8"))
    fps = plan.get("fps", 30)
    formatos = a.formatos.split(",") if a.formatos else plan.get("formatos", ["9x16", "4x5"])

    salida = base / plan.get("salida", "salida/video.mp4")
    salida.parent.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix="motor-"))
    try:
        for f in formatos:
            if f not in FORMATOS:
                sys.exit(f"Formato desconocido: {f} (válidos: {', '.join(FORMATOS)})")
            w, h = FORMATOS[f]
            if a.borrador:
                w, h = (w // 2 + 1) // 2 * 2, (h // 2 + 1) // 2 * 2  # mitad, redondeada a par (h264)
            out = salida.with_name(f"{salida.stem}_{f}{'_borrador' if a.borrador else ''}{salida.suffix}")
            total = render(plan, base, w, h, fps, out, a.borrador, tmp)
            print(f"OK {out} · {w}x{h} · {total:.2f}s")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
