# Estilo de la marca — Proyecto Dos Realty

> Lo que el productor y el auditor tienen que saber y no entra en `marca.json`.
> **Marca nueva.** Este repo salió del motor de contenido de Psico Studios: el motor es el mismo, pero el
> branding es OTRO. No usar nada de Psico Studios (colores, logo, fuentes, copys, fotos, CTA, tono).
> Fuente: manual de marca «PROYECTO DOS Guidelines» (MediaHaus), en `marca/manual/`. Cargado el 2026-11-16.
> Todo lo marcado «(a completar)» falta definir con el usuario.

## Qué hacemos y para quién
- **Proyecto Dos Realty** («Proyecto Dos»), inmobiliaria. Oficina: Perú 89, 7.º piso, CABA. Web: www.proyectodos.com.ar.
- Cómo se presentan: «Somos un equipo de jóvenes profesionales con amplia trayectoria en el mercado inmobiliario».
- Ejemplos del manual: emprendimientos (Edificio Co-living 9 de Julio, para estudiantes y jóvenes graduados),
  inversión («Seguridad y confianza en tu inversión»), proyectos en Tulum, México (Aldea Zama). Confirmar cuáles son reales.
- Años de trayectoria y diferencial: (a completar).

## Objetivo y estrategia (definido por el usuario, 2026-11-16)
- **Objetivo:** CAPTAR. Cada pieza tiene que acercar a un **propietario que quiere vender** o a un **comprador /
  inversor con capital**. El contenido es **educativo**: enseña algo útil y cierra con un CTA de captación.
- **Públicos (solo estos tres):**
  1. **Vendedores:** tienen una propiedad y quieren venderla. Dolores: no saber cuánto vale, publicar caro y que
     no se venda, ofertas bajas, papeles (sucesión, planos, escritura), impuestos y gastos de la venta, con qué
     comprar después.
  2. **Compradores:** tienen el capital y buscan dónde vivir. Dolores: precio justo vs. inflado, cuánto negociar,
     gastos de escritura, crédito hipotecario, qué revisar antes de reservar, usado vs. a estrenar.
  3. **Inversores:** buscan renta o valorización. Dolores: qué barrio rinde más, renta en USD, pozo vs. usado,
     comprar lote para construir, riesgos, temporario vs. tradicional.
- **Zona:** Capital Federal. Foco: **Belgrano, Palermo, Recoleta, Colegiales, Núñez, Saavedra, Chacarita y
  Coghlan**. Otros barrios de CABA se aceptan.
- **Qué buscamos siempre:** **casas, departamentos y lotes para construir.**
- **CTA según público:**
  - Vendedor → «PEDÍ TU TASACIÓN» / «QUIERO VENDER» / «Escribinos: tasamos sin cargo».
  - Comprador → «QUIERO RECIBIR PROPIEDADES» / «VER PROPIEDADES».
  - Inversor → «QUIERO OPORTUNIDADES» / «HABLEMOS DE TU INVERSIÓN».
- **Pilares de contenido:**
  1. **Datos del mercado por barrio** (m², tendencia, tiempo de venta, margen de negociación) → los tres públicos.
  2. **Guías paso a paso** (cómo vender, cómo comprar, gastos, papeles) → vendedor / comprador.
  3. **Números de inversión** (renta, lote: qué se puede construir, pozo vs. usado) → inversor.
  4. **Errores comunes** (publicar caro, no tasar, reservar sin revisar) → vendedor / comprador.
  5. **Barrio por barrio** (qué buscar, perfiles, precios) → los tres; refuerza que somos de la zona.
- **Datos:** todo número que salga en una pieza tiene que tener fuente y fecha en `investigacion/` (nunca
  inventar ni redondear a ojo). Si las fuentes no coinciden, decirlo en el chat y usar rangos o la más confiable.
  En la pieza va la fuente chica si el dato es fuerte («Fuente: Zonaprop, oct. 2026»).

## Datos del negocio (completar; nunca inventar)
- Zona: CABA (ver barrios foco en «Objetivo y estrategia»).
- Contacto: teléfono/WhatsApp (+54 11) 4041 5356 (de la tarjeta comercial; confirmar si es el WhatsApp para piezas).
- CTA por defecto: «VER PROPIEDADES». Otros: «QUIERO RECIBIR PROPIEDADES», «CONTACTANOS», «PEDÍ TU TASACIÓN».
- Instagram: (a completar)
- Matrícula / corredor responsable: (a completar si va en las piezas).
- Precios, m², expensas y datos de cada propiedad: SOLO los que pase el usuario. Si falta un dato, preguntar.

## Paleta (del manual)
- Neutra: negro `#080808`, blanco `#FFFFFF`, gris `#606060`, arena `#DDC5A2`.
- Complementaria: azul `#27529E` (color principal, fondo por defecto y texto del botón), celeste `#3DAAD2`,
  naranja `#E89064`, violeta `#7664CA`.
