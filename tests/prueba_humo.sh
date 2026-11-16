#!/usr/bin/env bash
# Prueba de humo: arma un video completo SIN servicios externos (sin ElevenLabs ni Whisper).
# Genera imágenes y audio de mentira con ffmpeg, subtítulos con tiempos inventados, borrador, final y hoja.
#   bash tests/prueba_humo.sh
set -euo pipefail
cd "$(dirname "$0")/.."
T=tests/_humo; rm -rf "$T"; mkdir -p "$T/img"
# La prueba usa una marca propia (no toca marca/marca.json del proyecto)
export MOTOR_MARCA="$PWD/$T/marca.json"

ffmpeg -loglevel error -y -f lavfi -i "testsrc2=s=1600x1200:d=1" -frames:v 1 "$T/img/a.jpg"
ffmpeg -loglevel error -y -f lavfi -i "mandelbrot=s=1200x1800" -frames:v 1 "$T/img/b.jpg"
ffmpeg -loglevel error -y -f lavfi -i "testsrc=s=1920x1080:r=30:d=4" -c:v libx264 -pix_fmt yuv420p "$T/img/clip.mp4"
ffmpeg -loglevel error -y -f lavfi -i "color=c=white:s=600x200,format=rgba" -frames:v 1 "$T/logo.png"
ffmpeg -loglevel error -y -f lavfi -i "sine=f=220:d=9" -ac 1 "$T/voz.mp3"

cat > "$T/marca.json" <<'EOF'
{"nombre": "Prueba", "colores": {"fondo": "#1A1A2E", "texto": "#FFFFFF", "acento": "#FFC400", "borde": "#000000"},
 "fuentes": {}, "logo": "logo.png", "cta": {"texto": "Agendá tu reunión", "color": "#FFC400", "estilo": "rellena"}}
EOF
cat > "$T/guion.txt" <<'EOF'
¿Tus leads llegan tarde? | y se enfrían
Nosotros los traemos | todos los días
Agendá tu reunión
EOF
cat > "$T/palabras.json" <<'EOF'
[{"palabra":"¿Tus","inicio":0.2,"fin":0.4},{"palabra":"leads","inicio":0.4,"fin":0.8},{"palabra":"llegan","inicio":0.8,"fin":1.1},
 {"palabra":"tarde?","inicio":1.1,"fin":1.5},{"palabra":"y","inicio":1.6,"fin":1.7},{"palabra":"se","inicio":1.7,"fin":1.9},
 {"palabra":"enfrían","inicio":1.9,"fin":2.5},{"palabra":"Nosotros","inicio":3.0,"fin":3.5},{"palabra":"los","inicio":3.5,"fin":3.6},
 {"palabra":"traemos","inicio":3.6,"fin":4.1},{"palabra":"todos","inicio":4.2,"fin":4.5},{"palabra":"los","inicio":4.5,"fin":4.6},
 {"palabra":"días","inicio":4.6,"fin":5.1},{"palabra":"Agendá","inicio":5.6,"fin":6.1},{"palabra":"tu","inicio":6.1,"fin":6.2},
 {"palabra":"reunión","inicio":6.2,"fin":6.8}]
EOF
cat > "$T/plan.json" <<'EOF'
{
  "salida": "salida/video.mp4",
  "voz": "voz.mp3",
  "subtitulos": "subs.ass",
  "transicion": "fundido",
  "escenas": [
    {"src": "img/a.jpg", "dur": 2.5, "mov": "acercar", "foco": [0.5, 0.3]},
    {"src": "img/clip.mp4", "dur": 2.5, "desde": 0.5, "transicion": "corte"},
    {"src": "img/b.jpg", "dur": 2.0, "mov": "izquierda"}
  ],
  "cierre": true
}
EOF

