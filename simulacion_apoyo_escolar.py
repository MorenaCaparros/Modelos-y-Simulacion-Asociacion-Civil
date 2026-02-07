"""
=============================================================================
 Modelos y Simulación — Trabajo Práctico
 Simulación de Eventos Discretos: Centro de Apoyo Escolar (Asociación Civil)
=============================================================================

Descripción:
    Este script simula el funcionamiento de un Centro de Apoyo Escolar
    perteneciente a una Asociación Civil. Se modela la llegada de niños
    que solicitan apoyo escolar y son atendidos por voluntarios.

    Se utiliza SimPy para modelar:
      - La llegada estocástica de niños (proceso de Poisson → tiempos
        exponenciales entre llegadas).
      - La atención por parte de voluntarios (recurso compartido limitado).
      - La duración de cada clase (distribución normal truncada).

Objetivo:
    Determinar si la cantidad de voluntarios configurada es suficiente
    para cubrir la demanda, analizando:
      • Tiempo promedio de espera en cola.
      • Porcentaje de ocupación de los voluntarios.

Autor:  Estudiante — Cátedra de Modelos y Simulación
Fecha:  2026
"""

import simpy
import random
import statistics

# ===========================================================================
#  VARIABLES DE CONTROL (configurables por el usuario)
# ===========================================================================

NUM_VOLUNTARIOS = 3          # Cantidad de voluntarios disponibles
TIEMPO_SIMULACION = 480      # Duración de la simulación en minutos (ej. 8 hs)
TASA_LLEGADA = 1 / 10        # Tasa λ para llegadas (1 niño cada ~10 min)
DURACION_CLASE_MEDIA = 45    # Media de la duración de la clase (minutos)
DURACION_CLASE_DESVIO = 10   # Desvío estándar de la duración de la clase (min)
SEMILLA = 42                 # Semilla para reproducibilidad


# ===========================================================================
#  CLASE PRINCIPAL: CentroApoyo
# ===========================================================================

