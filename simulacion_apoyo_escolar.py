"""
=============================================================================
 Modelos y Simulación — Trabajo Práctico
 Simulación de Eventos Discretos: Centro de Apoyo Escolar (Asociación Civil)
=============================================================================

 Universidad:  Universidad Católica de Salta
 Carrera:      Licenciatura en Ciencia de Datos
 Materia:      Modelos y Simulación
 Docente:      Gustavo Ramiro Rivadera
 Alumno:       Morena Caparros
 Fecha:        2026

Descripción:
    Una Asociación Civil funciona como nexo entre niños con dificultades
    de aprendizaje y voluntarios que brindan apoyo escolar. Un Equipo
    Profesional evalúa a cada niño, detecta carencias (lectoescritura,
    matemáticas, grafismos) y diseña un plan de trabajo personalizado.

    Este script modela el sistema completo mediante Simulación de Eventos
    Discretos (DES) con SimPy, incluyendo:

    ENTIDADES DE FLUJO (Niños):
      - Atributo «Dificultad»: Leve / Moderada / Grave  (probabilístico)
      - Atributo «Área»: Matemática / Lectura / Grafismo (probabilístico)

    RECURSOS (Voluntarios):
      - Clasificados por «Nivel de Expertise» (1-Básico, 2-Intermedio, 3-Avanzado)
      - Clasificados por «Área de competencia»
      - Disponibilidad limitada

    SERVIDORES (Equipo Profesional):
      - Recurso limitado que valida cada asignación niño-voluntario
      - Genera cuello de botella si hay pocos profesionales

    ALGORITMO DE MATCHING:
      - Regla: Skill del voluntario >= Dificultad del niño, en el área correcta.
      - Política configurable: match estricto vs. asignación generalista.

    ESCENARIOS DE PRUEBA:
      - Escenario Base: Operación normal.
      - Escenario A (Déficit): Alta demanda de dificultades graves, pocos
        voluntarios capacitados.
      - Escenario B (Crecimiento): Aumento del 200% en la matrícula.

    KPIs MEDIDOS:
      - Tiempo promedio de espera en cola antes de asignación.
      - Tasa de «Mal Matching» (niños atendidos por voluntarios no óptimos).
      - Porcentaje de ocupación de los voluntarios.
      - Porcentaje de ocupación del Equipo Profesional.
"""

import simpy
import random
import statistics
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


# ===========================================================================
#  ENUMERACIONES Y CONSTANTES DEL DOMINIO
# ===========================================================================

class Dificultad(IntEnum):
    """Nivel de dificultad de aprendizaje del niño (también sirve como
    nivel mínimo de expertise requerido en el voluntario)."""
    LEVE = 1
    MODERADA = 2
    GRAVE = 3


class Area(IntEnum):
    """Área de carencia del niño / competencia del voluntario."""
    MATEMATICA = 1
    LECTURA = 2
    GRAFISMO = 3


# Etiquetas legibles para impresión
NOMBRE_DIFICULTAD = {Dificultad.LEVE: "Leve", Dificultad.MODERADA: "Moderada",
                     Dificultad.GRAVE: "Grave"}
NOMBRE_AREA = {Area.MATEMATICA: "Matemática", Area.LECTURA: "Lectura",
               Area.GRAFISMO: "Grafismo"}


# ===========================================================================
#  DATACLASSES: Niño y Voluntario
# ===========================================================================

@dataclass
class Nino:
    """Entidad de flujo: representa a un niño que llega al centro."""
    id: int
    nombre: str
    dificultad: Dificultad       # Leve / Moderada / Grave
    area: Area                   # Matemática / Lectura / Grafismo
    tiempo_llegada: float = 0.0  # Instante en que llega al sistema


@dataclass
class Voluntario:
    """Recurso individual: representa a un voluntario del centro."""
    id: int
    nombre: str
    expertise: int               # 1=Básico, 2=Intermedio, 3=Avanzado
    area: Area                   # Área de competencia principal
    ocupado: bool = False
    tiempo_ocupado_total: float = 0.0  # Acumulador para calcular ocupación


# ===========================================================================
#  CONFIGURACIÓN DE ESCENARIOS
# ===========================================================================

