# Explainer animado (marca separada)

Videos explicativos animados: la frase de arriba se ilumina palabra por palabra al ritmo de la voz y, abajo,
entran íconos, listas, etiquetas, gráficos, números, fotos y sellos en la palabra justa.

**Usa su propia marca:** `explainer/marca/marca.json` + `explainer/marca/estilo.md` (+ `explainer/fuentes/`,
`explainer/marca/logo.png`). No comparte nada con `marca/` (videos y placas).

## Desde el chat
```
/configurar-marca-explainer     (una vez)
/explainer por qué los clientes no vuelven a comprar
```

## A mano
```bash
MOTOR_MARCA=explainer/marca/marca.json python3 motor/voz.py --texto trabajo-explainer/locucion.txt --salida trabajo-explainer/voz.mp3
python3 motor/transcribir.py trabajo-explainer/voz.mp3 trabajo-explainer/palabras.json
python3 explainer/explainer.py trabajo-explainer/plan.json --borrador
python3 explainer/explainer.py trabajo-explainer/plan.json                 # 9:16
python3 explainer/explainer.py trabajo-explainer/plan.json --formato 4x5   # 4:5
```
Sin `voz` ni `palabras` en el plan, el ritmo se estima (sirve para probar o para hacerlo solo con música).

## El plan
Modelo completo: `explainer/ejemplo/plan.json`. Cada escena:
- `texto`: lo que dice la voz en ese tramo (literal). Va arriba y se ilumina al decirse.
- `clave`: palabras que se recuadran en el color de acento cuando se dicen.
- `visual`: uno de los tipos de abajo. `en`: palabra en la que aparece cada elemento.
- `sello` (opcional): `{"texto": "SE VA", "en": "va", "color": "alerta", "pos": "abajo"}`.

| Tipo | Para qué | Ejemplo |
|---|---|---|
| `iconos` | comparar o presentar 1–4 cosas | `{"items": [{"icono": "moneda", "etiqueta": "Precio"}, {"icono": "check", "etiqueta": "Confianza", "acento": true}], "separador": "o"}` |
| `grupo` | uno en el centro y muchos alrededor | `{"centro": {"icono": "persona", "etiqueta": "Cliente"}, "alrededor": "casa", "cantidad": 6}` |
| `lista` | pasos o preguntas numeradas | `{"items": ["¿Qué?", "¿Cuándo?", "¿Quién?"], "en": ["uno", "dos", "tres"]}` |
| `etiquetas` | canales, opciones, categorías | `{"items": ["Anuncios", "Redes"], "icono": "persona"}` |
| `grafico` | algo que sube o baja | `{"puntos": [90, 60, 45], "etiquetas": ["Ene", "Feb", "Mar"]}` (baja → color alerta) |
| `numero` | un dato fuerte que cuenta | `{"valor": "+20", "etiqueta": "reuniones por mes"}` |
| `titulo` | golpe de texto grande | `{"texto": "¿Quién gana?", "icono": "estrella"}` |
| `imagen` | una foto tuya en tarjeta | `{"src": "../mis-imagenes/equipo.jpg", "alto": 0.8}` |

**Íconos** (dibujados por código, toman los colores de la marca): persona · casa · moneda · pregunta · check · cruz ·
reloj · calendario · mensaje · estrella · grafico · puerta · celular · lupa · rayo. Para uno propio:
`"icono": "../mis-iconos/camion.png"` (PNG transparente).

## Colores de la marca del explainer
`fondo` · `resplandor` (brillo del centro) · `texto` · `texto_tenue` (palabras todavía no dichas) · `acento` ·
`secundario` (rellenos) · `alerta` (sellos, gráficos que bajan).
