---
description: Carga la marca del explainer (colores, fuentes, logo, CTA, voz) en explainer/marca/ — separada de la de videos y placas
---
Configurá la marca del EXPLAINER (archivo `explainer/marca/marca.json`, no `marca/marca.json`). Charla corta:

1. Leé `explainer/marca/marca.json` y `explainer/marca/estilo.md`.
2. Pedí lo que falte:
   - **Colores en hex:** `fondo` (oscuro funciona mejor), `resplandor` (el brillo del centro), `texto`,
     `texto_tenue` (palabras todavía no dichas), `acento` (íconos destacados, etiquetas, números), `secundario`
     (rellenos y etiquetas comunes), `alerta` (sellos y gráficos que bajan). Si pasa su manual o logo, sacalos de ahí.
   - **Fuentes** (.ttf/.otf) en `explainer/fuentes/`: una principal en negrita (y opcional una de acento).
   - **Logo** PNG transparente en `explainer/marca/logo.png`.
   - **CTA** del cierre y estilo (rellena/contorno). **Voz** de ElevenLabs (voice_id) si es distinta.
   - Para `estilo.md`: tema de la cuenta, a quién le habla, tono.
3. Escribí los dos archivos y verificá que cada ruta exista.
4. Prueba: armá un explainer corto de 3 escenas sin voz (iconos, lista, sello) en `trabajo-explainer/prueba/` y
   mostrá la hoja (`motor/hoja.py ... --cada 1`). Ajustá hasta que diga que se ve como su marca.

$ARGUMENTS
