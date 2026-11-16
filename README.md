# Motor de contenido — Inmobiliaria

> Copia del motor de `motor-contenido` con **branding nuevo** (sin nada de Psico Studios).
> Primer paso: `/configurar-marca` con colores, logo, fuentes, CTA y tono de la inmobiliaria.

Videos verticales (9:16 + 4:5) y placas estáticas (1:1 + 4:5) con **tu marca** y **tus imágenes**, armados
desde el chat con Claude Code.

## 1. Instalación en tu compu (una vez)

Necesitás **Claude Code**, **Python 3.10+**, **ffmpeg** y **git**.

- macOS: `brew install ffmpeg python git`
- Ubuntu/Debian: `sudo apt install ffmpeg python3 python3-venv git`
- Windows: instalá WSL (Ubuntu) y seguí los pasos de Ubuntu dentro de WSL.

```bash
unzip motor-video.zip
cd motor-video
bash instalar.sh
```
`instalar.sh` revisa los programas, crea el entorno de Python, instala las dependencias, crea el `.env` y corre la
prueba de humo. Tiene que terminar en `PRUEBA DE HUMO OK`.

Después completá `.env` con tu `ELEVENLABS_API_KEY` (solo hace falta para videos con voz).

## 2. Primer uso

Abrí Claude Code **dentro de la carpeta** `motor-video` y corré:

```
/configurar-marca
```
Te pregunta colores, fuentes, logo, CTA y tono, lo guarda en `marca/` y te muestra una placa de prueba.

Antes, dejá:
- tus fuentes (.ttf/.otf) en `fuentes/`
- tu logo (PNG transparente) en `marca/logo.png`
- tus fotos y videos en `mis-imagenes/` (ver `mis-imagenes/LEEME.md`)

## 3. Uso diario

```
/placa "+20 reuniones por mes"            -> 2 variantes, 1:1 y 4:5, en salida/placas/
/video reel sobre por qué los leads se enfrían   -> guion, storyboard, OK, borrador, auditoría, final
/carrusel 5 errores que hacen perder clientes    -> estructura, OK, placas + PDF en salida/carruseles/
```
El agente `productor` propone, espera tu OK, produce y pasa todo por el `auditor` antes de entregarte.
Cada corrección que le hagas queda anotada en `marca/estilo.md` para no repetirla.

## 4. Estructura

```
marca/marca.json   colores, fuentes, logo, CTA, voz  <- lo leen todos los scripts
marca/estilo.md    tono, qué mostrar, reglas aprendidas
mis-imagenes/      tus fotos y videos
fuentes/           .ttf/.otf de tu marca
motor/
  voz.py           texto -> voz (ElevenLabs)
  transcribir.py   voz -> palabras con tiempos (faster-whisper, local y gratis)
  subtitulos.py    guion + tiempos -> subtítulos por frase (renglón 1 MAYÚSCULAS, renglón 2 itálica)
  armar.py         plan.json -> video 9:16 y 4:5 (fotos animadas, clips, cierre con logo y CTA, voz, música)
  placa.py         frase -> placas 1:1, 4:5 y 9:16 (foto, cuadro de un clip o color)
  carrusel.py      plan -> carrusel de varias placas (PNG + JPG + PDF para LinkedIn + vista previa)
  hoja.py          video -> hoja de cuadros para revisar de un vistazo
.claude/agents/    productor y auditor
.claude/commands/  /configurar-marca, /video, /placa, /carrusel, /configurar-marca-explainer, /explainer
explainer/         explainer animado con SU marca (explainer/marca/, explainer/fuentes/)
ejemplo/           plan.json, guion.txt y carrusel.json de referencia
tests/             prueba de humo (no usa servicios externos ni tu marca)
trabajo/ salida/   intermedios y entregables (no se suben al repo)
```

## 5. Usarlo a mano (sin el chat)

```bash
source .venv/bin/activate
python3 motor/placa.py --texto "Tus leads *llegan tarde* | y se enfrían" --imagen mis-imagenes/foto.jpg --salida salida/placas/p1
python3 motor/voz.py --texto trabajo/locucion.txt --salida trabajo/voz.mp3
python3 motor/transcribir.py trabajo/voz.mp3 trabajo/palabras.json
python3 motor/subtitulos.py --guion trabajo/guion.txt --palabras trabajo/palabras.json --salida trabajo/subs.ass
python3 motor/armar.py trabajo/plan.json --borrador     # revisar
python3 motor/armar.py trabajo/plan.json                # final
```
- Colores, fuentes, logo y CTA salen de `marca/marca.json`. Cualquier flag (`--color-acento`, `--cta`, `--logo`,
  `--fondo`…) los pisa para esa pieza; `--sin-logo` y `--sin-cta` los sacan.
- Guion: una línea = un bloque; `L1 | L2` = dos renglones. En placas, `*palabras*` van en el color de acento.
- **4:5:** no se recorta del 9:16, se arma. Si algo queda cortado, `"foco": [x, y]` en esa escena del plan.
- **Carrusel:** `python3 motor/carrusel.py trabajo/carrusel.json [--formato 1x1] [--marca explainer/marca/marca.json]`.
  Tipos de placa: `portada`, `texto`, `lista`, `dato`, `imagen`, `cita`, `cierre` (modelo en `ejemplo/carrusel.json`).
  Sale en `salida/carruseles/<nombre>/`: `01.png`…, `carrusel.pdf` (LinkedIn) y `vista.jpg`.
- **Placa desde un video:** `--video <clip original> --t 3.2`, nunca el video final (trae subtítulos quemados).

## 6. Subirlo a tu GitHub (opcional, recomendado)

```bash
git init && git add . && git commit -m "Motor de video y placas"
git remote add origin https://github.com/TU-USUARIO/motor-video.git
git push -u origin main
```
El `.env` (tus claves) no se sube. Si no querés subir tus fotos, mirá `.gitignore`.

## 7. Explainer animado (otra marca)
Módulo aparte en `explainer/`, con su propia marca (`explainer/marca/`). Texto que se ilumina con la voz +
íconos, listas, gráficos, números y sellos. `/configurar-marca-explainer` y `/explainer <tema>`.
Todo en `explainer/README.md`.

## 8. Próximas mejoras posibles
- Generación de imágenes y animación por API.
- QC automático (contraste, ancho del texto, duración de cada bloque).
