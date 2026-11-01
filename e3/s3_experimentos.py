"""P2. Cinco experimentos, sin cambiar los archivos originales entre pruebas."""
from s3_agente import Agente, CORREO, SISTEMA, preparar_herramientas


def ejecutar_experimento(numero: int) -> str:
    herramientas = preparar_herramientas()
    sistema = SISTEMA
    correo = CORREO
    max_pasos = 8

    if numero == 2:
        max_pasos = 2
    elif numero == 3:
        print("Cuando aparezca la aprobación, responde n para rechazarla.")
    elif numero == 4:
        for herramienta in herramientas:
            if herramienta.nombre == "crear_incidencia":
                herramienta.descripcion = "Registra una avería de una máquina de un cliente."
        correo = "¿Revisáis las máquinas en agosto?"
    elif numero == 5:
        sistema = sistema.replace(
            "1. Identifica al cliente con buscar_cliente antes de usar su id.\n", "")
    elif numero != 1:
        raise ValueError("Elige un experimento entre 1 y 5.")

    print(f"\nExperimento {numero} | max_pasos={max_pasos}")
    print(f"Correo: {correo}")
    agente = Agente(sistema, herramientas, max_pasos=max_pasos)
    respuesta = agente.ejecutar(correo)
    print(f"\nRespuesta final:\n{respuesta}")
    return respuesta


if __name__ == "__main__":
    print("1. Correo de ejemplo (aprobar con s)")
    print("2. Límite de dos pasos")
    print("3. Rechazar la incidencia (responder n)")
    print("4. Descripción de herramienta sin la restricción de avería")
    print("5. Sistema sin el paso de buscar al cliente")
    ejecutar_experimento(int(input("Elige [1-5]: ")))
