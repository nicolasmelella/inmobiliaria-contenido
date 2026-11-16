---
description: Carga tu marca (colores, fuentes, logo, CTA, voz) en marca/marca.json y deja una placa de prueba
---
Configurá la marca del proyecto. Hacelo como una charla corta, de a poco:

1. Leé `marca/marca.json` y `marca/estilo.md` para ver qué ya está cargado.
2. Pedile al usuario (lo que ya esté bien, no lo vuelvas a pedir):
   - **Colores en hex**: fondo, texto, acento (el de resaltar) y, si quiere, borde de subtítulos. Si pasa una imagen
     de su manual o de su logo, sacá los colores de ahí y confirmalos.
   - **Fuentes**: los archivos .ttf/.otf (una principal en negrita y una de acento, idealmente itálica). Tienen que
     quedar en `fuentes/`. Si no las tiene, sugerí equivalentes gratis de Google Fonts y decile cómo bajarlas.
   - **Logo**: PNG con fondo transparente en `marca/logo.png`. Si tiene fondo, avisale.
   - **CTA**: el texto exacto del botón y si va relleno o con contorno.
   - **Voz** (opcional): voice_id de ElevenLabs.
   - Para `estilo.md`: rubro, a quién le habla, tono, qué no mostrar.
3. Escribí `marca/marca.json` y `marca/estilo.md`. Verificá que cada archivo nombrado exista.
4. Prueba: armá una placa con una frase de ejemplo del rubro, una sobre color y otra sobre una imagen de
   `mis-imagenes/` (si hay):
   `python3 motor/placa.py --texto "..." --salida salida/prueba-marca/placa` y mostrásela (Read).
5. Preguntá si se ve como su marca y ajustá hasta que diga que sí.

$ARGUMENTS
