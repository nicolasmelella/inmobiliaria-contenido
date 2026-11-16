#!/usr/bin/env bash
# Instalación del motor (macOS, Linux o Windows con WSL). Correr desde la carpeta del proyecto:  bash instalar.sh
set -euo pipefail
cd "$(dirname "$0")"
ok() { echo "  ✔ $*"; }; falta() { echo "  ✘ $*"; FALTA=1; }
FALTA=0
echo "== Revisando programas"
command -v python3 >/dev/null && ok "python3 $(python3 --version | cut -d' ' -f2)" || falta "python3 (macOS: brew install python · Ubuntu: sudo apt install python3 python3-venv)"
command -v ffmpeg >/dev/null && ok "ffmpeg" || falta "ffmpeg (macOS: brew install ffmpeg · Ubuntu: sudo apt install ffmpeg)"
if command -v ffmpeg >/dev/null; then
  ffmpeg -hide_banner -filters 2>/dev/null | grep -q ' subtitles ' && ok "ffmpeg con libass (subtítulos)" \
    || falta "tu ffmpeg no tiene libass: en macOS 'brew reinstall ffmpeg'; en Ubuntu el de apt ya lo trae"
fi
[ "$FALTA" = 0 ] || { echo "Instalá lo que falta y volvé a correr: bash instalar.sh"; exit 1; }

echo "== Entorno de Python"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "dependencias instaladas en .venv"

[ -f .env ] || { cp .env.example .env; ok "creé .env: completá ELEVENLABS_API_KEY (y ELEVENLABS_VOICE_ID si querés)"; }

echo "== Prueba de humo"
bash tests/prueba_humo.sh | tail -1
echo
echo "Listo. Abrí Claude Code en esta carpeta y corré /configurar-marca"
echo "(antes de usar el motor a mano: source .venv/bin/activate)"
