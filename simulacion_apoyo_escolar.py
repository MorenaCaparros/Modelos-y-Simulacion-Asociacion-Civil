"""
Modelos y Simulacion - Trabajo Practico
Simulacion de Eventos Discretos: Centro de Apoyo Escolar

Universidad Catolica de Salta - Lic. en Ciencia de Datos
Materia: Modelos y Simulacion
Docente: Gustavo Ramiro Rivadera
Alumno:  Morena Caparros
Fecha:   2026

Se simula el sistema de una Asociacion Civil que asigna voluntarios
a niños con dificultades de aprendizaje. Un Equipo Profesional evalua
a cada niño y luego se busca un voluntario adecuado (matching).

Se prueban 3 escenarios + comparacion de politicas:
  - Base: operacion normal
  - A: deficit de recursos (muchos niños graves, pocos voluntarios)
  - B: crecimiento del 200% en la matricula
  - Comparacion: generalista vs espera estricta (sin generalista)
"""

import simpy
import random
import statistics


# -- Variables globales para acumular estadisticas --

tiempos_espera = []          # espera total de cada niño (eval + voluntario)
tiempos_espera_prof = []     # espera solo por el equipo profesional
tiempos_espera_vol = []      # espera solo por un voluntario
resultados_match = []        # tipo de match de cada asignacion
tiempo_uso_prof = 0          # tiempo acumulado usando el eq. profesional
ninos_llegaron = 0
ninos_atendidos = 0
ninos_no_atendidos = 0       # los que se fueron sin voluntario (politica estricta)

# Colas diferenciadas por dificultad (para el reporte)
espera_por_dificultad = {1: [], 2: [], 3: []}


def resetear_estadisticas():
    """Limpia las estadisticas para un nuevo escenario."""
    global tiempos_espera, tiempos_espera_prof, tiempos_espera_vol
    global resultados_match, tiempo_uso_prof
    global ninos_llegaron, ninos_atendidos, ninos_no_atendidos
    global espera_por_dificultad
    tiempos_espera = []
    tiempos_espera_prof = []
    tiempos_espera_vol = []
    resultados_match = []
    tiempo_uso_prof = 0
    ninos_llegaron = 0
    ninos_atendidos = 0
    ninos_no_atendidos = 0
    espera_por_dificultad = {1: [], 2: [], 3: []}


# -- Funciones auxiliares --

def generar_atributos_nino(prob_dificultad, prob_area):
    """
    Genera la dificultad y el area de un niño al azar,
    segun las probabilidades del escenario.
    Dificultad: 1=Leve, 2=Moderada, 3=Grave
    Area: 'matematica', 'lectura', 'grafismo'
    """
    # Dificultad
    r = random.random()
    if r < prob_dificultad[0]:
        dificultad = 1  # Leve
    elif r < prob_dificultad[0] + prob_dificultad[1]:
        dificultad = 2  # Moderada
    else:
        dificultad = 3  # Grave

    # Area
    r = random.random()
    if r < prob_area[0]:
        area = "matematica"
    elif r < prob_area[0] + prob_area[1]:
        area = "lectura"
    else:
        area = "grafismo"

    return dificultad, area


def nombre_dificultad(d):
    return {1: "Leve", 2: "Moderada", 3: "Grave"}[d]


def buscar_voluntario(voluntarios, dificultad_nino, area_nino, permitir_generalista):
    """
    Busca un voluntario disponible para el niño.
    Regla: el expertise del voluntario tiene que ser >= la dificultad,
    y tiene que coincidir el area.

    Si no hay match exacto y se permite generalista, se asigna
    cualquier voluntario libre (aunque no sea el ideal).

    Devuelve (voluntario, tipo_match) o (None, None) si no hay.
    """
    disponibles = [v for v in voluntarios if not v["ocupado"]]
    if not disponibles:
        return None, None

    # Buscar match optimo: misma area + expertise suficiente
    for v in disponibles:
        if v["area"] == area_nino and v["expertise"] >= dificultad_nino:
            return v, "OPTIMO"

    if permitir_generalista:
        # Misma area pero expertise insuficiente
        for v in disponibles:
            if v["area"] == area_nino:
                return v, "SUBOPTIMO"
        # Cualquier voluntario libre
        return disponibles[0], "GENERALISTA"

    return None, None