class CentroApoyo:
    """
    Representa el Centro de Apoyo Escolar de la Asociación Civil.

    Atributos:
        env (simpy.Environment):
            El entorno de simulación de SimPy.
        voluntarios (simpy.Resource):
            Recurso compartido que modela a los voluntarios. Cuando todos
            están ocupados, los niños deben esperar en cola.
        num_voluntarios (int):
            Cantidad total de voluntarios configurados.
        tiempos_espera (list[float]):
            Lista que almacena el tiempo de espera en cola de cada niño.
        tiempos_ocupacion (list[float]):
            Lista que almacena el tiempo de atención efectiva de cada
            voluntario por cada niño atendido (para calcular la ocupación).
    """

    def __init__(self, env: simpy.Environment, num_voluntarios: int):
        """
        Inicializa el Centro de Apoyo Escolar.

        Args:
            env: Entorno de simulación de SimPy.
            num_voluntarios: Cantidad de voluntarios disponibles.
        """
        self.env = env
        self.num_voluntarios = num_voluntarios
        # Creamos el recurso con capacidad = cantidad de voluntarios
        self.voluntarios = simpy.Resource(env, capacity=num_voluntarios)

        # Listas para recolectar estadísticas
        self.tiempos_espera: list[float] = []
        self.tiempos_ocupacion: list[float] = []

    # -----------------------------------------------------------------------
    #  Proceso: Atender a un niño
    # -----------------------------------------------------------------------
    def atender_nino(self, nombre: str):
        """
        Proceso de SimPy que modela la experiencia completa de un niño
        en el centro de apoyo escolar:
            1. Llega al centro.
            2. Solicita un voluntario (espera si no hay disponible).
            3. Recibe la clase de apoyo (duración aleatoria ~ Normal).
            4. Se retira del centro.

        Args:
            nombre: Identificador del niño (para logging).
        """
        # Momento en que el niño llega al centro
        tiempo_llegada = self.env.now
        print(f"  [{self.env.now:6.1f} min] 🧒 {nombre} llega al centro.")

        # --- Solicitar un voluntario (puede haber espera en cola) ----------
        with self.voluntarios.request() as solicitud:
            yield solicitud  # Espera hasta que un voluntario esté libre

            # Calcular cuánto tiempo esperó en cola
            tiempo_espera = self.env.now - tiempo_llegada
            self.tiempos_espera.append(tiempo_espera)

            if tiempo_espera > 0:
                print(f"  [{self.env.now:6.1f} min] ⏳ {nombre} esperó "
                      f"{tiempo_espera:.1f} min en cola.")
            else:
                print(f"  [{self.env.now:6.1f} min] ✅ {nombre} es atendido "
                      f"de inmediato.")

            # --- Duración de la clase (distribución normal truncada) -------
            # Se trunca para que no sea negativa ni absurdamente larga
            duracion = max(
                15,  # mínimo 15 minutos
                min(
                    random.gauss(DURACION_CLASE_MEDIA, DURACION_CLASE_DESVIO),
                    90   # máximo 90 minutos
                )
            )
            self.tiempos_ocupacion.append(duracion)

            print(f"  [{self.env.now:6.1f} min] 📖 {nombre} comienza su clase "
                  f"(duración: {duracion:.1f} min).")

            # El voluntario queda ocupado durante la clase
            yield self.env.timeout(duracion)

        # El niño se retira (el voluntario queda libre automáticamente)
        print(f"  [{self.env.now:6.1f} min] 👋 {nombre} terminó su clase y "
              f"se retira.")

    # -----------------------------------------------------------------------
    #  Reportes de estadísticas
    # -----------------------------------------------------------------------
    def reporte(self):
        """
        Imprime un resumen estadístico al finalizar la simulación:
          - Cantidad total de niños atendidos.
          - Tiempo promedio de espera en cola.
          - Tiempo máximo de espera en cola.
          - Porcentaje de ocupación de los voluntarios.
        """
        print("\n" + "=" * 65)
        print("  📊  RESULTADOS DE LA SIMULACIÓN")
        print("=" * 65)

        total_ninos = len(self.tiempos_espera)
        print(f"\n  ▸ Niños que llegaron al centro:    {total_ninos}")
        print(f"  ▸ Voluntarios disponibles:         {self.num_voluntarios}")
        print(f"  ▸ Tiempo de simulación:            {TIEMPO_SIMULACION} min "
              f"({TIEMPO_SIMULACION / 60:.1f} horas)")

        # --- Tiempo promedio de espera en cola -----------------------------
        if total_ninos > 0:
            promedio_espera = statistics.mean(self.tiempos_espera)
            max_espera = max(self.tiempos_espera)
            ninos_esperaron = sum(1 for t in self.tiempos_espera if t > 0)
        else:
            promedio_espera = 0
            max_espera = 0
            ninos_esperaron = 0

        print(f"\n  ▸ Tiempo promedio de espera:       {promedio_espera:.2f} min")
        print(f"  ▸ Tiempo máximo de espera:         {max_espera:.2f} min")
        print(f"  ▸ Niños que tuvieron que esperar:  {ninos_esperaron} "
              f"({(ninos_esperaron / total_ninos * 100) if total_ninos > 0 else 0:.1f}%)")

        # --- Porcentaje de ocupación de los voluntarios --------------------
        # Tiempo total de atención / (voluntarios × tiempo simulado) × 100
        if self.tiempos_ocupacion:
            tiempo_total_atencion = sum(self.tiempos_ocupacion)
            capacidad_total = self.num_voluntarios * TIEMPO_SIMULACION
            porcentaje_ocupacion = (tiempo_total_atencion / capacidad_total) * 100
        else:
            porcentaje_ocupacion = 0
            tiempo_total_atencion = 0

        print(f"\n  ▸ Tiempo total de atención:        {tiempo_total_atencion:.1f} min")
        print(f"  ▸ Capacidad total disponible:      "
              f"{self.num_voluntarios} vol × {TIEMPO_SIMULACION} min = "
              f"{self.num_voluntarios * TIEMPO_SIMULACION} min")
        print(f"  ▸ Porcentaje de ocupación:         {porcentaje_ocupacion:.1f}%")

        # --- Interpretación rápida -----------------------------------------
        print("\n  " + "-" * 61)
        if porcentaje_ocupacion > 85:
            print("  ⚠️  ALERTA: Los voluntarios están MUY sobrecargados.")
            print("  Se recomienda incorporar más voluntarios.")
        elif porcentaje_ocupacion > 60:
            print("  ℹ️  Los voluntarios tienen una carga MODERADA.")
            print("  El sistema funciona pero con poca holgura.")
        else:
            print("  ✅  Los voluntarios tienen capacidad suficiente.")
            print("  El sistema opera con holgura aceptable.")
        print("=" * 65)


