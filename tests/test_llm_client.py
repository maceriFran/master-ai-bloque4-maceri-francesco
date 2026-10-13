"""Pruebas sin red: contrato del adaptador y contabilidad de tokens."""
import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

with patch("dotenv.load_dotenv"):
    from llm_client import LLM, Respuesta


class AdaptadorTests(unittest.TestCase):
    def cliente(self, formato):
        llm = object.__new__(LLM)
        llm.modelo = "modelo-de-prueba"
        llm.formato = formato
        # Los tokens incluyen más que el texto: el adaptador no debe recortarlos.
        respuesta = NS(
            output_text="hola", content=[NS(type="text", text="ho"),
                                         NS(type="thinking"), NS(type="text", text="la")],
            choices=[NS(message=NS(content="hola"))],
            usage=NS(input_tokens=11, output_tokens=27, total_input_tokens=11,
                     total_output_tokens=27, prompt_tokens=11, completion_tokens=27),
        )
        crear = Mock(return_value=respuesta)
        llm._c = NS(responses=NS(create=crear), messages=NS(create=crear),
                    interactions=NS(create=crear), chat=NS(completions=NS(create=crear)))
        return llm, crear

    def test_limite_temperatura_y_respuesta_en_los_cuatro_formatos(self):
        for formato in ("responses", "messages", "interactions", "chat"):
            with self.subTest(formato=formato):
                llm, crear = self.cliente(formato)
                r = llm.responder("sistema", "pregunta", temperatura=0, max_tokens=20)
                args = crear.call_args.kwargs
                config = args["generation_config"] if formato == "interactions" else args
                limite = "max_output_tokens" if formato in ("responses", "interactions") else "max_tokens"
                self.assertEqual(config[limite], 20)
                self.assertEqual(config["temperature"], 0)
                self.assertEqual(args["model"], "modelo-de-prueba")
                if formato == "responses":
                    self.assertEqual(args["instructions"], "sistema")
                    self.assertEqual(args["input"], "pregunta")
                elif formato == "messages":
                    self.assertEqual(args["system"], "sistema")
                    self.assertEqual(args["messages"], [{"role": "user", "content": "pregunta"}])
                elif formato == "interactions":
                    self.assertEqual(args["system_instruction"], "sistema")
                    self.assertEqual(args["input"], "pregunta")
                else:
                    self.assertEqual(args["messages"], [{"role": "system", "content": "sistema"},
                                                        {"role": "user", "content": "pregunta"}])
                self.assertEqual((r.texto, r.tokens_entrada, r.tokens_salida), ("hola", 11, 27))
                self.assertGreaterEqual(r.segundos, 0)

    def test_valores_omitidos_y_limite_obligatorio_de_claude(self):
        for formato in ("responses", "messages", "interactions", "chat"):
            with self.subTest(formato=formato):
                llm, crear = self.cliente(formato)
                llm.responder("sistema", "pregunta")
                args = crear.call_args.kwargs
                self.assertNotIn("temperature", args)
                self.assertNotIn("generation_config", args)
                self.assertNotIn("max_output_tokens", args)
                if formato == "messages":
                    self.assertEqual(args["max_tokens"], 512)
                else:
                    self.assertNotIn("max_tokens", args)

    def test_coste_y_modelo_sin_precio(self):
        r = Respuesta("hola", 100, 20, 0.1, "anthropic/claude-haiku-4.5")
        self.assertAlmostEqual(r.coste_usd, 0.0002)
        self.assertIsNone(Respuesta("hola", 100, 20, 0.1, "desconocido").coste_usd)

    def test_chat_sin_texto_conserva_los_tokens_reportados(self):
        llm, crear = self.cliente("chat")
        crear.return_value.choices[0].message.content = None
        r = llm.responder("sistema", "pregunta", max_tokens=20)
        self.assertEqual(r.texto, "")
        self.assertEqual(r.tokens_salida, 27)


if __name__ == "__main__":
    unittest.main()
