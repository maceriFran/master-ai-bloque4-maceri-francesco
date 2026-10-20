"""Validación local de S2 P1, sin llamadas a modelos."""
import contextlib
import io
import unittest
from unittest.mock import patch

with patch("dotenv.load_dotenv"):
    import s2_extraer_correo as s2


class ClasificadorTests(unittest.TestCase):
    def resultado(self, cliente=None, cantidad=1):
        return s2.CorreoClasificado(tipo="pedido", cliente=cliente,
            lineas=[s2.Linea(producto="blend", cantidad=cantidad)],
            urgente=False, resumen="Pedido de café.")

    def test_cliente_existente_y_cliente_desconocido(self):
        with patch.object(s2, "buscar_cliente", return_value=[{"id": 1}]) as buscar:
            self.assertEqual(s2.validar_negocio(self.resultado("Bar La Esquina")), [])
            buscar.assert_called_once_with("Bar La Esquina")
        with patch.object(s2, "buscar_cliente", return_value=[]):
            avisos = s2.validar_negocio(self.resultado("Café Nube Azul"))
            self.assertIn("cliente no encontrado", avisos[0])

    def test_sin_cliente_no_consulta_bd_y_valida_cantidad(self):
        with patch.object(s2, "buscar_cliente") as buscar:
            self.assertEqual(s2.validar_negocio(self.resultado()), [])
            self.assertEqual(s2.validar_negocio(self.resultado(cantidad=0)), ["cantidad no válida"])
            buscar.assert_not_called()

    def test_none_y_error_no_rompen_el_bucle_ni_reducen_denominador(self):
        salida = io.StringIO()
        with patch.object(s2, "CASOS", [("correo de prueba", "pedido")]), \
             patch.object(s2, "con_openai", return_value=None), \
             patch.object(s2, "con_claude", side_effect=RuntimeError("detalle no publicable")), \
             patch.object(s2, "con_gemini", return_value=self.resultado()), \
             patch.object(s2, "validar_negocio", return_value=[]), \
             patch.object(s2.Path, "is_file", return_value=True), \
             contextlib.redirect_stdout(salida):
            s2.evaluar()
        texto = salida.getvalue()
        self.assertIn("OpenAI: 0/1", texto)
        self.assertIn("Claude: 0/1", texto)
        self.assertIn("Gemini: 1/1", texto)
        self.assertIn("sin salida estructurada", texto)
        self.assertNotIn("detalle no publicable", texto)

    def test_casos_suficientes_y_etiquetas_validas(self):
        self.assertGreaterEqual(len(s2.CASOS), 15)
        self.assertEqual(len({c for c, _ in s2.CASOS}), len(s2.CASOS))
        self.assertTrue(all(t in {"pedido", "incidencia", "consulta", "mixto"} for _, t in s2.CASOS))


if __name__ == "__main__":
    unittest.main()
