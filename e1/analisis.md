# P4. Comparativa de proveedores

Evaluamos cinco correos por proveedor. Puntuamos de 1 a 5
considerando fidelidad a los datos disponibles, utilidad, claridad
y cumplimiento del máximo de dos frases.

| Proveedor | Calidad media | Latencia media | Tokens salida totales | Coste medio por correo USD | Estimación 2.000 correos USD |
|---|---:|---:|---:|---:|---:|
| OpenAI | 3,8 | 1,926 s | 260 | 0,00027450 | 0,549 |
| Claude | 3,6 | 1,752 s | 389 | 0,00045600 | 0,912 |
| Gemini | 2,4 | 6,674 s | 2937 | 0,00223515 | 4,4703 |

## Tokens de salida

Gemini registra aproximadamente 11,3 veces más tokens de salida
que OpenAI, aunque sus respuestas visibles no son proporcionalmente
más largas.

Los modelos pueden consumir tokens de razonamiento interno que
se contabilizan como salida, aunque no aparezcan en el texto final.
Esto es coherente con la prueba de P3, donde Gemini registró
razonamiento sin producir texto visible con un límite pequeño.
Para conocer el desglose exacto de P4 habría que consultar los
detalles de uso de estas llamadas.

También existen diferencias de tokenización entre modelos.

## Calidad de las respuestas

OpenAI obtuvo 3,8/5, Claude 3,6/5 y Gemini 2,4/5 según nuestra rúbrica.
Son valoraciones manuales sobre una muestra pequeña.

OpenAI y Gemini afirmaron que había entregas los sábados sin
disponer de información que lo confirmase. Gemini también prometió
asistencia inmediata e inventó un producto concreto y una oferta
de muestras.

Claude fue prudente ante las consultas sobre entregas y facturas,
pero su respuesta al hotel fue genérica, contenía un error gramatical
y superaba el límite de dos frases.

## Elección para 2.000 correos al mes

Elegiríamos OpenAI para una primera prueba supervisada:
obtuvo la mejor calidad media de esta evaluación y el menor coste.

El gasto estimado sería:
0,00027450 USD por correo × 2.000 = 0,549 USD al mes.

Claude fue el más rápido, con 1,752 segundos de media frente a
1,926 de OpenAI, una diferencia de 0,174 segundos. En esta muestra,
esa ventaja no compensa su mayor coste y su calidad ligeramente menor.

Gemini fue el más lento y costoso, sin mejorar la calidad evaluada.

La estimación supone correos y respuestas similares a los cinco
ejemplos y los precios usados en P3. No incluye reintentos,
herramientas ni otros gastos. Cinco correos no bastan para
generalizar: ampliaríamos la evaluación antes de usarlo en producción.

Antes de automatizar respuestas, aportaríamos información real sobre
entregas, catálogo y procedimientos, e indicaríamos al modelo que
no invente condiciones comerciales ni acciones realizadas.
