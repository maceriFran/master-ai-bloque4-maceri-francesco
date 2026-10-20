# S2 · P1. Clasificador de correos con evaluación

Práctica realizada el **20 de octubre de 2026**. Se ha completado únicamente P1 de S2; las prácticas de herramientas restantes todavía no se han resuelto.

## 1. De dónde partimos

Se descargaron el [clasificador oficial](https://github.com/JavierDomi/master-ia-bloque4/blob/main/s2-structured-output-tools/P1-clasificador-de-correos-con-evaluacion/s2_extraer_correo.py) y [herramientas.py](https://github.com/JavierDomi/master-ia-bloque4/blob/main/s2-structured-output-tools/P2-herramientas-como-funciones-python/herramientas.py).

El clasificador ya incluía:

- `Linea`: producto y cantidad.
- `CorreoClasificado`: tipo, cliente, líneas del pedido, urgencia y resumen.
- Una función por proveedor, que pide una respuesta estructurada.
- Seis correos con su tipo esperado.
- Una comprobación de cantidades no positivas.

Se conservaron esos modelos Pydantic, el mensaje `SISTEMA` y las llamadas oficiales. OpenAI usa Responses, Claude usa Messages y Gemini usa Chat Completions por OpenRouter. La rama opcional de Gemini nativo se conserva, pero no se utilizó en esta evaluación.

Modelos configurados:

| Proveedor | Modelo |
| --- | --- |
| OpenAI | `openai/gpt-5.4-mini` |
| Claude | `anthropic/claude-haiku-4.5` |
| Gemini | `google/gemini-3.8-flash` |

Se reutilizaron `.venv`, `.env` y `tostadero.db`. El `requirements.txt` oficial de S2 coincide con el existente y `pip check` no detectó dependencias rotas. No se recreó la base de datos ni se modificó `.env`.

## 2. Evaluación inicial

Se ejecutaron las funciones oficiales sobre los seis casos originales:

| Proveedor | Aciertos iniciales |
| --- | ---: |
| OpenAI | 6/6 |
| Claude | 6/6 |
| Gemini | 6/6 |

Las 18 respuestas estructuradas están en [resultados_iniciales.json](resultados_iniciales.json).

## 3. Ampliación a quince casos

Cada elemento de `CASOS` contiene `(correo, tipo_esperado)`. La etiqueta esperada sirve para corregir la respuesta, pero **no se envía al modelo**.

| Caso | Contenido o dificultad | Tipo esperado |
| ---: | --- | --- |
| 1 | Pedido de 20 kg, Bar La Esquina; original | pedido |
| 2 | Molino con ruido y solicitud de asistencia; original | incidencia |
| 3 | Disponibilidad de descafeinado; original | consulta |
| 4 | Pedido y cafetera que gotea, Lumbre; original | mixto |
| 5 | Pedido urgente, Hotel Prado Suites; original | pedido |
| 6 | Pregunta por una factura; original | consulta |
| 7 | Ironía: «¡Fantástico, otra vez la cafetera…!» y una avería real | incidencia |
| 8 | Bar La Esquina hace un pedido y menciona la recomendación del Hotel Prado Suites | pedido |
| 9 | Correo en inglés sobre un molino averiado | incidencia |
| 10 | Pregunta sobre dos cafés sin nombre de negocio | consulta |
| 11 | Pedido de Café Nube Azul, que no existe en la base | pedido |
| 12 | Pedido formulado como pregunta, confirmado expresamente | pedido |
| 13 | Niega que quiera pedir; solo pregunta el precio | consulta |
| 14 | Pedido de descafeinado y molino que no arranca | mixto |
| 15 | Avería ya resuelta y pregunta por el horario de recogida | consulta |

Los textos completos están en `CASOS` y en el registro de resultados.

## 4. Validación de negocio

### Dependencia de la siguiente práctica

P1 pide usar `buscar_cliente`, pero esa función no está definida en el archivo del clasificador: aparece en `herramientas.py`, dentro de P2. Según la aclaración del profesor en clase, detectar esa dependencia formaba parte del ejercicio.

En esta solución se adelantó el uso de esa función de P2: se descargó el archivo oficial y se importaron `BD` y `buscar_cliente` para completar la validación. `herramientas.py` contiene funciones; los datos de clientes están en `tostadero.db`. La IA solo extrae el nombre del correo y el código Python realiza después la consulta. No se ha implementado un bucle en el que la IA elija herramientas, ni se han usado las otras funciones de negocio de P2.

La nueva función `validar_negocio()` conserva la comprobación de cantidades y añade:

```python
if resultado.cliente and not buscar_cliente(resultado.cliente):
    avisos.append(f"cliente no encontrado en la base de datos: {resultado.cliente}")
```

Paso a paso:

1. Si `cliente` es `None`, no buscamos ningún negocio.
2. Si hay nombre, llamamos a `buscar_cliente`.
3. Esa función oficial hace una consulta SQL parametrizada sobre `clientes`, usando coincidencia parcial.
4. Si devuelve una lista vacía, imprimimos un aviso.

Se utiliza la base existente de S0. En el caso 11 los tres proveedores extrajeron **Café Nube Azul** y los tres produjeron el aviso de cliente no encontrado. Eso no es un fallo del modelo: extrajo correctamente un nombre que no está registrado.

En el caso 10 los tres devolvieron `cliente=null`, por lo que no se realizó esa búsqueda. En el caso 8 los tres extrajeron **Bar La Esquina** como cliente que hace el pedido. La coincidencia parcial también permite encontrar «Lumbre» dentro de «Restaurante Lumbre».

La búsqueda comprueba que hay una coincidencia, no autentica al remitente ni resuelve todos los posibles nombres ambiguos. El esquema oficial tiene un único campo `cliente`: el caso 8 contiene dos negocios mencionados, pero solo uno solicita el pedido; no se afirma que el esquema pueda representar pedidos independientes de varios clientes.

## 5. Resultados de los quince casos

| Proveedor | Aciertos | Porcentaje | Fallos de tipo | Salidas ausentes/errores |
| --- | ---: | ---: | ---: | ---: |
| OpenAI | 15/15 | 100 % | 0 | 0 |
| Claude | 15/15 | 100 % | 0 | 0 |
| Gemini | 15/15 | 100 % | 0 | 0 |

El detalle está en [resultados_p1.json](resultados_p1.json): proveedor, número de caso, correo, etiqueta esperada, objeto devuelto, acierto y avisos de negocio.

Para evitar consumo repetido, un comprobador temporal guardó las respuestas iniciales y las reutilizó al ejecutar `evaluar()` con los quince casos. Se hicieron **45 llamadas nuevas en total**: 18 iniciales y 27 para los nueve casos añadidos. El registro final contiene 45 evaluaciones, de las que 18 están marcadas `reutilizado=true`. El sistema, los modelos y los primeros seis correos no se cambiaron entre ambas fases.

## 6. Revisión de fallos y etiquetas

**No hubo desacuerdos entre tipo obtenido y esperado en esta ejecución. No se corrigió ninguna etiqueta después de ver las respuestas.** No se han inventado fallos ni modificaciones de etiquetas para completar este apartado.

Se revisaron especialmente estas posibles ambigüedades:

- **Caso 7:** la expresión positiva es irónica; lo que se solicita es reparar una avería. Se mantiene `incidencia`.
- **Caso 8:** dos nombres de negocios no significan dos intenciones. Solo se hace un pedido; se mantiene `pedido`.
- **Caso 9:** pedir que envíen un técnico por una máquina averiada es una incidencia, aunque esté escrito en inglés.
- **Caso 12:** tener signos de interrogación no convierte un pedido en consulta. El texto confirma expresamente la compra; se mantiene `pedido`.
- **Caso 13:** el pedido está negado. La intención actual es preguntar un precio; se mantiene `consulta`.
- **Caso 15:** la avería ya está resuelta. La única solicitud actual es conocer el horario; se mantiene `consulta`.

Si hubiera una etiqueta realmente dudosa, habría que revisarla por el significado del correo y aplicar la misma etiqueta a todos los proveedores, no cambiarla para favorecer un resultado.

Estos porcentajes miden **solo el campo `tipo`**, como pide el enunciado. No significan que se haya medido exhaustivamente la exactitud de las cantidades, la urgencia o el resumen. Quince correos de ejemplo tampoco garantizan un 100 % en correos nuevos.

## 7. Cambios en el bucle y comprobaciones locales

Se agrupó el bucle en `evaluar()` para poder probarlo y se añadieron:

- Número de caso, tipo esperado y tipo obtenido en cada línea.
- Avisos de negocio mediante `validar_negocio`.
- Un control de `None`: si falta la salida estructurada, se avisa antes de acceder a `.tipo`.
- Captura de errores por caso, mostrando solo la clase de error. Los casos fallidos siguen contando en el denominador.
- Comprobación de que existe la base de datos antes de consultar.

Las cuatro pruebas de `tests/test_s2_extraer_correo.py` pasaron sin llamadas a las APIs: cliente existente/desconocido, ausencia de cliente y cantidad inválida, salida `None`/excepción, y conjunto de al menos quince casos con etiquetas válidas. También se comprobó la sintaxis y que las copias de código de la raíz y `e2/` son idénticas.

## 8. Archivos y ejecución

- `s2_extraer_correo.py`: copia de trabajo en la raíz.
- `herramientas.py`: funciones oficiales, en la raíz; P1 solo utiliza la búsqueda de clientes.
- `e2/s2_extraer_correo.py`: copia para entregar.
- `e2/analisis.md`: este documento.
- `e2/resultados_iniciales.json` y `e2/resultados_p1.json`: evidencia de las evaluaciones realizadas.

La copia de `e2/` localiza `.env`, `herramientas.py` y `tostadero.db` en la raíz de `bloque4`; no necesita otro entorno ni otra base de datos.

Desde `bloque4`, en PowerShell:

```powershell
.\.venv\Scripts\python.exe s2_extraer_correo.py
# O ejecutar la copia de entrega:
.\.venv\Scripts\python.exe e2\s2_extraer_correo.py
```

Cada ejecución normal vuelve a realizar 45 llamadas y consume saldo; no hace falta repetirlas para consultar los resultados guardados. El script imprime los resultados en pantalla; los JSON incluidos fueron guardados por el comprobador temporal durante esta validación.

Para ejecutar solo las pruebas locales, sin consumir APIs:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_s2_extraer_correo.py -v
```

Esta entrega corresponde a P1 de S2 e incluye los resultados ya obtenidos, sin repetir las llamadas para su publicación. No se incluyen credenciales, el entorno virtual ni la base de datos.