python3 motor/subtitulos.py --guion "$T/guion.txt" --palabras "$T/palabras.json" --salida "$T/subs.ass" --hasta 7.0
python3 motor/armar.py "$T/plan.json" --borrador
python3 motor/armar.py "$T/plan.json"
python3 motor/hoja.py "$T/salida/video_9x16.mp4" "$T/salida/hoja_9x16.jpg" --ass "$T/subs.ass"
python3 motor/hoja.py "$T/salida/video_4x5.mp4" "$T/salida/hoja_4x5.jpg" --ass "$T/subs.ass"
dim() { ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$1"; }
[ "$(dim "$T/salida/video_9x16.mp4")" = "1080,1920" ] || { echo "FALLA 9:16"; exit 1; }
[ "$(dim "$T/salida/video_4x5.mp4")" = "1080,1350" ] || { echo "FALLA 4:5"; exit 1; }

# Placas: sobre foto, sobre un cuadro del video y sobre color
# p1: logo, CTA y acento salen solos de la marca
python3 motor/placa.py --texto "Tus leads *llegan tarde* | y se enfrían" --imagen "$T/img/b.jpg" --salida "$T/salida/placas/p1"
python3 motor/placa.py --texto "*+20 leads* por mes | sin depender de referidos" --video "$T/img/clip.mp4" --t 2.0 \
  --logo "$T/logo.png" --cta "Quiero más info" --estilo-cta rellena --color-cta "#FFC400" --formatos 1x1,4x5,9x16 \
  --salida "$T/salida/placas/p2"
python3 motor/placa.py --texto "Reuniones *todas las semanas*" --fondo "#F2EFE6" --color-acento "#C2410C" \
  --sin-logo --cta "Agendá" --estilo-cta contorno --salida "$T/salida/placas/p3"
python3 - "$T/salida/placas" <<'PY'
import sys
from pathlib import Path
from PIL import Image
esperado = {"1x1": (1080, 1080), "4x5": (1080, 1350), "9x16": (1080, 1920)}
n = 0
for f in Path(sys.argv[1]).glob("*.png"):
    fmt = f.stem.split("_")[-1]
    assert Image.open(f).size == esperado[fmt], f
    n += 1
assert n == 7, n
print(f"placas OK ({n})")
PY
# Explainer (marca separada, sin voz: ritmo estimado) en 9:16 y 4:5
E="$T/explainer"; mkdir -p "$E"
cp explainer/ejemplo/plan.json "$E/plan.json"
python3 - "$E/plan.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p)); d.pop("voz"); d.pop("palabras"); json.dump(d, open(p, "w"), ensure_ascii=False)
PY
cp "$T/img/a.jpg" "$E/foto.jpg"
printf '{"colores": {"acento": "#22C55E"}, "fuentes": {}, "logo": "%s", "cta": {"texto": "Seguinos"}}' "$PWD/$T/logo.png" > "$E/marca.json"
python3 explainer/explainer.py "$E/plan.json" --marca "$E/marca.json" --borrador | tail -1
python3 explainer/explainer.py "$E/plan.json" --marca "$E/marca.json" --formato 4x5 | tail -1
[ "$(dim "$E/salida/explainer_9x16_borrador.mp4")" = "540,960" ] || { echo "FALLA explainer 9:16"; exit 1; }
[ "$(dim "$E/salida/explainer_4x5.mp4")" = "1080,1350" ] || { echo "FALLA explainer 4:5"; exit 1; }
python3 motor/hoja.py "$E/salida/explainer_4x5.mp4" "$E/hoja.jpg" --cada 4 | tail -1
# Carrusel (con la marca de prueba) en 4:5 y 1:1
K="$T/carrusel"; mkdir -p "$K/mis-imagenes"
cp ejemplo/carrusel.json "$K/" && sed -i.bak 's#\.\./mis-imagenes/#mis-imagenes/#g' "$K/carrusel.json"
cp "$T/img/b.jpg" "$K/mis-imagenes/equipo-reunion-oficina.jpg"; cp "$T/img/a.jpg" "$K/mis-imagenes/cliente-firmando.jpg"
python3 motor/carrusel.py "$K/carrusel.json" --salida "$K/out45" | tail -1
python3 motor/carrusel.py "$K/carrusel.json" --formato 1x1 --salida "$K/out11" | tail -1
python3 - "$K" <<'PY'
import sys
from pathlib import Path
from PIL import Image
k = Path(sys.argv[1])
for carpeta, tam in (("out45", (1080, 1350)), ("out11", (1080, 1080))):
    pngs = sorted((k / carpeta).glob("[0-9][0-9].png"))
    assert len(pngs) == 8, (carpeta, len(pngs))
    assert all(Image.open(p).size == tam for p in pngs), carpeta
    assert (k / carpeta / "carrusel.pdf").stat().st_size > 10000
print("carrusel OK (8 placas en 4:5 y 1:1 + PDF)")
PY
echo "PRUEBA DE HUMO OK -> $T/salida/"
