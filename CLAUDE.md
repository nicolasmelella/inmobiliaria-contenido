# Motor de contenido — Inmobiliaria — instrucciones para Claude

> **Branding nuevo.** Este repo es una copia del motor de `motor-contenido` (Psico Studios). El motor es el mismo,
> pero la marca es OTRA: nunca usar colores, logo, copys, fotos, CTA ni tono de Psico Studios. Mientras
> `marca/marca.json` diga "Mi marca" o falte `marca/logo.png`, proponer `/configurar-marca` antes de producir.

Proyecto para producir videos verticales (9:16 + 4:5) y placas estáticas (1:1 + 4:5) con **mi marca** y **mis imágenes**.

- **Marca:** `marca/marca.json` (colores, fuentes, logo, CTA, voz) y `marca/estilo.md` (tono, qué mostrar, reglas
  aprendidas). Leerlos antes de cualquier pieza. Si siguen con los valores de ejemplo, proponer `/configurar-marca`.
- **Imágenes:** solo las de `mis-imagenes/`. Nunca de internet ni de otras marcas. Excepción aprobada: material
  hecho con IA en Canva a partir de fotos reales (`mis-imagenes/ia/`): fotos animadas y escenas ilustrativas con
  personas generadas, NUNCA presentadas como propiedades, clientes ni testimonios reales (ni «mejorar» una propiedad con IA). Cada video de IA usa el límite
  de IA de Canva del usuario: pedir OK antes de cada generación. Ver `marca/estilo.md` → «IA».
- **Comandos:** `/configurar-marca` · `/video <tema o guion>` · `/placa <frase o tema>` · `/carrusel <tema>`.
- **Explainer animado (OTRA marca, separada):** `explainer/` con su marca en `explainer/marca/`. Comandos
  `/configurar-marca-explainer` y `/explainer <tema>`; agente `explainer`. Nunca mezclar las dos marcas.
- **Agentes:** `productor` (orquesta) y `auditor` (revisa siempre antes de entregar).
- **Motor:** `motor/` (ver README). Si le falta algo se agrega al motor, no se hacen scripts sueltos, y después
  `bash tests/prueba_humo.sh` tiene que seguir dando OK.
- Trabajo intermedio en `trabajo/` (explainer: `trabajo-explainer/`), entregables en `salida/`. Las claves van en `.env` (nunca en el chat, el código ni el repo).
- Hablame en español rioplatense (voseo).
- **Si corrés en un entorno en la nube** (ver `nube/LEEME.md`): el contenedor se borra al cerrar la sesión.
  Logo, fuentes, fotos de `mis-imagenes/` y cambios de marca → commit y push. Entregables (videos, placas,
  carruseles, PDF) → mandáselos al usuario por el chat para que los descargue. Si falta ffmpeg o Whisper no puede
  bajar el modelo, avisá qué configurar en el entorno (setup script / dominios permitidos) en vez de improvisar.
