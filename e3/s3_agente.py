"""Sesión 3. Un agente desde cero: bucle, límite de pasos, trazas y aprobación humana.

Proveedor: Claude (Messages API). El patrón es idéntico con OpenAI o Gemini."""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import anthropic
from dotenv import load_dotenv

from herramientas import DEFINICIONES, FUNCIONES

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass
class Herramienta:
    nombre: str
    descripcion: str
    esquema: dict
    funcion: Callable
    requiere_aprobacion: bool = False


class Agente:
    def __init__(self, sistema: str, herramientas: list[Herramienta], max_pasos: int = 8):
        self.llm = anthropic.Anthropic(timeout=60.0, max_retries=1)
        self.modelo = os.environ["ANTHROPIC_MODEL"]
        self.sistema, self.max_pasos = sistema, max_pasos
        self.herramientas = {h.nombre: h for h in herramientas}

    def _definiciones(self) -> list[dict]:
        return [{"name": h.nombre, "description": h.descripcion, "input_schema": h.esquema}
                for h in self.herramientas.values()]

    def _ejecutar(self, nombre: str, args: dict) -> tuple[object, bool]:
        """Devuelve (resultado, es_error). Los errores vuelven al modelo para que se corrija."""
        h = self.herramientas.get(nombre)
        if h is None:
            return f"La herramienta {nombre} no existe.", True
        if h.requiere_aprobacion:
            decision = input(f"  ¿Aprobar {nombre}({args})? [s/N] ").strip().lower()
            print(f"[aprobación] {'s' if decision == 's' else 'n'}")
            if decision != "s":
                return "Un operador humano ha rechazado esta acción. No la repitas.", True
        try:
            salida = h.funcion(**args)
            return salida, isinstance(salida, dict) and "error" in salida
        except Exception as e:  # argumentos inventados, fallo de BD...
            return f"Error al ejecutar {nombre}: {e}", True

    def ejecutar(self, objetivo: str) -> str:
        mensajes: list = [{"role": "user", "content": objetivo}]
        for paso in range(1, self.max_pasos + 1):
            r = self.llm.messages.create(
                model=self.modelo, max_tokens=2048, system=self.sistema,
                tools=self._definiciones(), messages=mensajes,
            )
            mensajes.append({"role": "assistant", "content": r.content})
            print(f"[paso {paso}] tokens: entrada={r.usage.input_tokens}, "
                  f"salida={r.usage.output_tokens}")
            if r.stop_reason != "tool_use":  # condición de parada: respuesta final
                return "".join(b.text for b in r.content if b.type == "text")
            resultados = []
            for bloque in r.content:
                if bloque.type == "text" and bloque.text.strip():
                    print(f"[paso {paso}] texto del modelo: {bloque.text.strip()}")
                if bloque.type != "tool_use":
                    continue
                salida, es_error = self._ejecutar(bloque.name, bloque.input)
                print(f"[paso {paso}] {bloque.name}({bloque.input}) -> {salida} "
                      f"(error={es_error})")
                resultados.append({
                    "type": "tool_result", "tool_use_id": bloque.id, "is_error": es_error,
                    "content": json.dumps(salida, ensure_ascii=False, default=str),
                })
            mensajes.append({"role": "user", "content": resultados})
        return "He alcanzado el límite de pasos sin terminar. Paso el caso a una persona."


SISTEMA = """Eres el agente de atención técnica de Tostadero Retiro S.L.
Objetivo: resolver correos de clientes usando las herramientas.
Procedimiento:
1. Identifica al cliente con buscar_cliente antes de usar su id.
2. Si hay una avería, registra una incidencia con la prioridad adecuada
   (alta si el local no puede servir café).
   Consulta stock_producto para conocer el SKU de la máquina; no lo inventes.
3. Si preguntan por pedidos, consulta los datos reales; no inventes cifras.
   No prometas fechas de entrega ni visitas técnicas que las herramientas no confirmen.
4. Termina con una respuesta breve al cliente, en español y con tono cordial."""

CORREO = ("Buenas, os escribo del Restaurante Lumbre. La cafetera de dos grupos no "
          "calienta y hoy no podemos servir cafés. ¿Además, cuándo llega el pedido pendiente?")


def preparar_herramientas() -> list[Herramienta]:
    return [
        Herramienta(d["name"], d["description"], d["parameters"], FUNCIONES[d["name"]],
                    requiere_aprobacion=(d["name"] == "crear_incidencia"))
        for d in DEFINICIONES
    ]


if __name__ == "__main__":
    agente = Agente(SISTEMA, preparar_herramientas())
    print(agente.ejecutar(CORREO))

