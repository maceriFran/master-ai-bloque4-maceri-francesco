"""Sesión 2. Salidas estructuradas: de un correo libre a un objeto validado."""
import os
from pathlib import Path
import sys
from typing import Literal

import anthropic
import openai
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

# La copia de e2 usa los mismos .env, herramientas.py y base de datos de la raíz.
RAIZ = Path(__file__).resolve().parent
if RAIZ.name == "e2":
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))
from herramientas import BD, buscar_cliente

load_dotenv(RAIZ / ".env")


class Linea(BaseModel):
    producto: str = Field(description="Producto tal y como lo menciona el cliente")
    cantidad: int = Field(description="Unidades o kilos pedidos")


class CorreoClasificado(BaseModel):
    tipo: Literal["pedido", "incidencia", "consulta", "mixto"]
    cliente: str | None = Field(description="Nombre del negocio si aparece; si no, null")
    lineas: list[Linea] = Field(description="Vacía si no hay pedido")
    urgente: bool
    resumen: str = Field(description="Una sola frase en español")


SISTEMA = "Extraes información de correos de clientes de un distribuidor de café para hostelería."


def con_openai(correo: str) -> CorreoClasificado:
    r = openai.OpenAI().responses.parse(
        model=os.environ["OPENAI_MODEL"], instructions=SISTEMA, input=correo,
        text_format=CorreoClasificado,
    )
    return r.output_parsed


def con_claude(correo: str) -> CorreoClasificado:
    r = anthropic.Anthropic().messages.parse(
        model=os.environ["ANTHROPIC_MODEL"], max_tokens=1024, system=SISTEMA,
        messages=[{"role": "user", "content": correo}],
        output_format=CorreoClasificado,
    )
    return r.parsed_output


def con_gemini(correo: str) -> CorreoClasificado:
    if os.getenv("GEMINI_API_KEY"):  # opcional: API nativa de Gemini
        cliente = genai.Client()  # en una variable: si no, el SDK cierra el cliente antes de usarlo
        r = cliente.interactions.create(
            model=os.environ["GEMINI_MODEL"].removeprefix("google/"),
            system_instruction=SISTEMA, input=correo,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": CorreoClasificado.model_json_schema(),
            },
        )
        return CorreoClasificado.model_validate_json(r.output_text)
    # Por defecto, vía OpenRouter con Chat Completions
    cliente = openai.OpenAI(base_url="https://openrouter.ai/api/v1",
                            api_key=os.environ["OPENROUTER_API_KEY"])
    r = cliente.chat.completions.parse(
        model=os.environ["GEMINI_MODEL"],
        messages=[{"role": "system", "content": SISTEMA}, {"role": "user", "content": correo}],
        response_format=CorreoClasificado,
    )
    return r.choices[0].message.parsed


# (Correo, tipo esperado). Los primeros seis son los casos oficiales.
# Clasificamos la intención, no la puntuación ni el número de negocios mencionados.
CASOS = [
    ("Necesito 20 kg del blend de hostelería para el viernes. Bar La Esquina.", "pedido"),
    ("El molino hace un ruido raro desde ayer, ¿podéis venir?", "incidencia"),
    ("¿Tenéis café descafeinado de especialidad?", "consulta"),
    ("Mandadme 5 kg de Etiopía y, de paso, la cafetera gotea. Lumbre.", "mixto"),
    ("URGENTE: sin café para mañana, 10 kg de blend. Hotel Prado Suites", "pedido"),
    ("Buenas, ¿la factura de septiembre ya está emitida?", "consulta"),
    ("¡Fantástico, otra vez la cafetera de Restaurante Lumbre sin sacar ni una gota! "
     "Necesitamos que reparéis la avería.", "incidencia"),
    ("Soy del Bar La Esquina. El Hotel Prado Suites nos recomendó vuestro café. "
     "Queremos 3 kg de blend para el viernes.", "pedido"),
    ("Our grinder has stopped working. Please send a technician to Hotel Prado Suites.",
     "incidencia"),
    ("¿Qué diferencia hay entre vuestro café de Etiopía y el blend de hostelería?",
     "consulta"),
    ("Soy de Café Nube Azul y quiero pedir 4 kg de blend para el lunes.", "pedido"),
    ("¿Podéis enviarnos 6 kg de blend para el martes? Confirmamos el pedido. "
     "Panadería Ibiza.", "pedido"),
    ("No queremos hacer un pedido todavía. Solo necesitamos saber el precio "
     "del descafeinado. Cafetería Atocha 12.", "consulta"),
    ("Panadería Ibiza: enviad 2 kg de descafeinado y revisad el molino, "
     "que no arranca desde hoy.", "mixto"),
    ("Cafetería Atocha 12: la cafetera ya funciona, no hay ninguna avería pendiente. "
     "¿Cuál es el horario para recoger café?", "consulta"),
]


def validar_negocio(resultado: CorreoClasificado) -> list[str]:
    """Pydantic valida la forma; estas comprobaciones validan datos del negocio."""
    avisos = []
    if any(l.cantidad <= 0 for l in resultado.lineas):
        avisos.append("cantidad no válida")
    if resultado.cliente and not buscar_cliente(resultado.cliente):
        avisos.append(f"cliente no encontrado en la base de datos: {resultado.cliente}")
    return avisos


def evaluar() -> None:
    # Evita que SQLite cree por accidente una base vacía si falta la de S0.
    if not BD.is_file():
        raise FileNotFoundError("Falta tostadero.db en la raíz de bloque4.")
    for nombre, extraer in [("OpenAI", con_openai), ("Claude", con_claude), ("Gemini", con_gemini)]:
        aciertos = 0
        for numero, (correo, esperado) in enumerate(CASOS, start=1):
            try:
                resultado = extraer(correo)
            except Exception as error:
                # No imprimimos la excepción completa: podría incluir datos de la petición.
                print(f"  [{nombre}] caso {numero}: error {type(error).__name__}", flush=True)
                continue
            if resultado is None:
                print(f"  [{nombre}] caso {numero}: sin salida estructurada; "
                      "revisa el modelo configurado y el límite de tokens.", flush=True)
                continue
            aciertos += resultado.tipo == esperado
            estado = "OK" if resultado.tipo == esperado else "FALLO"
            print(f"  [{nombre}] caso {numero}: {estado}, "
                  f"esperado={esperado}, obtenido={resultado.tipo}", flush=True)
            for aviso in validar_negocio(resultado):
                print(f"  [{nombre}] caso {numero}: AVISO: {aviso}", flush=True)
        print(f"{nombre}: {aciertos}/{len(CASOS)} tipos correctos", flush=True)


if __name__ == "__main__":
    evaluar()