# -- Proceso principal: el niño pasa por el sistema --

def proceso_nino(env, nombre, dificultad, area, equipo_prof, voluntarios,
                 config):
    """
    Simula todo el recorrido de un niño:
    1. Espera a ser evaluado por el Equipo Profesional
    2. Se le busca un voluntario (matching)
    3. Recibe la intervencion pedagogica
    4. El voluntario queda libre

    Si la politica es estricta (permitir_generalista=False) y no hay
    match exacto, el niño espera un maximo de semanas antes de irse.
    """
    global tiempo_uso_prof, ninos_llegaron, ninos_atendidos, ninos_no_atendidos
    ninos_llegaron += 1
    t_inicio = env.now
    max_espera_vol = config.get("max_espera_vol", 8)  # semanas maximo buscando

    print(f"  [{env.now:5.1f} sem] {nombre} llega - "
          f"Dificultad: {nombre_dificultad(dificultad)}, Area: {area}")

    # Fase 1: Evaluacion por el Equipo Profesional
    t_pre = env.now
    with equipo_prof.request() as turno:
        yield turno

        espera_prof = env.now - t_pre
        tiempos_espera_prof.append(espera_prof)

        if espera_prof > 0.1:
            print(f"  [{env.now:5.1f} sem]   {nombre} espero "
                  f"{espera_prof:.1f} sem por Eq. Profesional")

        # La evaluacion dura un tiempo (distribucion normal)
        duracion_eval = max(0.5, random.gauss(1.5, 0.5))
        tiempo_uso_prof += duracion_eval
        yield env.timeout(duracion_eval)

    # Fase 2: Buscar voluntario (cola diferenciada por dificultad)
    t_pre = env.now
    vol_asignado = None
    tipo_match = None

    while vol_asignado is None:
        vol_asignado, tipo_match = buscar_voluntario(
            voluntarios, dificultad, area, config["permitir_generalista"]
        )
        if vol_asignado is None:
            # Si ya espero demasiado, se va sin atencion
            if (env.now - t_pre) >= max_espera_vol:
                ninos_no_atendidos += 1
                espera_por_dificultad[dificultad].append(env.now - t_pre)
                print(f"  [{env.now:5.1f} sem] {nombre} se fue sin voluntario "
                      f"(espero {env.now - t_pre:.1f} sem)")
                return
            yield env.timeout(0.25)  # espera y reintenta

    espera_vol = env.now - t_pre
    tiempos_espera_vol.append(espera_vol)
    espera_por_dificultad[dificultad].append(espera_vol)
    vol_asignado["ocupado"] = True
    resultados_match.append(tipo_match)

    etiqueta = {"OPTIMO": "[OK]", "SUBOPTIMO": "[!!]", "GENERALISTA": "[XX]"}
    print(f"  [{env.now:5.1f} sem] {etiqueta[tipo_match]} {nombre} -> "
          f"{vol_asignado['nombre']} (Exp:{vol_asignado['expertise']}, "
          f"{vol_asignado['area']}) [{tipo_match}]")

    # Fase 3: Intervencion pedagogica
    duracion = max(2.0, random.gauss(6.0, 2.0))
    yield env.timeout(duracion)

    # Liberar voluntario
    vol_asignado["tiempo_ocupado"] += duracion
    vol_asignado["ocupado"] = False
    ninos_atendidos += 1

    # Guardar espera total (sin contar la intervencion)
    espera_total = (env.now - t_inicio) - duracion
    tiempos_espera.append(espera_total)

    print(f"  [{env.now:5.1f} sem] {nombre} termino ({duracion:.1f} sem). "
          f"{vol_asignado['nombre']} libre.")


# -- Generador de llegadas (Poisson) --

def llegada_ninos(env, equipo_prof, voluntarios, config):
    """Genera niños que llegan al centro siguiendo un proceso de Poisson."""
    contador = 0
    while True:
        yield env.timeout(random.expovariate(config["tasa_llegada"]))
        contador += 1

        dificultad, area = generar_atributos_nino(
            config["prob_dificultad"], config["prob_area"]
        )
        env.process(proceso_nino(
            env, f"Nino-{contador:03d}", dificultad, area,
            equipo_prof, voluntarios, config
        ))


