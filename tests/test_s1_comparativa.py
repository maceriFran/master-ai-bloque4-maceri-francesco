"""Comprueba el CSV y la reutilización de clientes sin consumir APIs."""
import contextlib
import csv
import io
import os
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class ComparativaTests(unittest.TestCase):
    def test_quince_filas_clientes_reutilizados_y_texto_completo(self):
        script = Path(__file__).resolve().parents[1] / "s1_comparativa.py"
        clientes = []
        texto = 'Respuesta con coma, comillas "citadas" y salto\nde línea.'

        class ClienteSimulado:
            def __init__(self, proveedor):
                self.proveedor = proveedor
                self.llamadas = []
                clientes.append(self)

            def responder(self, sistema, correo):
                self.llamadas.append((sistema, correo))
                return SimpleNamespace(segundos=1.2345, tokens_entrada=12,
                                       tokens_salida=34, coste_usd=0.0002, texto=texto)

        salida = io.StringIO()
        with tempfile.TemporaryDirectory() as carpeta:
            anterior = Path.cwd()
            try:
                os.chdir(carpeta)
                with patch.dict("sys.modules", {"llm_client": SimpleNamespace(LLM=ClienteSimulado)}):
                    with contextlib.redirect_stdout(salida):
                        variables = runpy.run_path(str(script), run_name="__main__")
                with open("comparativa.csv", newline="", encoding="utf-8") as f:
                    lector = csv.DictReader(f)
                    filas = list(lector)
                    self.assertEqual(lector.fieldnames, ["proveedor", "correo", "segundos",
                        "tokens_entrada", "tokens_salida", "coste_usd", "calidad_1a5", "respuesta"])
            finally:
                os.chdir(anterior)
        self.assertEqual([c.proveedor for c in clientes], ["openai", "claude", "gemini"])
        self.assertEqual(len(filas), 15)
        for cliente in clientes:
            self.assertEqual(cliente.llamadas, [(variables["SISTEMA"], c) for c in variables["CORREOS"]])
            self.assertEqual(sum(f["proveedor"] == cliente.proveedor for f in filas), 5)
        for fila in filas:
            self.assertEqual(fila["respuesta"], texto)
            self.assertEqual(fila["segundos"], "1.23")
            self.assertEqual(fila["calidad_1a5"], "")
            self.assertEqual(float(fila["coste_usd"]), 0.0002)
            self.assertEqual((fila["tokens_entrada"], fila["tokens_salida"]), ("12", "34"))
        self.assertEqual(sum("correo " in linea for linea in salida.getvalue().splitlines()), 15)


if __name__ == "__main__":
    unittest.main()