- Gradientes del manual: azul→violeta, violeta→celeste, celeste→azul (ver `marca/logos/cuadrados/7-9.png`).
- Piezas de redes del manual: fondos azul o negro/gris oscuro, texto blanco, fotos de edificios e interiores,
  dato destacado en arena (ej. «*9 de julio.*»). Usar `--fondo "#080808"` para la variante oscura.

## Tipografía
- **En redes (lo que usa hoy el feed, manda sobre el manual): Poppins.** Título Poppins Bold, bajada Poppins
  Regular, etiqueta Poppins Medium. El manual dice Montserrat (queda en `fuentes/` para papelería/otros usos).
- Texto en minúsculas normales; la etiqueta y el botón en MAYÚSCULAS.

## Formato de placa (de los posteos reales del usuario, 2026-11-16)
- Foto de edificios/propiedades de Buenos Aires a pantalla completa, con tinte azul arriba y velo oscuro abajo.
- Logo **horizontal blanco** arriba a la izquierda (`marca/logo-horizontal-blanco.png`).
- Abajo a la izquierda, en este orden: **etiqueta** (píldora con degradado celeste→azul, MAYÚSCULAS) →
  **título** en Poppins Bold blanco (1–3 renglones) → **bajada** en Poppins Regular → **botón blanco** con texto azul
  en MAYÚSCULAS, alineado a la izquierda.
- Comando: `python3 motor/placa.py --texto "Título | bajada" --etiqueta "PROPIEDADES SELECCIONADAS"
  --cta "Ver propiedades" --imagen mis-imagenes/x.jpg --salida salida/placas/x` (la marca ya trae todo lo demás).

## Copys aprobados (posteos del usuario; usar como base)
- Etiqueta «PROPIEDADES SELECCIONADAS» · «Descubrí el estilo de vida que buscás» | «Conocé nuestras propiedades en
  Buenos Aires y encontrá la tuya» · botón «VER PROPIEDADES».
- Etiqueta «SUMATE A LA COMUNIDAD» · «Tu próximo hogar está más cerca de lo que pensás» | «Seguinos y recibí antes
  que nadie las mejores oportunidades en Buenos Aires» · botón «QUIERO RECIBIR PROPIEDADES».
- Tono que se ve: aspiracional y cercano (hogar, estilo de vida, oportunidades), foco en **Buenos Aires**.

## Logo
- `marca/logo-horizontal-blanco.png`: horizontal blanco; es el que va en las placas (arriba a la izquierda).
- `marca/logo-simbolo-blanco.png`: la «P» blanca sola (avatares, marcas de agua, explainer).
- `marca/logo.png`: símbolo + «PROYECTO DOS REALTY» apilado, blanco (cierres de video, portadas).
- `marca/logos/`: versiones negras/grises para fondos claros (`--logo marca/logos/...`).
- `marca/logos/cuadrados/`: los 15 avatares cuadrados del manual (perfil de redes).
- Respetar el área de protección del manual (1X alrededor). No deformar ni recolorear fuera de la paleta.
  Usos incorrectos del manual: logo sobre rojo, sobre fondos que no son de la paleta o sobre fotos sin contraste.

## Tono
- Registro: voseo rioplatense («Contactanos», «Encontranos en»). Profesional, joven, de confianza.
- Palabras que usamos: (a completar)
- Palabras que NO usamos: (a completar). Nada de urgencia falsa («últimas unidades» si no es cierto).

## Imágenes
- Solo fotos/videos propios de `mis-imagenes/` (propiedades, equipo, oficina, barrio).
- Nombrarlas por propiedad y ambiente: `depto-palermo-3amb/living-balcon.jpg`.
- Qué no mostrar: datos personales de propietarios/inquilinos, patentes, caras sin permiso, direcciones exactas
  si el usuario no lo autoriza.

## IA
- Igual que en el motor original: escenas generadas con IA solo como ilustración, nunca presentadas como
  propiedades, clientes o testimonios reales. Nunca «mejorar» una propiedad con IA de forma que engañe
  (agregar ambientes, vistas o terminaciones que no tiene). Pedir OK antes de cada generación.

## Pronunciación (para la voz)
- (a completar)

## Reglas aprendidas
<!-- El productor anota acá cada corrección tuya, con fecha. Las viejas se tachan, no se borran. -->
- 2026-11-16: repo creado a partir de motor-contenido. Mismo motor, branding nuevo (no reutilizar Psico Studios).
- 2026-11-16: marca Proyecto Dos cargada desde el manual. Formato de placa ajustado a 2 posteos reales del usuario
  (Poppins, etiqueta con degradado, logo horizontal arriba a la izquierda, botón blanco). Falta que apruebe las pruebas.
