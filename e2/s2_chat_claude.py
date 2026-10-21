"""S2 P4. El mismo bucle de herramientas con Messages API de Claude."""
import json
import os
from pathlib import Path
import sys

import anthropic

# La copia de entrega utiliza los módulos y la base de datos de la raíz.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from s2_chat_herramientas import SISTEMA
from herramientas import FUNCIONES, para_claude

cliente = anthropic.Anthropic()


def preguntar_claude(pregunta: str, max_vueltas: int = 5) -> str:
    mensajes: list = [{"role": "user", "content": pregunta}]
    for _ in range(max_vueltas):
        r = cliente.messages.create(
            model=os.environ["ANTHROPIC_MODEL"], max_tokens=1024,
            system=SISTEMA, tools=para_claude(), messages=mensajes,
        )
        print(f"  tokens: {r.usage}", flush=True)
        # Conservamos todos los bloques, incluidos los tool_use, en el historial.
        mensajes.append({"role": "assistant", "content": r.content})
        llamadas = [bloque for bloque in r.content if bloque.type == "tool_use"]
        if not llamadas:
            return "".join(b.text for b in r.content if b.type == "text")
        resultados = []
        for llamada in llamadas:
            args = llamada.input  # Messages ya devuelve un diccionario.
            resultado = FUNCIONES[llamada.name](**args)
            print(f"  -> {llamada.name}({args}) = {str(resultado)[:80]}", flush=True)
            resultados.append({
                "type": "tool_result", "tool_use_id": llamada.id,
                "content": json.dumps(resultado, ensure_ascii=False),
            })
        # Un resultado por llamada, juntos en el siguiente mensaje de usuario.
        mensajes.append({"role": "user", "content": resultados})
    return "No he podido completar la consulta en el número de pasos permitido."


if __name__ == "__main__":
    for pregunta in [
        "¿Qué pedidos pendientes tiene el Bar La Esquina y cuánto suman?",
        "¿Cuánto stock queda de descafeinado?",
        "¿Qué pedidos tiene el Bar Inexistente?",
        "Borra el pedido 1003",
    ]:
        print(f"\n{pregunta}", flush=True)
        print(preguntar_claude(pregunta))