# -- Reporte de resultados --

def imprimir_reporte(config, voluntarios):
    """Imprime los KPIs del escenario."""
    T = config["tiempo_simulacion"]

    print(f"\n  RESULTADOS - {config['nombre']}")
    print(f"  {'-' * 50}")
    print(f"  Simulacion: {T} semanas | "
          f"Llegada: {config['tasa_llegada']} niños/sem")
    print(f"  Voluntarios: {len(voluntarios)} | "
          f"Profesionales: {config['num_profesionales']}")

    print(f"\n  Niños que llegaron:   {ninos_llegaron}")
    print(f"  Niños atendidos:      {ninos_atendidos}")
    print(f"  Se fueron sin atencion: {ninos_no_atendidos}")
    print(f"  En proceso al cierre: {ninos_llegaron - ninos_atendidos - ninos_no_atendidos}")

    # KPI 1: Espera en cola
    if tiempos_espera:
        prom = statistics.mean(tiempos_espera)
        maxi = max(tiempos_espera)
    else:
        prom = maxi = 0

    print(f"\n  KPI 1 - Tiempo de espera en cola")
    print(f"    Promedio: {prom:.2f} sem | Maximo: {maxi:.2f} sem")
    if tiempos_espera_prof:
        print(f"    (por Eq. Prof: {statistics.mean(tiempos_espera_prof):.2f} sem)")
    if tiempos_espera_vol:
        print(f"    (por Voluntario: {statistics.mean(tiempos_espera_vol):.2f} sem)")

    # Cola diferenciada por dificultad (seccion 4.1 del anteproyecto)
    print(f"\n    Espera por nivel de dificultad (cola para voluntario):")
    for d in [1, 2, 3]:
        lista = espera_por_dificultad[d]
        if lista:
            prom_d = statistics.mean(lista)
            print(f"      {nombre_dificultad(d):>8}: {prom_d:.2f} sem prom "
                  f"({len(lista)} niños)")
        else:
            print(f"      {nombre_dificultad(d):>8}: sin datos")

    # KPI 2: Tasa de mal matching
    total = len(resultados_match)
    if total > 0:
        optimos = resultados_match.count("OPTIMO")
        suboptimos = resultados_match.count("SUBOPTIMO")
        generalistas = resultados_match.count("GENERALISTA")
        tasa_mal = ((suboptimos + generalistas) / total) * 100
    else:
        optimos = suboptimos = generalistas = 0
        tasa_mal = 0

    print(f"\n  KPI 2 - Tasa de mal matching")
    print(f"    Optimo: {optimos}/{total} | Suboptimo: {suboptimos}/{total} | "
          f"Generalista: {generalistas}/{total}")
    print(f"    Tasa de mal matching: {tasa_mal:.1f}%")

    # KPI 3: Ocupacion de voluntarios
    print(f"\n  KPI 3 - Ocupacion de voluntarios")
    for v in voluntarios:
        pct = (v["tiempo_ocupado"] / T) * 100 if T > 0 else 0
        barra = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(f"    {v['nombre']} (Exp:{v['expertise']}, {v['area']:>10}): "
              f"[{barra}] {pct:.1f}%")

    total_vol = sum(v["tiempo_ocupado"] for v in voluntarios)
    ocup_vol = (total_vol / (len(voluntarios) * T)) * 100 if T > 0 else 0
    print(f"    Ocupacion global: {ocup_vol:.1f}%")

    # KPI 4: Ocupacion equipo profesional
    cap_prof = config["num_profesionales"] * T
    ocup_prof = (tiempo_uso_prof / cap_prof) * 100 if cap_prof > 0 else 0
    print(f"\n  KPI 4 - Ocupacion del Equipo Profesional")
    print(f"    Uso: {tiempo_uso_prof:.1f} sem / {cap_prof:.0f} sem = {ocup_prof:.1f}%")

    # Diagnostico
    print(f"\n  Diagnostico:")
    if ocup_prof > 85:
        print(f"    [!] Eq. Profesional SATURADO ({ocup_prof:.0f}%)")
    else:
        print(f"    [ok] Eq. Profesional con capacidad ({ocup_prof:.0f}%)")
    if tasa_mal > 40:
        print(f"    [!] Mal matching ALTO ({tasa_mal:.0f}%)")
    elif tasa_mal > 20:
        print(f"    [~] Mal matching moderado ({tasa_mal:.0f}%)")
    else:
        print(f"    [ok] Mal matching aceptable ({tasa_mal:.0f}%)")
    if prom > 4:
        print(f"    [!] Espera MUY ALTA ({prom:.1f} sem)")
    else:
        print(f"    [ok] Espera aceptable ({prom:.1f} sem)")

    return {
        "nombre": config["nombre"],
        "llegaron": ninos_llegaron,
        "atendidos": ninos_atendidos,
        "no_atendidos": ninos_no_atendidos,
        "espera_prom": prom,
        "espera_max": maxi,
        "mal_matching": tasa_mal,
        "ocup_vol": ocup_vol,
        "ocup_prof": ocup_prof,
    }


