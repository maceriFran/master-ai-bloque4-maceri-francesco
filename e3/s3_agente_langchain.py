"""Sesión 3. El mismo agente con LangChain 1.x: create_agent + middleware."""
import os
from typing import Literal

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, ModelCallLimitMiddleware
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

import herramientas as h
from s3_agente import CORREO, SISTEMA


@tool
def buscar_cliente(texto: str) -> list[dict]:
    """Busca clientes por nombre (coincidencia parcial). Devuelve id, nombre, tipo y distrito."""
    return h.buscar_cliente(texto)


@tool
def consultar_pedidos(cliente_id: int) -> list[dict]:
    """Lista los pedidos de un cliente con fecha, estado y total en euros."""
    return h.consultar_pedidos(cliente_id)


@tool
def stock_producto(texto: str) -> list[dict]:
    """Consulta precio y stock de productos cuyo nombre o SKU contenga el texto."""
    return h.stock_producto(texto)


@tool
def crear_incidencia(cliente_id: int, maquina: str, descripcion: str,
                     prioridad: Literal["baja", "media", "alta"]) -> dict:
    """Registra una avería concreta de un cliente. maquina es el SKU, p. ej. MAQ-010.

    Úsala solo si el cliente describe una avería concreta.
    """
    return h.crear_incidencia(cliente_id, maquina, descripcion, prioridad)


def crear_agente(max_pasos: int = 8):
    return create_agent(
        model=f"anthropic:{os.environ['ANTHROPIC_MODEL']}",
        tools=[buscar_cliente, consultar_pedidos, stock_producto, crear_incidencia],
        system_prompt=SISTEMA,
        middleware=[
            HumanInTheLoopMiddleware(interrupt_on={
                "crear_incidencia": {"allowed_decisions": ["approve", "reject"]}}),
            # thread_limit mantiene el tope también después de reanudar una pausa.
            ModelCallLimitMiddleware(run_limit=max_pasos, thread_limit=max_pasos,
                                     exit_behavior="error"),
        ],
        checkpointer=InMemorySaver(),
    )


def ejecutar(correo: str = CORREO, max_pasos: int = 8) -> str:
    agente = crear_agente(max_pasos)
    config = {"configurable": {"thread_id": "correo-lumbre-001"}}
    entrada = {"messages": [{"role": "user", "content": correo}]}
    vistos = set()
    try:
        while True:
            for estado in agente.stream(entrada, config, stream_mode="values"):
                for mensaje in estado["messages"]:
                    if mensaje.id in vistos:
                        continue
                    vistos.add(mensaje.id)
                    if mensaje.type == "tool":
                        print(f"[resultado {mensaje.name}] {mensaje.content}")
                    elif mensaje.text:
                        print(f"[{mensaje.type}] {mensaje.text}")
                    if getattr(mensaje, "tool_calls", None):
                        print(f"[herramientas] {mensaje.tool_calls}")
                    if getattr(mensaje, "usage_metadata", None):
                        uso = mensaje.usage_metadata
                        print(f"[tokens] entrada={uso['input_tokens']}, salida={uso['output_tokens']}")
            if not estado.get("__interrupt__"):
                return estado["messages"][-1].text
            decisiones = []
            for peticion in estado["__interrupt__"][0].value["action_requests"]:
                ok = input(f"¿Aprobar {peticion['name']}({peticion['args']})? [s/N] ").strip().lower() == "s"
                print(f"[aprobación] {'s' if ok else 'n'}")
                decisiones.append({"type": "approve"} if ok else {
                    "type": "reject", "message": "Un operador ha rechazado esta acción. No la repitas."})
            entrada = Command(resume={"decisions": decisiones})
    except ModelCallLimitExceededError:
        return "He alcanzado el límite de pasos sin terminar. Paso el caso a una persona."


if __name__ == "__main__":
    print(ejecutar())

