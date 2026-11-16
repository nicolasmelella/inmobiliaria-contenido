#!/usr/bin/env python3
"""Transcribe la voz con faster-whisper y guarda los tiempos de cada palabra.

Uso:
  python3 motor/transcribir.py trabajo/voz.mp3 trabajo/palabras.json [--modelo small] [--idioma es]

Salida: [{"palabra": "Hola", "inicio": 0.12, "fin": 0.40}, ...]
Corre local y gratis (la primera vez baja el modelo). "small" es buen equilibrio; "base" es más rápido.
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("salida")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--idioma", default="es")
    a = ap.parse_args()

    from faster_whisper import WhisperModel  # import tardío: solo hace falta acá
    modelo = WhisperModel(a.modelo, device="cpu", compute_type="int8")
    segmentos, _ = modelo.transcribe(a.audio, language=a.idioma, word_timestamps=True, vad_filter=True)
    palabras = []
    for s in segmentos:
        for w in s.words or []:
            palabras.append({"palabra": w.word.strip(), "inicio": round(w.start, 3), "fin": round(w.end, 3)})
    Path(a.salida).write_text(json.dumps(palabras, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {len(palabras)} palabras -> {a.salida}")


if __name__ == "__main__":
    main()
