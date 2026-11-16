#!/usr/bin/env python3
"""Genera la locución con ElevenLabs.

Uso:
  python3 motor/voz.py --texto locucion.txt --salida trabajo/voz.mp3 [--voz VOICE_ID] [--modelo eleven_multilingual_v2]

Necesita ELEVENLABS_API_KEY (y opcionalmente ELEVENLABS_VOICE_ID) en .env.
El texto de la voz puede diferir del guion en la grafía (ej. siglas escritas como se pronuncian);
el guion literal es el que va a los subtítulos.
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from comun import cargar_env, cargar_marca, g  # noqa: E402


def main():
    cargar_env()
    ap = argparse.ArgumentParser()
    ap.add_argument("--texto", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--voz", default=os.environ.get("ELEVENLABS_VOICE_ID") or g(cargar_marca(), "voz", "voice_id"))
    ap.add_argument("--modelo", default="eleven_multilingual_v2")
    ap.add_argument("--estabilidad", type=float, default=0.5)
    ap.add_argument("--similitud", type=float, default=0.75)
    ap.add_argument("--velocidad", type=float, default=g(cargar_marca(), "voz", "velocidad", defecto=1.0))
    a = ap.parse_args()

    clave = os.environ.get("ELEVENLABS_API_KEY")
    if not clave:
        sys.exit("Falta ELEVENLABS_API_KEY en .env")
    if not a.voz:
        sys.exit("Falta la voz: --voz, ELEVENLABS_VOICE_ID en .env o voz.voice_id en marca/marca.json")

    texto = Path(a.texto).read_text(encoding="utf-8").strip()
    cuerpo = json.dumps({
        "text": texto,
        "model_id": a.modelo,
        "voice_settings": {"stability": a.estabilidad, "similarity_boost": a.similitud, "speed": a.velocidad},
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{a.voz}?output_format=mp3_44100_128",
        data=cuerpo, method="POST",
        headers={"xi-api-key": clave, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        audio = r.read()
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_bytes(audio)
    print(f"OK voz -> {a.salida} ({len(audio)//1024} KB)")


if __name__ == "__main__":
    main()