# ===========================================================================
#  GENERADOR DE LLEGADAS DE NIÑOS
# ===========================================================================

def llegada_ninos(env: simpy.Environment, centro: CentroApoyo):
    """
    Proceso generador de SimPy que crea la llegada continua de niños
    al centro de apoyo escolar.

    Los tiempos entre llegadas siguen una distribución exponencial
    (modelando un proceso de Poisson), lo cual es estándar para
    modelar llegadas aleatorias en sistemas de colas.

    Args:
        env: Entorno de simulación de SimPy.
        centro: Instancia del CentroApoyo donde llegan los niños.
    """
    contador = 0
    while True:
        # Tiempo hasta la próxima llegada (distribución exponencial)
        tiempo_entre_llegadas = random.expovariate(TASA_LLEGADA)
        yield env.timeout(tiempo_entre_llegadas)

        # Llega un nuevo niño
        contador += 1
        nombre = f"Niño-{contador:03d}"

        # Lanzamos el proceso de atención para este niño
        env.process(centro.atender_nino(nombre))


# ===========================================================================
#  FUNCIÓN PRINCIPAL
# ===========================================================================

def main():
    """
    Función principal que configura y ejecuta la simulación.
    """
    # Configurar semilla para reproducibilidad
    random.seed(SEMILLA)

    print("=" * 65)
    print("  🏫  SIMULACIÓN: Centro de Apoyo Escolar — Asociación Civil")
    print("=" * 65)
    print(f"\n  Configuración:")
    print(f"    • Voluntarios:            {NUM_VOLUNTARIOS}")
    print(f"    • Tiempo de simulación:   {TIEMPO_SIMULACION} min "
          f"({TIEMPO_SIMULACION / 60:.1f} horas)")
    print(f"    • Llegada promedio:       1 niño cada "
          f"{1 / TASA_LLEGADA:.0f} min")
    print(f"    • Duración media clase:   {DURACION_CLASE_MEDIA} ± "
          f"{DURACION_CLASE_DESVIO} min")
    print(f"    • Semilla aleatoria:      {SEMILLA}")
    print("\n" + "-" * 65)
    print("  📋  LOG DE EVENTOS:")
    print("-" * 65)

    # --- Crear entorno de SimPy -------------------------------------------
    env = simpy.Environment()

    # --- Crear el centro de apoyo -----------------------------------------
    centro = CentroApoyo(env, num_voluntarios=NUM_VOLUNTARIOS)

    # --- Iniciar el proceso de llegada de niños ---------------------------
    env.process(llegada_ninos(env, centro))

    # --- Ejecutar la simulación -------------------------------------------
    env.run(until=TIEMPO_SIMULACION)

    # --- Mostrar resultados -----------------------------------------------
    centro.reporte()


# ===========================================================================
#  EJECUCIÓN
# ===========================================================================

if __name__ == "__main__":
    main()