@dataclass
class ConfigEscenario:
    """Agrupa todas las variables de control de un escenario de simulación."""
    nombre: str

    # --- Tiempo ---
    tiempo_simulacion: float  # En semanas virtuales (unidad de tiempo)
    semilla: int = 42

    # --- Demanda (Niños) ---
    tasa_llegada: float = 1.0           # Niños por semana (lambda Poisson)
    prob_dificultad: dict = field(default_factory=lambda: {
        Dificultad.LEVE: 0.50,
        Dificultad.MODERADA: 0.35,
        Dificultad.GRAVE: 0.15,
    })
    prob_area: dict = field(default_factory=lambda: {
        Area.MATEMATICA: 0.45,
        Area.LECTURA: 0.35,
        Area.GRAFISMO: 0.20,
    })

    # --- Oferta (Voluntarios) ---
    voluntarios_spec: list = field(default_factory=list)
    # Cada elemento: {"nombre": str, "expertise": int, "area": Area}

    # --- Equipo Profesional (servidor de validación) ---
    num_profesionales: int = 2
    tiempo_evaluacion_media: float = 1.5   # Semanas que tarda la evaluación
    tiempo_evaluacion_desvio: float = 0.5

    # --- Duración de la intervención pedagógica ---
    duracion_intervencion_media: float = 6.0   # Semanas
    duracion_intervencion_desvio: float = 2.0

    # --- Política de matching ---
    # True = si no hay match exacto, se asigna un generalista (mal matching)
    # False = el niño espera hasta que haya un voluntario adecuado
    permitir_generalista: bool = True


# ---------------------------------------------------------------------------
#  ESCENARIOS PREDEFINIDOS (Sección 4.3 del anteproyecto)
# ---------------------------------------------------------------------------

def crear_voluntarios_base() -> list:
    """Pool de voluntarios para el escenario base y de crecimiento."""
    return [
        {"nombre": "Vol-01", "expertise": 3, "area": Area.MATEMATICA},
        {"nombre": "Vol-02", "expertise": 2, "area": Area.MATEMATICA},
        {"nombre": "Vol-03", "expertise": 3, "area": Area.LECTURA},
        {"nombre": "Vol-04", "expertise": 2, "area": Area.LECTURA},
        {"nombre": "Vol-05", "expertise": 1, "area": Area.LECTURA},
        {"nombre": "Vol-06", "expertise": 2, "area": Area.GRAFISMO},
        {"nombre": "Vol-07", "expertise": 1, "area": Area.GRAFISMO},
        {"nombre": "Vol-08", "expertise": 1, "area": Area.MATEMATICA},
    ]


ESCENARIO_BASE = ConfigEscenario(
    nombre="Base (Operación Normal)",
    tiempo_simulacion=52,       # 52 semanas = 1 año
    tasa_llegada=3.0,           # ~3 niños nuevos por semana
    voluntarios_spec=crear_voluntarios_base(),
    num_profesionales=2,
    permitir_generalista=True,
)

ESCENARIO_A_DEFICIT = ConfigEscenario(
    nombre="A - Déficit de Recursos",
    tiempo_simulacion=52,
    tasa_llegada=5.0,           # Alta demanda
    prob_dificultad={           # Mayoría graves
        Dificultad.LEVE: 0.15,
        Dificultad.MODERADA: 0.30,
        Dificultad.GRAVE: 0.55,
    },
    voluntarios_spec=[          # Pocos y de bajo nivel
        {"nombre": "Vol-01", "expertise": 1, "area": Area.MATEMATICA},
        {"nombre": "Vol-02", "expertise": 1, "area": Area.LECTURA},
        {"nombre": "Vol-03", "expertise": 2, "area": Area.GRAFISMO},
        {"nombre": "Vol-04", "expertise": 1, "area": Area.MATEMATICA},
    ],
    num_profesionales=1,        # Solo 1 profesional
    permitir_generalista=True,
)

ESCENARIO_B_CRECIMIENTO = ConfigEscenario(
    nombre="B - Crecimiento 200%",
    tiempo_simulacion=52,
    tasa_llegada=9.0,           # 3x la tasa base (200% de aumento)
    voluntarios_spec=crear_voluntarios_base(),  # Mismos voluntarios
    num_profesionales=2,
    permitir_generalista=True,
)


# ===========================================================================
#  CLASE PRINCIPAL: CentroApoyo
# ===========================================================================