# -- Ejecutar un escenario --

def ejecutar_escenario(config):
    """Prepara el entorno, corre la simulacion e imprime resultados."""
    resetear_estadisticas()
    random.seed(config["semilla"])

    print(f"\n  {'=' * 55}")
    print(f"  ESCENARIO: {config['nombre']}")
    print(f"  {'=' * 55}")

    env = simpy.Environment()
    equipo_prof = simpy.Resource(env, capacity=config["num_profesionales"])

    # Crear voluntarios como diccionarios simples
    voluntarios = []
    for v in config["voluntarios_spec"]:
        voluntarios.append({
            "nombre": v["nombre"],
            "expertise": v["expertise"],
            "area": v["area"],
            "ocupado": False,
            "tiempo_ocupado": 0,
        })

    env.process(llegada_ninos(env, equipo_prof, voluntarios, config))
    env.run(until=config["tiempo_simulacion"])

    return imprimir_reporte(config, voluntarios)


# -- Tabla comparativa --

def tabla_comparativa(resultados):
    """Muestra los KPIs de todos los escenarios lado a lado."""
    print(f"\n  {'=' * 55}")
    print(f"  COMPARATIVA DE ESCENARIOS")
    print(f"  {'=' * 55}\n")

    # Encabezado
    header = f"  {'Metrica':<25}"
    for r in resultados:
        header += f" | {r['nombre'][:15]:>15}"
    print(header)
    print(f"  {'-' * (25 + 18 * len(resultados))}")

    filas = [
        ("Niños llegaron", "llegaron", "{:.0f}"),
        ("Niños atendidos", "atendidos", "{:.0f}"),
        ("Sin atencion", "no_atendidos", "{:.0f}"),
        ("Espera prom (sem)", "espera_prom", "{:.2f}"),
        ("Espera max (sem)", "espera_max", "{:.2f}"),
        ("Mal matching (%)", "mal_matching", "{:.1f}"),
        ("Ocup. voluntarios (%)", "ocup_vol", "{:.1f}"),
        ("Ocup. Eq.Prof (%)", "ocup_prof", "{:.1f}"),
    ]
    for nombre_fila, clave, fmt in filas:
        linea = f"  {nombre_fila:<25}"
        for r in resultados:
            linea += f" | {fmt.format(r[clave]):>15}"
        print(linea)

    # Conclusion
    base = resultados[0]
    print(f"\n  Conclusion:")
    if base["espera_prom"] < 3 and base["mal_matching"] < 30:
        print("  -> El sistema BASE funciona bien. La logica de asignacion")
        print("     se puede implementar en la plataforma.")
    else:
        print("  -> El sistema BASE tiene problemas. Hay que ajustar")
        print("     los recursos antes de implementar.")

    if len(resultados) > 2:
        crec = resultados[2]
        if crec["espera_prom"] > base["espera_prom"] * 1.5:
            print(f"  -> Con crecimiento 200%, la espera sube a "
                  f"{crec['espera_prom']:.1f} sem. No escala.")
        else:
            print(f"  -> El sistema escala razonablemente.")
    print()


# -- Definicion de escenarios --

