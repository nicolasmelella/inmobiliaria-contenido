#!/usr/bin/env python3
"""Hoja de cuadros: una imagen con un cuadro por bloque de subtítulo (o cada N segundos) para revisar
el video de un vistazo, sin mirarlo entero. Es lo que se le pasa al agente auditor.

Uso:
  python3 motor/hoja.py salida/video.mp4 salida/hoja.jpg --ass trabajo/subs.ass   # un cuadro por bloque
  python3 motor/hoja.py salida/video.mp4 salida/hoja.jpg --cada 2                  # un cuadro cada 2 s
"""
import argparse
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import correr, duracion  # noqa: E402


def tiempos_ass(ruta):
    ts = []
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        m = re.match(r"Dialogue:\s*\d+,(\d+):(\d+):([\d.]+),(\d+):(\d+):([\d.]+),", linea)
        if m:
            ini = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
            fin = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6])
            ts.append(ini + min(0.6, (fin - ini) / 2))  # después de la animación de entrada
    return ts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("salida")
    ap.add_argument("--ass")
    ap.add_argument("--cada", type=float, default=2.0)
    ap.add_argument("--columnas", type=int, default=5)
    ap.add_argument("--ancho-celda", type=int, default=270)
    a = ap.parse_args()

    from PIL import Image, ImageDraw

    total = duracion(a.video)
    ts = tiempos_ass(a.ass) if a.ass else [i * a.cada + 0.2 for i in range(int(total // a.cada) + 1)]
    ts.append(max(total - 0.3, 0))  # último cuadro (cierre)
    ts = [t for t in ts if t < total]

    tmp = Path(tempfile.mkdtemp(prefix="hoja-"))
    celdas = []
    for i, t in enumerate(ts):
        f = tmp / f"c{i:03d}.jpg"
        correr(["ffmpeg", "-y", "-ss", f"{t:.3f}", "-i", a.video, "-frames:v", "1",
                "-vf", f"scale={a.ancho_celda}:-2", str(f)])
        if not f.exists():  # muy cerca del final ffmpeg puede no devolver cuadro: se saltea
            continue
        celdas.append((t, Image.open(f).convert("RGB")))

    cw, ch = celdas[0][1].size
    rot = 22
    cols = min(a.columnas, len(celdas))
    filas = (len(celdas) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * cw, filas * (ch + rot)), "white")
    d = ImageDraw.Draw(hoja)
    for i, (t, im) in enumerate(celdas):
        x, y = (i % cols) * cw, (i // cols) * (ch + rot)
        hoja.paste(im, (x, y + rot))
        d.text((x + 6, y + 4), f"#{i + 1}  {t:.1f}s", fill="black")
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    hoja.save(a.salida, quality=88)
    print(f"OK hoja con {len(celdas)} cuadros -> {a.salida}")


if __name__ == "__main__":
    main()
