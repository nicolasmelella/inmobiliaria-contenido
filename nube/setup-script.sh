#!/usr/bin/env bash
# Script de instalación para un ENTORNO EN LA NUBE de Claude Code.
# Copiá TODO este contenido en: menú del entorno (barra de título de la sesión) → Edit → Setup script.
# Corre al arrancar cada sesión nueva. No lee las variables secretas del entorno (no las necesita).
set -e
apt-get update -qq || true
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg fonts-dejavu-core fonts-liberation fontconfig
python3 -m pip install -q "faster-whisper==1.2.1" "Pillow>=10" \
  || python3 -m pip install -q --break-system-packages "faster-whisper==1.2.1" "Pillow>=10"
ffmpeg -hide_banner -filters 2>/dev/null | grep -q ' subtitles ' && echo "ffmpeg con libass OK"