class CentroApoyo:
    """
    Modelo del Centro de Apoyo Escolar de la Asociación Civil.

    Componentes del sistema (Sección 4.1 del anteproyecto):
      - Entidades de flujo: Niños (generados estocásticamente).
      - Recursos: Voluntarios (con expertise y área).
      - Servidores: Equipo Profesional (valida asignaciones).
      - Colas: Diferenciadas por combinación dificultad/área.

    El centro coordina:
      1. Evaluación del niño por el Equipo Profesional.
      2. Matching con un voluntario adecuado.
      3. Intervención pedagógica.
      4. Liberación del voluntario.
    """

    def __init__(self, env: simpy.Environment, config: ConfigEscenario):
        self.env = env
        self.config = config

        # --- Recurso: Equipo Profesional (servidor de validación) ----------
        # Actúa como servidor único que evalúa y valida cada asignación.
        # Es el cuello de botella descrito en la sección 2 del anteproyecto.
        self.equipo_profesional = simpy.Resource(
            env, capacity=config.num_profesionales
        )

        # --- Recursos: Voluntarios individuales ----------------------------
        # Cada voluntario es un objeto con atributos; se gestiona la
        # disponibilidad como un pool diferenciado por skill y área.
        self.voluntarios: list[Voluntario] = []
        for i, spec in enumerate(config.voluntarios_spec):
            vol = Voluntario(
                id=i + 1,
                nombre=spec["nombre"],
                expertise=spec["expertise"],
                area=spec["area"],
            )
            self.voluntarios.append(vol)

        # --- Estadísticas / KPIs -------------------------------------------
        self.tiempos_espera_cola: list[float] = []       # Espera total
        self.tiempos_espera_profesional: list[float] = [] # Espera por Eq. Prof.
        self.tiempos_espera_voluntario: list[float] = []  # Espera por voluntario
        self.resultados_matching: list[dict] = []         # Info de cada matching
        self.ninos_atendidos: int = 0
        self.ninos_que_llegaron: int = 0
        self.tiempo_uso_profesional: float = 0.0          # Tiempo acumulado

    # -----------------------------------------------------------------------
    #  Algoritmo de Matching (Sección 4.2)
    # -----------------------------------------------------------------------
    def buscar_voluntario(self, nino: Nino) -> Optional[Voluntario]:
        """
        Busca el mejor voluntario disponible para un niño dado.

        Regla principal (match óptimo):
          - Voluntario.area == Niño.area
          - Voluntario.expertise >= Niño.dificultad

        Si no hay match óptimo y la política permite generalista:
          - Se busca cualquier voluntario libre con expertise >= dificultad
            (sin importar el área -> «Mal Matching»).

        Si la política NO permite generalista:
          - Se retorna None y el niño debe esperar.

        Args:
            nino: El niño que necesita ser asignado.

        Returns:
            Voluntario encontrado o None si no hay disponible.
        """
        disponibles = [v for v in self.voluntarios if not v.ocupado]

        if not disponibles:
            return None

        # --- Paso 1: Buscar match ÓPTIMO (misma área + expertise suficiente)
        optimos = [
            v for v in disponibles
            if v.area == nino.area and v.expertise >= nino.dificultad
        ]
        if optimos:
            # Elegir el de menor expertise suficiente (conservar los mejores)
            optimos.sort(key=lambda v: v.expertise)
            return optimos[0]

        # --- Paso 2: Si se permite generalista, buscar cualquiera con skill
        if self.config.permitir_generalista:
            # Primero: misma área pero expertise insuficiente
            misma_area = [v for v in disponibles if v.area == nino.area]
            if misma_area:
                misma_area.sort(key=lambda v: v.expertise, reverse=True)
                return misma_area[0]

            # Segundo: otra área pero con expertise suficiente
            otra_area_skill = [
                v for v in disponibles
                if v.expertise >= nino.dificultad
            ]
            if otra_area_skill:
                otra_area_skill.sort(key=lambda v: v.expertise)
                return otra_area_skill[0]

            # Último recurso: cualquier voluntario libre
            return disponibles[0]

        # --- Política estricta: no hay match, el niño espera
        return None

    def clasificar_matching(self, nino: Nino, voluntario: Voluntario) -> str:
        """
        Clasifica la calidad del matching realizado.

        Returns:
            'OPTIMO':      Misma área y expertise >= dificultad.
            'SUBOPTIMO':   Misma área pero expertise < dificultad.
            'GENERALISTA': Distinta área (mal matching pedagógico).
        """
        if voluntario.area == nino.area and voluntario.expertise >= nino.dificultad:
            return "OPTIMO"
        elif voluntario.area == nino.area:
            return "SUBOPTIMO"
        else:
            return "GENERALISTA"

    # -----------------------------------------------------------------------
    #  Proceso completo del Niño en el sistema (Sección 4.2)
    # -----------------------------------------------------------------------
    def proceso_nino(self, nino: Nino):
        """
        Proceso de SimPy que modela el ciclo de vida completo de un niño
        dentro del sistema de la Asociación Civil:

        1. LLEGADA: El niño ingresa al sistema con dificultad y área.
        2. EVALUACIÓN: El Equipo Profesional lo evalúa (recurso limitado,
           puede generar cola / cuello de botella).
        3. MATCHING: Se busca un voluntario adecuado según la lógica de
           asignación (Skill >= Dificultad, misma Área).
        4. INTERVENCIÓN: El voluntario trabaja con el niño durante un
           período (distribución normal).
        5. LIBERACIÓN: El voluntario queda libre para otro niño.
        """
        self.ninos_que_llegaron += 1
        tiempo_inicio = self.env.now

        print(f"  [{self.env.now:6.1f} sem] >> {nino.nombre} llega | "
              f"Dificultad: {NOMBRE_DIFICULTAD[nino.dificultad]} | "
              f"Area: {NOMBRE_AREA[nino.area]}")

        # ===================================================================
        #  FASE 1: Evaluación por el Equipo Profesional (servidor limitado)
        # ===================================================================
        tiempo_pre_prof = self.env.now
        with self.equipo_profesional.request() as turno_profesional:
            yield turno_profesional  # Espera si el equipo está ocupado

            espera_profesional = self.env.now - tiempo_pre_prof
            self.tiempos_espera_profesional.append(espera_profesional)

            if espera_profesional > 0.01:
                print(f"  [{self.env.now:6.1f} sem]    {nino.nombre} espero "
                      f"{espera_profesional:.1f} sem por el Eq. Profesional.")

            # Duración de la evaluación (distribución normal truncada)
            duracion_eval = max(
                0.5,
                random.gauss(
                    self.config.tiempo_evaluacion_media,
                    self.config.tiempo_evaluacion_desvio,
                )
            )
            self.tiempo_uso_profesional += duracion_eval
            yield self.env.timeout(duracion_eval)

            print(f"  [{self.env.now:6.1f} sem]    {nino.nombre} evaluado por "
                  f"Eq. Profesional (duro {duracion_eval:.1f} sem).")

        # ===================================================================
        #  FASE 2: Matching y asignación de voluntario
        # ===================================================================
        tiempo_pre_vol = self.env.now
        voluntario_asignado = None

        # Esperar hasta encontrar un voluntario (polling con re-check)
        while voluntario_asignado is None:
            voluntario_asignado = self.buscar_voluntario(nino)
            if voluntario_asignado is None:
                # No hay voluntario disponible -> esperar y reintentar
                yield self.env.timeout(0.25)  # Re-check cada 0.25 semanas

        espera_voluntario = self.env.now - tiempo_pre_vol
        self.tiempos_espera_voluntario.append(espera_voluntario)

        # Marcar voluntario como ocupado
        voluntario_asignado.ocupado = True

        # Clasificar la calidad del matching
        tipo_match = self.clasificar_matching(nino, voluntario_asignado)
        self.resultados_matching.append({
            "nino": nino.nombre,
            "dificultad": nino.dificultad,
            "area_nino": nino.area,
            "voluntario": voluntario_asignado.nombre,
            "expertise": voluntario_asignado.expertise,
            "area_vol": voluntario_asignado.area,
            "tipo_match": tipo_match,
        })

        simbolo = {"OPTIMO": "[OK]", "SUBOPTIMO": "[!!]", "GENERALISTA": "[XX]"}
        print(f"  [{self.env.now:6.1f} sem] {simbolo[tipo_match]} {nino.nombre} -> "
              f"{voluntario_asignado.nombre} "
              f"(Exp:{voluntario_asignado.expertise}, "
              f"Area:{NOMBRE_AREA[voluntario_asignado.area]}) "
              f"[Match: {tipo_match}]"
              + (f" (espero {espera_voluntario:.1f} sem)" if espera_voluntario > 0.01 else ""))

        # ===================================================================
        #  FASE 3: Intervención pedagógica
        # ===================================================================
        duracion_intervencion = max(
            2.0,
            random.gauss(
                self.config.duracion_intervencion_media,
                self.config.duracion_intervencion_desvio,
            )
        )
        yield self.env.timeout(duracion_intervencion)

        # Liberar voluntario
        voluntario_asignado.tiempo_ocupado_total += duracion_intervencion
        voluntario_asignado.ocupado = False
        self.ninos_atendidos += 1

        # Tiempo total en el sistema (espera = total - intervención)
        tiempo_total = self.env.now - tiempo_inicio
        self.tiempos_espera_cola.append(tiempo_total - duracion_intervencion)

        print(f"  [{self.env.now:6.1f} sem] << {nino.nombre} completo su "
              f"intervencion ({duracion_intervencion:.1f} sem). "
              f"Voluntario {voluntario_asignado.nombre} libre.")

    # -----------------------------------------------------------------------
    #  Reporte de KPIs (Sección 4.3)
    # -----------------------------------------------------------------------
    def reporte(self):
        """
        Genera el reporte completo de KPIs al finalizar la simulación,
        alineado con las métricas de éxito definidas en la sección 4.3
        del anteproyecto.
        """
        T = self.config.tiempo_simulacion
        sep = "=" * 70

        print(f"\n{sep}")
        print(f"  RESULTADOS -- Escenario: {self.config.nombre}")
        print(f"{sep}")

        # --- Resumen general -----------------------------------------------
        print(f"\n  {'CONFIGURACION':^66}")
        print(f"  {'-' * 66}")
        print(f"  Tiempo simulado:          {T} semanas")
        print(f"  Tasa de llegada:          {self.config.tasa_llegada} ninos/semana")
        print(f"  Voluntarios:              {len(self.voluntarios)}")
        print(f"  Profesionales (Eq.Prof.): {self.config.num_profesionales}")
        print(f"  Politica de matching:     "
              f"{'Generalista permitido' if self.config.permitir_generalista else 'Solo match estricto'}")

        print(f"\n  {'KPI -- DEMANDA Y ATENCION':^66}")
        print(f"  {'-' * 66}")
        print(f"  Ninos que llegaron:       {self.ninos_que_llegaron}")
        print(f"  Ninos atendidos (completo): {self.ninos_atendidos}")
        en_proceso = self.ninos_que_llegaron - self.ninos_atendidos
        print(f"  Ninos en proceso al cierre: {en_proceso}")

        # --- KPI 1: Tiempo promedio de espera en cola ----------------------
        print(f"\n  {'KPI 1 -- TIEMPO DE ESPERA EN COLA':^66}")
        print(f"  {'-' * 66}")
        if self.tiempos_espera_cola:
            prom_espera = statistics.mean(self.tiempos_espera_cola)
            max_espera = max(self.tiempos_espera_cola)
            med_espera = statistics.median(self.tiempos_espera_cola)
        else:
            prom_espera = max_espera = med_espera = 0

        print(f"  Espera promedio total:    {prom_espera:.2f} semanas")
        print(f"  Espera mediana:           {med_espera:.2f} semanas")
        print(f"  Espera maxima:            {max_espera:.2f} semanas")

        if self.tiempos_espera_profesional:
            prom_ep = statistics.mean(self.tiempos_espera_profesional)
            print(f"  -> Espera por Eq. Prof.:  {prom_ep:.2f} semanas (promedio)")
        if self.tiempos_espera_voluntario:
            prom_ev = statistics.mean(self.tiempos_espera_voluntario)
            print(f"  -> Espera por Voluntario: {prom_ev:.2f} semanas (promedio)")

        # --- KPI 2: Tasa de Mal Matching -----------------------------------
        print(f"\n  {'KPI 2 -- TASA DE MAL MATCHING':^66}")
        print(f"  {'-' * 66}")
        total_match = len(self.resultados_matching)
        if total_match > 0:
            optimos = sum(1 for r in self.resultados_matching
                          if r["tipo_match"] == "OPTIMO")
            suboptimos = sum(1 for r in self.resultados_matching
                             if r["tipo_match"] == "SUBOPTIMO")
            generalistas = sum(1 for r in self.resultados_matching
                               if r["tipo_match"] == "GENERALISTA")
            tasa_mal = ((suboptimos + generalistas) / total_match) * 100
        else:
            optimos = suboptimos = generalistas = 0
            tasa_mal = 0

        print(f"  Asignaciones totales:     {total_match}")
        if total_match > 0:
            print(f"  [OK] Match optimo:        {optimos}  "
                  f"({optimos / total_match * 100:.1f}%)")
            print(f"  [!!] Match suboptimo:     {suboptimos}  "
                  f"({suboptimos / total_match * 100:.1f}%)")
            print(f"  [XX] Match generalista:   {generalistas}  "
                  f"({generalistas / total_match * 100:.1f}%)")
        print(f"  Tasa de Mal Matching:     {tasa_mal:.1f}%")

        # --- KPI 3: Ocupación de Voluntarios -------------------------------
        print(f"\n  {'KPI 3 -- OCUPACION DE VOLUNTARIOS':^66}")
        print(f"  {'-' * 66}")
        for vol in self.voluntarios:
            pct = (vol.tiempo_ocupado_total / T) * 100 if T > 0 else 0
            barra_llena = int(pct / 5)
            barra_vacia = 20 - barra_llena
            barra = "#" * barra_llena + "." * barra_vacia
            print(f"  {vol.nombre} (Exp:{vol.expertise}, "
                  f"{NOMBRE_AREA[vol.area]:>10}): "
                  f"[{barra}] {pct:5.1f}%")

        tiempo_total_vol = sum(v.tiempo_ocupado_total for v in self.voluntarios)
        capacidad_total = len(self.voluntarios) * T
        ocupacion_global = (tiempo_total_vol / capacidad_total * 100
                            if capacidad_total > 0 else 0)
        print(f"  {'':>36}  ----------")
        print(f"  {'Ocupacion global voluntarios:':>36}  {ocupacion_global:.1f}%")

        # --- KPI 4: Ocupación del Equipo Profesional -----------------------
        print(f"\n  {'KPI 4 -- OCUPACION DEL EQUIPO PROFESIONAL':^66}")
        print(f"  {'-' * 66}")
        capacidad_prof = self.config.num_profesionales * T
        ocupacion_prof = (self.tiempo_uso_profesional / capacidad_prof * 100
                          if capacidad_prof > 0 else 0)
        print(f"  Tiempo total de evaluaciones: {self.tiempo_uso_profesional:.1f} semanas")
        print(f"  Capacidad total:              "
              f"{self.config.num_profesionales} prof x {T} sem = "
              f"{capacidad_prof:.0f} sem")
        print(f"  Ocupacion Eq. Profesional:    {ocupacion_prof:.1f}%")

        # --- Diagnóstico ---------------------------------------------------
        print(f"\n  {'DIAGNOSTICO':^66}")
        print(f"  {'-' * 66}")

        alertas = []
        if ocupacion_global > 85:
            alertas.append("  [ROJO] Voluntarios SOBRECARGADOS ({:.0f}%). "
                           "Incorporar mas voluntarios.".format(ocupacion_global))
        elif ocupacion_global > 60:
            alertas.append("  [AMARILLO] Voluntarios con carga MODERADA ({:.0f}%). "
                           "Poca holgura.".format(ocupacion_global))
        else:
            alertas.append("  [VERDE] Voluntarios con capacidad suficiente "
                           "({:.0f}%).".format(ocupacion_global))

        if ocupacion_prof > 85:
            alertas.append("  [ROJO] Equipo Profesional SATURADO ({:.0f}%). "
                           "Incorporar profesionales.".format(ocupacion_prof))
        elif ocupacion_prof > 60:
            alertas.append("  [AMARILLO] Equipo Profesional con carga MODERADA "
                           "({:.0f}%).".format(ocupacion_prof))
        else:
            alertas.append("  [VERDE] Equipo Profesional con capacidad suficiente "
                           "({:.0f}%).".format(ocupacion_prof))

        if tasa_mal > 40:
            alertas.append(f"  [ROJO] Tasa de Mal Matching ALTA ({tasa_mal:.0f}%). "
                           "Se necesitan voluntarios especializados.")
        elif tasa_mal > 20:
            alertas.append(f"  [AMARILLO] Tasa de Mal Matching MODERADA ({tasa_mal:.0f}%). "
                           "Revisar distribucion de skills.")
        else:
            alertas.append(f"  [VERDE] Tasa de Mal Matching aceptable ({tasa_mal:.0f}%).")

        if prom_espera > 4:
            alertas.append(f"  [ROJO] Espera promedio MUY ALTA ({prom_espera:.1f} sem). "
                           "El sistema no cubre la demanda.")
        elif prom_espera > 2:
            alertas.append(f"  [AMARILLO] Espera promedio MODERADA ({prom_espera:.1f} sem).")
        else:
            alertas.append(f"  [VERDE] Espera promedio aceptable ({prom_espera:.1f} sem).")

        for a in alertas:
            print(a)

        print(f"\n{sep}\n")

        # Retornar KPIs como diccionario para comparación entre escenarios
        return {
            "escenario": self.config.nombre,
            "ninos_llegaron": self.ninos_que_llegaron,
            "ninos_atendidos": self.ninos_atendidos,
            "espera_promedio": prom_espera,
            "espera_maxima": max_espera,
            "tasa_mal_matching": tasa_mal,
            "ocupacion_voluntarios": ocupacion_global,
            "ocupacion_profesional": ocupacion_prof,
        }


