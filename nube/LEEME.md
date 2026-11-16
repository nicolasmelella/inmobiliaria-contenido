# Usarlo en un entorno en la nube de Claude Code

1. **Repo:** subí el contenido de este proyecto a un repo tuyo de GitHub (privado).
2. **Entorno** (menú del entorno en la barra de título → Edit, o uno nuevo):
   - **Setup script:** el contenido de `nube/setup-script.sh`.
   - **Variable de entorno:** `ELEVENLABS_API_KEY` = tu clave (nunca la pegues en el chat). Opcional `ELEVENLABS_VOICE_ID`.
   - **Network access:** nivel *Limited* con estos *Allowed domains* (y la casilla de package managers tildada):
     `api.elevenlabs.io` (voz) · `huggingface.co` y `*.hf.co` (modelo de Whisper, se baja una vez por sesión).
3. **Sesión** con ese entorno y ese repo.
4. **Tus archivos** (logo, fuentes, fotos): adjuntalos en el chat y pedí que los guarde en su carpeta y haga commit.
   El contenedor se borra al cerrar la sesión: lo que no está en el repo se pierde.
5. **Entregables:** al terminar, Claude te manda los archivos por el chat para descargar (los .mp4 no se suben al repo).
