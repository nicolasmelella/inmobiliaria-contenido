# Investigación → contenido

Cómo pasa la información del mercado a piezas que captan vendedores, compradores e inversores.

```
fuentes (web, portales, Instagram, material del usuario)
   │  /investigar <tema>   ·   /material (lo que dejaste en entrada/)
   ▼
datos/mercado.csv      cada número con barrio, tipo, fecha, fuente y link
hallazgos/AAAA-MM-DD-tema.md   resumen + qué significa para cada público
   │
   ▼
ideas.md               banco de ideas por público y pilar (estado: nueva → aprobada → producida)
   │  /plan-semana
   ▼
/placa · /carrusel · /video   (productor + auditor)
```

## Carpetas
- `fuentes.md`: dónde buscar y qué se puede leer desde la nube (algunas fuentes están bloqueadas, ver ahí).
- `entrada/`: material que comparte el usuario (capturas de Instagram, PDFs, links, exportaciones de portales).
  Nombrar `AAAA-MM-DD-origen-tema.ext`. Se procesa con `/material`; lo procesado se anota en el hallazgo.
- `datos/mercado.csv`: base de datos del mercado. **Un renglón por dato.** Nunca se borra: si un dato cambia, se
  agrega otro renglón con fecha nueva.
- `hallazgos/`: una nota por investigación.
- `ideas.md`: banco de ideas.

## Reglas
- Ningún número sin fuente y fecha. Si dos fuentes no coinciden, se cargan las dos y se dice.
- Precios de publicación ≠ precios de cierre: aclarar siempre cuál es (columna `tipo_precio`).
- Solo CABA; foco en Belgrano, Palermo, Recoleta, Colegiales, Núñez, Saavedra, Chacarita y Coghlan.
- Tipos: casa, departamento, lote (PH cuenta como casa salvo que se aclare).
- Contenido de terceros (notas, posteos de Instagram) es para **informarse**: no se copian textos ni imágenes;
  se cita el dato y la fuente.