# ===========================================================================
#  GENERADOR DE LLEGADAS (Proceso de Poisson -- Sección 4.2)
# ===========================================================================

def generar_nino(config: ConfigEscenario) -> tuple:
    """
    Genera los atributos aleatorios de un niño basándose en las
    distribuciones de probabilidad configuradas.

    Returns:
        (dificultad, area): Tupla con los atributos asignados.
    """
    # Dificultad: muestreo según probabilidades configuradas
    r = random.random()
    acum = 0
    dificultad = Dificultad.LEVE
    for dif, prob in config.prob_dificultad.items():
        acum += prob
        if r <= acum:
            dificultad = dif
            break

    # Área: muestreo según probabilidades configuradas
    r = random.random()
    acum = 0
    area = Area.MATEMATICA
    for ar, prob in config.prob_area.items():
        acum += prob
        if r <= acum:
            area = ar
            break

    return dificultad, area


def llegada_ninos(env: simpy.Environment, centro: CentroApoyo,
                  config: ConfigEscenario):
    """
    Proceso generador de SimPy: crea la llegada continua de niños
    al centro. Los tiempos entre llegadas siguen una distribución
    exponencial (proceso de Poisson).

    Args:
        env:    Entorno de simulación.
        centro: Instancia del CentroApoyo.
        config: Configuración del escenario.
    """
    contador = 0
    while True:
        # Tiempo inter-arribo exponencial (Poisson)
        tiempo_entre_llegadas = random.expovariate(config.tasa_llegada)
        yield env.timeout(tiempo_entre_llegadas)

        contador += 1
        dificultad, area = generar_nino(config)
        nino = Nino(
            id=contador,
            nombre=f"Nino-{contador:03d}",
            dificultad=dificultad,
            area=area,
            tiempo_llegada=env.now,
        )

        # Lanzar el proceso del niño en el sistema
        env.process(centro.proceso_nino(nino))