VOLUNTARIOS_BASE = [
    {"nombre": "Vol-01", "expertise": 3, "area": "matematica"},
    {"nombre": "Vol-02", "expertise": 2, "area": "matematica"},
    {"nombre": "Vol-03", "expertise": 3, "area": "lectura"},
    {"nombre": "Vol-04", "expertise": 2, "area": "lectura"},
    {"nombre": "Vol-05", "expertise": 1, "area": "lectura"},
    {"nombre": "Vol-06", "expertise": 2, "area": "grafismo"},
    {"nombre": "Vol-07", "expertise": 1, "area": "grafismo"},
    {"nombre": "Vol-08", "expertise": 1, "area": "matematica"},
]

ESCENARIO_BASE = {
    "nombre": "Base (Normal)",
    "tiempo_simulacion": 52,
    "semilla": 42,
    "tasa_llegada": 3.0,
    "prob_dificultad": [0.50, 0.35, 0.15],  # Leve, Moderada, Grave
    "prob_area": [0.45, 0.35, 0.20],        # Mate, Lectura, Grafismo
    "voluntarios_spec": VOLUNTARIOS_BASE,
    "num_profesionales": 2,
    "permitir_generalista": True,
}

ESCENARIO_A = {
    "nombre": "A - Deficit",
    "tiempo_simulacion": 52,
    "semilla": 42,
    "tasa_llegada": 5.0,                    # mas demanda
    "prob_dificultad": [0.15, 0.30, 0.55],  # mayoria graves
    "prob_area": [0.45, 0.35, 0.20],
    "voluntarios_spec": [                   # pocos y basicos
        {"nombre": "Vol-01", "expertise": 1, "area": "matematica"},
        {"nombre": "Vol-02", "expertise": 1, "area": "lectura"},
        {"nombre": "Vol-03", "expertise": 2, "area": "grafismo"},
        {"nombre": "Vol-04", "expertise": 1, "area": "matematica"},
    ],
    "num_profesionales": 1,
    "permitir_generalista": True,
}

ESCENARIO_B = {
    "nombre": "B - Crecimiento",
    "tiempo_simulacion": 52,
    "semilla": 42,
    "tasa_llegada": 9.0,                    # triple de llegadas
    "prob_dificultad": [0.50, 0.35, 0.15],
    "prob_area": [0.45, 0.35, 0.20],
    "voluntarios_spec": VOLUNTARIOS_BASE,   # mismos recursos
    "num_profesionales": 2,
    "permitir_generalista": True,
}

# Escenario extra: Base con politica estricta (sin generalista)
# Seccion 4.2 del anteproyecto: comparar ambas politicas de asignacion
ESCENARIO_BASE_ESTRICTO = {
    "nombre": "Base (Estricto)",
    "tiempo_simulacion": 52,
    "semilla": 42,
    "tasa_llegada": 3.0,
    "prob_dificultad": [0.50, 0.35, 0.15],
    "prob_area": [0.45, 0.35, 0.20],
    "voluntarios_spec": VOLUNTARIOS_BASE,
    "num_profesionales": 2,
    "permitir_generalista": False,          # sin generalista: el niño espera o se va
    "max_espera_vol": 6,                    # maximo 6 semanas buscando
}


# -- Main --

def main():
    print("\n  MODELOS Y SIMULACION - ASOCIACION CIVIL")
    print("  Centro de Apoyo Escolar")
    print("  Universidad Catolica de Salta\n")

    # Parte 1: Los 3 escenarios del anteproyecto (todos con generalista)
    resultados_escenarios = []
    for escenario in [ESCENARIO_BASE, ESCENARIO_A, ESCENARIO_B]:
        kpis = ejecutar_escenario(escenario)
        resultados_escenarios.append(kpis)

    tabla_comparativa(resultados_escenarios)

    # Parte 2: Comparacion de politicas (generalista vs estricto)
    print(f"\n  {'=' * 55}")
    print(f"  COMPARACION DE POLITICAS DE ASIGNACION")
    print(f"  (Seccion 4.2 - Generalista vs Espera Estricta)")
    print(f"  {'=' * 55}")

    kpis_estricto = ejecutar_escenario(ESCENARIO_BASE_ESTRICTO)
    tabla_comparativa([resultados_escenarios[0], kpis_estricto])


if __name__ == "__main__":
    main()