# ===========================================================================
#  EJECUCIÓN DE UN ESCENARIO
# ===========================================================================

def ejecutar_escenario(config: ConfigEscenario) -> dict:
    """
    Configura y ejecuta un escenario completo de simulación.

    Args:
        config: Configuración del escenario.

    Returns:
        Diccionario con los KPIs resultantes.
    """
    random.seed(config.semilla)

    print("\n" + "=" * 70)
    print(f"  SIMULACION -- Escenario: {config.nombre}")
    print("=" * 70)
    print(f"\n  Configuracion:")
    print(f"    * Voluntarios:          {len(config.voluntarios_spec)}")
    print(f"    * Profesionales:        {config.num_profesionales}")
    print(f"    * Tasa de llegada:      {config.tasa_llegada} ninos/semana")
    print(f"    * Simulacion:           {config.tiempo_simulacion} semanas")
    print(f"    * Politica matching:    "
          f"{'Generalista' if config.permitir_generalista else 'Estricto'}")
    print(f"    * Semilla:              {config.semilla}")
    print(f"\n  {'LOG DE EVENTOS':^66}")
    print(f"  {'-' * 66}")

    env = simpy.Environment()
    centro = CentroApoyo(env, config)
    env.process(llegada_ninos(env, centro, config))
    env.run(until=config.tiempo_simulacion)

    return centro.reporte()


# ===========================================================================
#  COMPARATIVA DE ESCENARIOS
# ===========================================================================

def comparar_escenarios(resultados: list[dict]):
    """
    Imprime una tabla comparativa de KPIs entre todos los escenarios
    ejecutados, facilitando el análisis de sensibilidad.
    """
    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  TABLA COMPARATIVA DE ESCENARIOS")
    print(f"{sep}\n")

    # Encabezado
    header = f"  {'Metrica':<30}"
    for r in resultados:
        nombre_corto = r['escenario'][:18]
        header += f" | {nombre_corto:>18}"
    print(header)
    print(f"  {'-' * (30 + 21 * len(resultados))}")

    # Filas
    metricas = [
        ("Ninos que llegaron", "ninos_llegaron", "{:.0f}"),
        ("Ninos atendidos", "ninos_atendidos", "{:.0f}"),
        ("Espera prom. (sem)", "espera_promedio", "{:.2f}"),
        ("Espera max. (sem)", "espera_maxima", "{:.2f}"),
        ("Mal Matching (%)", "tasa_mal_matching", "{:.1f}"),
        ("Ocupacion Vol. (%)", "ocupacion_voluntarios", "{:.1f}"),
        ("Ocupacion Eq.Prof.(%)", "ocupacion_profesional", "{:.1f}"),
    ]

    for nombre_metrica, clave, fmt in metricas:
        fila = f"  {nombre_metrica:<30}"
        for r in resultados:
            valor = fmt.format(r[clave])
            fila += f" | {valor:>18}"
        print(fila)

    print(f"\n{sep}")

    # Conclusión
    print(f"\n  CONCLUSION DEL EXPERIMENTO (Seccion 4.3):")
    print(f"  {'-' * 66}")

    base = resultados[0] if resultados else None
    if base:
        if base["espera_promedio"] < 3 and base["tasa_mal_matching"] < 30:
            print("  [OK] El escenario BASE muestra tiempos de espera estables y")
            print("       tasa de mal matching aceptable. La logica de asignacion")
            print("       es VALIDA para su implementacion en la plataforma real.")
        else:
            print("  [!!] El escenario BASE muestra debilidades. Se recomienda")
            print("       ajustar la cantidad de recursos antes de implementar.")

    if len(resultados) > 2:
        crec = resultados[2]
        if crec["espera_promedio"] > base["espera_promedio"] * 2:
            print(f"\n  [ROJO] Con crecimiento del 200%, los tiempos de espera se")
            print(f"         disparan ({crec['espera_promedio']:.1f} sem). El sistema")
            print(f"         NO escala sin incorporar mas voluntarios/profesionales.")
        else:
            print(f"\n  [OK] El sistema escala razonablemente ante un crecimiento")
            print(f"       del 200% en la matricula.")

    print()


# ===========================================================================
#  FUNCIÓN PRINCIPAL
# ===========================================================================

def main():
    """
    Punto de entrada: ejecuta los 3 escenarios definidos en el anteproyecto
    y genera la tabla comparativa de KPIs.
    """
    print("\n" + "=" * 70)
    print("  MODELOS Y SIMULACION -- ASOCIACION CIVIL")
    print("  Simulacion de Eventos Discretos: Centro de Apoyo Escolar")
    print("  Universidad Catolica de Salta -- Lic. en Ciencia de Datos")
    print("=" * 70)

    escenarios = [
        ESCENARIO_BASE,
        ESCENARIO_A_DEFICIT,
        ESCENARIO_B_CRECIMIENTO,
    ]

    resultados = []
    for escenario in escenarios:
        kpis = ejecutar_escenario(escenario)
        resultados.append(kpis)

    # Tabla comparativa final
    comparar_escenarios(resultados)


# ===========================================================================
#  EJECUCIÓN
# ===========================================================================

if __name__ == "__main__":
    main()
