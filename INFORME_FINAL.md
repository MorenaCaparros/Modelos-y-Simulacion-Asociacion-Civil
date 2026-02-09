# TRABAJO FINAL – MODELOS Y SIMULACIÓN

**Universidad:** Universidad Católica de Salta  
**Carrera:** Licenciatura en Ciencia de Datos  
**Materia:** Modelos y Simulación  
**Docente:** Gustavo Ramiro Rivadera  
**Alumno:** Morena Caparros  
**Fecha:** Febrero 2026

---

## 1. Introducción

La Asociación Civil funciona como un nexo operativo entre niños con dificultades de aprendizaje y voluntarios dispuestos a brindar apoyo escolar. La operación se basa en la intervención de un Equipo Profesional que evalúa a cada niño, detecta carencias específicas (lectoescritura, matemáticas, grafismos) y diseña un plan de trabajo personalizado.

Para que la intervención sea exitosa, debe existir una correspondencia (matching) efectiva entre las necesidades del niño y las competencias del voluntario asignado. Dado que se proyecta un crecimiento exponencial en la matrícula, resulta fundamental validar la lógica de asignación y la capacidad operativa del sistema antes de su informatización definitiva.

Este trabajo presenta el desarrollo completo de la simulación propuesta en el anteproyecto, incluyendo la implementación del modelo, la validación mediante escenarios sintéticos y el análisis de resultados para fundamentar decisiones operativas.

---

## 2. Definición del Problema

Actualmente, el proceso de asignación y seguimiento se realiza de forma manual utilizando herramientas de ofimática (hojas de cálculo). Este método presenta limitaciones críticas ante el escalamiento:

- **Saturación del recurso crítico:** El Equipo Profesional actúa como un servidor único que debe validar cada asignación manualmente, generando cuellos de botella que retrasan el inicio de las intervenciones.

- **Ineficiencia en la asignación:** Debido a la falta de automatización, generalmente se prioriza la disponibilidad sobre la mejora a nivel pedagógico, asignando voluntarios sin las herramientas específicas para la dificultad del niño o con las herramientas pero sin las capacidades necesarias.

- **Incertidumbre operativa:** No existe capacidad para predecir cuántos voluntarios se necesitarán para cubrir la demanda futura, ni cómo afectará la variabilidad de la asistencia al flujo de trabajo.

El problema más importante es **la necesidad de evaluar el comportamiento del sistema bajo condiciones de carga variable** para definir reglas del sistema que sean sólidas antes de la implementación del software.

---

## 3. Marco Teórico Aplicado

Este proyecto se enmarca en la metodología de **Simulación de Eventos Discretos (DES)**. A diferencia de un sistema estático, la operación de la asociación es dinámica porque la llegada de nuevos niños y la disponibilidad de los voluntarios varían en el tiempo.

Se propone modelar matemáticamente este sistema para estudiar la interacción entre:
- **Demanda:** Niños que llegan al centro
- **Oferta:** Voluntarios disponibles
- **Recursos de control:** Equipo Profesional

El objetivo es validar las reglas de asignación automática y dimensionar la capacidad operativa necesaria para evitar el colapso del servicio.

### 3.1. Simulación de Eventos Discretos (DES)

La Simulación de Eventos Discretos es una técnica de modelado en la que el estado del sistema cambia en momentos específicos del tiempo (eventos discretos). En este caso, los eventos son:

- **Llegada** de un niño al centro
- **Inicio** de evaluación por el Equipo Profesional
- **Fin** de evaluación
- **Asignación** de voluntario
- **Fin** de intervención pedagógica

Entre eventos, el estado del sistema permanece constante. Esta característica permite avanzar el tiempo de forma eficiente sin simular cada instante.

### 3.2. Proceso de Poisson para Llegadas

La llegada de niños se modela como un **proceso de Poisson** con parámetro λ (tasa de llegada). Esto implica que:

- Los tiempos entre llegadas consecutivas siguen una distribución **Exponencial(λ)**
- Las llegadas son **independientes** entre sí
- La tasa λ representa el número promedio de niños que llegan por unidad de tiempo (semanas)

Esta es una suposición estándar en teoría de colas y permite capturar la variabilidad aleatoria de la demanda.

### 3.3. Herramientas Utilizadas

- **Python 3.9:** Lenguaje de programación base
- **SimPy 4.x:** Framework especializado para simulación de eventos discretos en Python
- **Streamlit:** Dashboard interactivo para visualización de resultados (componente opcional)
- **Pandas:** Manipulación y presentación de datos tabulares

---

## 4. Solución del Problema

Para abordar la incertidumbre operativa y validar la lógica de asignación, se desarrolló un modelo de simulación computacional estructurado en tres fases: modelado, lógica de simulación y validación.

### 4.1. Modelado del Sistema (Entidades y Estados)

Se definió un modelo conceptual que representa los componentes del sistema real y sus atributos:

#### 4.1.1. Entidades de Flujo (Niños)

Los niños son las **entidades** que atraviesan el sistema. Cada niño se modela con atributos aleatorios:

```python
# Estructura de un niño
nino = {
    "dificultad": int,  # 1=Leve, 2=Moderada, 3=Grave
    "area": str         # "matematica" | "lectura" | "grafismo"
}
```

Los atributos se generan según distribuciones de probabilidad configurables por escenario:

```python
def generar_atributos_nino(prob_dificultad, prob_area):
    """
    Genera la dificultad y el área de un niño al azar.
    prob_dificultad: [P(Leve), P(Moderada), P(Grave)]
    prob_area: [P(Matematica), P(Lectura), P(Grafismo)]
    """
    r = random.random()
    if r < prob_dificultad[0]:
        dificultad = 1  # Leve
    elif r < prob_dificultad[0] + prob_dificultad[1]:
        dificultad = 2  # Moderada
    else:
        dificultad = 3  # Grave
    
    # Similar para área...
    return dificultad, area
```

#### 4.1.2. Recursos (Voluntarios)

Los voluntarios son **recursos limitados** que pueden estar ocupados o disponibles:

```python
# Estructura de un voluntario
voluntario = {
    "nombre": str,
    "expertise": int,      # 1=Básico, 2=Intermedio, 3=Experto
    "area": str,           # Área de especialidad
    "ocupado": bool,       # Estado actual
    "tiempo_ocupado": float  # Acumulador para KPI
}
```

El sistema gestiona un pool de voluntarios definido por cada escenario.

#### 4.1.3. Servidores (Equipo Profesional)

El Equipo Profesional se modela como un **recurso SimPy** con capacidad limitada:

```python
env = simpy.Environment()
equipo_prof = simpy.Resource(env, capacity=N)  # N profesionales
```

Este recurso representa la capacidad de evaluación y actúa como **cuello de botella** si la demanda supera la capacidad.

#### 4.1.4. Colas de Espera Diferenciadas

Se implementaron colas separadas por nivel de dificultad para analizar tiempos de espera por segmento:

```python
espera_por_dificultad = {
    1: [],  # Tiempos de espera de casos Leves
    2: [],  # Tiempos de espera de casos Moderados
    3: []   # Tiempos de espera de casos Graves
}
```

Esto permite identificar si algún tipo de caso está siendo desfavorecido por el algoritmo de matching.

### 4.2. Lógica de Simulación (Motor de Eventos Discretos)

Se desarrolló un script en Python (`simulacion_apoyo_escolar.py`, 664 líneas) utilizando SimPy para recrear la dinámica temporal del sistema.

#### 4.2.1. Generación de Eventos (Llegadas)

Se programó la llegada de niños (Arrivals) siguiendo una distribución de Poisson:

```python
def llegada_ninos(env, equipo_prof, voluntarios, config):
    """Genera niños que llegan al centro siguiendo un proceso de Poisson."""
    contador = 0
    while True:
        # Tiempo entre llegadas ~ Exponencial(λ)
        yield env.timeout(random.expovariate(config["tasa_llegada"]))
        contador += 1
        
        # Generar atributos del niño
        dificultad, area = generar_atributos_nino(
            config["prob_dificultad"], 
            config["prob_area"]
        )
        
        # Crear proceso del niño
        env.process(proceso_nino(
            env, f"Nino-{contador:03d}", dificultad, area,
            equipo_prof, voluntarios, config
        ))
```

#### 4.2.2. Algoritmo de Matching Simulado

Se implementó la lógica de decisión que el software final deberá ejecutar.

**Regla principal:** `expertise_voluntario >= dificultad_niño AND área_coincide`

```python
def buscar_voluntario(voluntarios, dificultad_nino, area_nino, permitir_generalista):
    """
    Regla: expertise_voluntario >= dificultad_nino AND area coincide
    
    Prioridad:
    1. Match óptimo (área + expertise suficiente)
    2. Subóptimo (área correcta, expertise insuficiente) [solo si generalista=True]
    3. Generalista (cualquier área) [solo si generalista=True]
    """
    # Buscar match óptimo
    for v in disponibles:
        if v["area"] == area_nino and v["expertise"] >= dificultad_nino:
            return v, "OPTIMO"
    
    # Si no hay match y se permite generalista
    if permitir_generalista:
        # Buscar subóptimo (área correcta)
        for v in disponibles:
            if v["area"] == area_nino:
                return v, "SUBOPTIMO"
        # Cualquier voluntario
        return disponibles[0], "GENERALISTA"
    
    return None, None  # El niño espera o se va
```

**Política Estricta (comparación):**  
Si `permitir_generalista=False`, el niño espera hasta 6 semanas. Si no encuentra match, se va sin atención. Esto permite evaluar el trade-off entre **cobertura** (atender a todos) vs **calidad** (solo matches óptimos).

#### 4.2.3. Proceso Completo de un Niño

El recorrido de cada niño se modela como un proceso SimPy con 5 fases:

```python
def proceso_nino(env, nombre, dificultad, area, equipo_prof, voluntarios, config):
    """
    Simula el recorrido completo:
    1. Llegada (registrada)
    2. Evaluación por Equipo Profesional
    3. Búsqueda de voluntario
    4. Intervención pedagógica
    5. Liberación del voluntario
    """
    t_inicio = env.now
    
    # FASE 1: Evaluación por Equipo Profesional
    t_pre_prof = env.now
    with equipo_prof.request() as turno:
        yield turno  # Espera hasta que haya un profesional libre
        
        espera_prof = env.now - t_pre_prof
        tiempos_espera_prof.append(espera_prof)  # KPI
        
        # Duración de evaluación ~ Normal(μ=1.5, σ=0.5)
        duracion_eval = max(0.5, random.gauss(1.5, 0.5))
        yield env.timeout(duracion_eval)
    
    # FASE 2: Búsqueda de voluntario
    t_pre_vol = env.now
    vol_asignado = None
    
    while vol_asignado is None:
        vol_asignado, tipo_match = buscar_voluntario(...)
        
        if vol_asignado is None:
            # Si política estricta: timeout
            if (env.now - t_pre_vol) >= config.get("max_espera_vol", 8):
                ninos_no_atendidos += 1
                return  # Se va sin atención
            
            yield env.timeout(0.25)  # Espera y reintenta
    
    espera_vol = env.now - t_pre_vol
    tiempos_espera_vol.append(espera_vol)  # KPI
    vol_asignado["ocupado"] = True
    resultados_match.append(tipo_match)  # KPI
    
    # FASE 3: Intervención pedagógica
    # Duración ~ Normal(μ=6, σ=2)
    duracion = max(2.0, random.gauss(6.0, 2.0))
    yield env.timeout(duracion)
    
    # FASE 4: Liberación
    vol_asignado["tiempo_ocupado"] += duracion
    vol_asignado["ocupado"] = False
    ninos_atendidos += 1
```

#### 4.2.4. Reloj de Simulación

El sistema avanza en el tiempo virtual (semanas) registrando el estado de cada entidad. La simulación corre por **52 semanas** (1 año) para cada escenario:

```python
env = simpy.Environment()
env.process(llegada_ninos(...))
env.run(until=52)  # Simula 52 semanas
```

#### 4.2.5. Estructura del Código Fuente

El archivo principal (`simulacion_apoyo_escolar.py`, ~664 líneas) expone además una función para uso externo desde el dashboard:

```python
def correr_simulacion(config, silencioso=False):
    """
    Corre un escenario y devuelve dict con todos los KPIs.
    Si silencioso=True, no imprime nada (para dashboard).
    """
    resetear_estadisticas()
    random.seed(config["semilla"])
    
    env = simpy.Environment()
    equipo_prof = simpy.Resource(env, capacity=config["num_profesionales"])
    voluntarios = [...]
    
    if silencioso:
        import io, sys
        sys.stdout = io.StringIO()
    
    env.process(llegada_ninos(env, equipo_prof, voluntarios, config))
    env.run(until=config["tiempo_simulacion"])
    
    return {
        "espera_prom": statistics.mean(tiempos_espera),
        "mal_matching": (suboptimos + generalistas) / total * 100,
        # ... más métricas
    }
```

#### 4.2.6. Dashboard Interactivo (Componente Opcional)

Se desarrolló un dashboard con **Streamlit** (`app.py`, ~379 líneas) que permite:

- Seleccionar escenarios predefinidos o crear uno personalizado
- Visualizar KPIs con tarjetas métricas estilizadas
- Gráficos de barras para distribución de matching
- Ocupación individual de cada voluntario
- Semáforos visuales con diagnóstico automático

**Características técnicas:**
- Iconografía con Material Symbols Rounded (Google Fonts)
- Paleta de colores de Google (#4285f4 azul, #f9ab00 amarillo, #1e8e3e verde)
- Ejecución local en `http://localhost:8501`

```bash
streamlit run app.py
```

> **Aclaración:** El dashboard NO forma parte del contenido evaluable. Es solo una herramienta visual para explorar resultados sin modificar código.

### 4.3. Validación mediante Escenarios Sintéticos

#### 4.3.1. Diseño de Escenarios

Se diseñaron **5 escenarios** para probar el sistema bajo diferentes condiciones:

| Escenario | Tasa llegada | Voluntarios | Profesionales | Distribución dificultad | Objetivo |
|-----------|--------------|-------------|---------------|-------------------------|----------|
| **Base** | 3 niños/sem | 8 (mix) | 2 | 50% leve, 35% mod, 15% grave | Operación normal |
| **A - Déficit** | 5 niños/sem | 4 (básicos) | 1 | 15% leve, 30% mod, 55% grave | Estrés por demanda alta y recursos bajos |
| **B - Crecimiento** | 9 niños/sem | 8 (mix) | 2 | 50% leve, 35% mod, 15% grave | Crecimiento 200% sin aumentar recursos |
| **C - Reforzado** | 1 niño/sem | 12 (expertos) | 4 | 55% leve, 30% mod, 15% grave | Recursos óptimos, baja demanda |
| **D - Demanda baja** | 1 niño/sem | 8 (mix) | 3 | 70% leve, 25% mod, 5% grave | Casos mayormente leves |

Además, se compararon **dos políticas de asignación**:
- **Generalista** (flexible): Si no hay match óptimo, se asigna cualquier voluntario
- **Estricta**: El niño espera hasta 6 semanas o se va sin atención

#### 4.3.2. Métricas Clave (KPIs)

El modelo registra 4 indicadores principales:

1. **Tiempo de espera en cola** (promedio y máximo)
   - Desglosado por: espera profesional, espera voluntario, espera por dificultad

2. **Tasa de mal matching** (%)
   - % de asignaciones subóptimas o generalistas

3. **Ocupación de voluntarios** (%)
   - Por voluntario individual y promedio global

4. **Ocupación del Equipo Profesional** (%)
   - Identifica si es cuello de botella

#### 4.3.3. Resultados de la Simulación

Simulación de **52 semanas** con semilla aleatoria 42:

| Métrica | Base | A-Déficit | B-Crecimiento | C-Reforzado | D-Demanda baja |
|---------|------|-----------|---------------|-------------|----------------|
| Niños llegaron | 155 | 260 | 455 | 58 | 53 |
| Niños atendidos | 56 | 30 | 57 | 50 | 45 |
| Sin atención | 0 | 0 | 0 | 0 | 0 |
| **Espera prom (sem)** | **13.18** | **21.64** | **20.56** | **1.68** | **2.30** |
| Espera máx (sem) | 25.55 | 40.69 | 39.53 | 3.33 | 6.88 |
| **Mal matching (%)** | **59.4** | **79.4** | **60.0** | **17.5** | **55.8** |
| Ocup. voluntarios (%) | 80.4 | 79.0 | 78.6 | 46.4 | 64.7 |
| **Ocup. Eq.Prof (%)** | **101.1** | **102.0** | **102.7** | **45.2** | **49.5** |

#### 4.3.4. Análisis por Escenario

**Escenario Base (Normal)**
- ✅ Voluntarios operan al 80% (saludable)
- ❌ Equipo Profesional **saturado** al 101% (cuello de botella)
- ❌ Mal matching del 59.4% (necesidad de más voluntarios E3)
- ❌ Espera promedio de 13.2 semanas (inaceptable)

**Diagnóstico:** El sistema base NO es viable. La saturación del Equipo Profesional genera retrasos masivos.

**Escenario A - Déficit**
- ❌ Peor escenario: espera de 21.6 semanas
- ❌ Mal matching del 79.4% (voluntarios básicos no cubren casos graves)
- ❌ Solo 30 de 260 niños atendidos en el año

**Diagnóstico:** Con alta demanda de casos graves y recursos limitados, el sistema colapsa.

**Escenario B - Crecimiento**
- ❌ Con 200% más matrícula, espera sube a 20.6 semanas
- ❌ Solo 57 de 455 niños atendidos (87% en cola)
- ✅ Mal matching similar a Base (60%)

**Diagnóstico:** El sistema **NO escala**. Se requiere aumentar profesionales proporcionalmente.

**Escenario C - Reforzado** ✅
- ✅ Espera promedio de 1.68 semanas (excelente)
- ✅ Mal matching del 17.5% (bajo)
- ✅ Equipo Profesional al 45% (sin saturación)
- ✅ 50 de 58 niños atendidos (86%)

**Diagnóstico:** Con **12 voluntarios expertos** y **4 profesionales**, el sistema funciona óptimamente.

**Escenario D - Demanda Baja**
- ✅ Espera de 2.3 semanas (aceptable)
- ⚠️ Mal matching del 55.8% (alto pese a baja demanda)
- ✅ Equipo Profesional al 49.5%

**Diagnóstico:** Revela que VOLUNTARIOS_BASE carece de expertise E3 en grafismo. Incluso con poca demanda, 56% de asignaciones son subóptimas.

#### 4.3.5. Comparación de Políticas

| Métrica | Base (Generalista) | Base (Estricta) |
|---------|-------------------|-----------------|
| Niños atendidos | 56 | 48 |
| Sin atención | 0 | 10 |
| Espera prom | 13.18 sem | 12.10 sem |
| **Mal matching** | **59.4%** | **0.0%** |
| Ocup. voluntarios | 80.4% | 67.3% |

**Conclusión:** La política estricta elimina el mal matching, pero **10 niños se van sin atención** tras esperar 6 semanas. Trade-off entre calidad y cobertura.

#### 4.3.6. Espera por Nivel de Dificultad (Escenario Base)

| Dificultad | Niños | Espera prom (sem) |
|------------|-------|-------------------|
| Leve | 30 | 9.2 |
| Moderada | 18 | 16.8 |
| Grave | 8 | 22.5 |

**Interpretación:** Los casos graves esperan 2.4x más que los leves. El algoritmo de matching favorece inadvertidamente casos simples (hay más voluntarios E1/E2).

#### 4.3.7. Verificación Lógica del Modelo

✅ **Test 1 - Matching óptimo:** Con 12 voluntarios E3 y demanda baja, mal matching bajó a 17.5%  
✅ **Test 2 - Cuello de botella:** Al reducir profesionales a 1, ocupación subió a 102%  
✅ **Test 3 - Escalabilidad:** Al triplicar tasa de llegada, espera subió 56%  
✅ **Test 4 - Política estricta:** Sin generalista, 10 niños se fueron (comportamiento esperado)

Se probó además cambiar la semilla aleatoria (42 → 999):
- Variación en espera promedio: ±8%
- Variación en mal matching: ±5%
- **Conclusión:** Los resultados son consistentes y el modelo no depende de una semilla particular.

---

## 5. Conclusiones

### 5.1. Respuestas a las Preguntas de Investigación

**¿El sistema actual puede escalar?**  
❌ **NO.** El Escenario B demostró que con 200% más matrícula y los mismos recursos, la espera sube a 20.6 semanas y solo se atiende al 12.5% de los niños.

**¿El Equipo Profesional es un cuello de botella?**  
✅ **SÍ.** En los escenarios Base, A y B, la ocupación supera el 100%. Es el recurso crítico que limita el throughput del sistema.

**¿La lógica de matching es eficiente?**  
⚠️ **PARCIALMENTE.** Funciona bien con recursos adecuados (Escenario C: 17.5% mal matching), pero con VOLUNTARIOS_BASE alcanza 60% de asignaciones subóptimas.

**¿Se debe permitir asignación generalista?**  
✅ **SÍ, pero con límites.** La política estricta deja 10 niños sin atención. Una solución intermedia sería: permitir generalista solo para casos Leves, y espera para Graves.

### 5.2. Recomendaciones Operativas

1. **Aumentar Equipo Profesional:**  
   Pasar de 2 a **4 profesionales** para reducir ocupación del 101% al 45%.

2. **Reclutar Voluntarios E3:**  
   La configuración óptima es **12 voluntarios** con al menos **50% en expertise 3** y cobertura balanceada en las 3 áreas.

3. **Implementar Priorización:**  
   Casos Graves deben tener prioridad en la asignación para reducir su espera (actualmente 2.4x mayor que Leves).

4. **Política de Matching Híbrida:**  
   ```
   IF dificultad == GRAVE:
       esperar match óptimo (max 4 semanas)
   ELSE:
       permitir generalista si espera > 2 semanas
   ```

5. **Monitoreo en Producción:**  
   Implementar dashboard en tiempo real para detectar saturación temprana.

### 5.3. Validación de la Lógica para Software

✅ **El algoritmo de matching es válido** para implementar en la plataforma, CON las modificaciones recomendadas.

✅ **El dimensionamiento de recursos es crítico:** No basta con programar bien el matching; se necesitan 4 profesionales y 12 voluntarios E3 para operación estable.

✅ **La simulación cumplió su objetivo:** Identificó problemas que habrían colapsado el sistema en producción.

### 5.4. Lecciones Aprendidas

- **SimPy es potente pero requiere diseño cuidadoso:** Las colas implícitas y el manejo de recursos necesitan planificación.
- **Datos sintéticos bien diseñados son clave:** Los 5 escenarios cubrieron desde operación normal hasta colapso.
- **La visualización ayuda a comunicar resultados:** El dashboard Streamlit facilitó explicar trade-offs a stakeholders no técnicos.

### 5.5. Bibliografía

- **SimPy Documentation** (https://simpy.readthedocs.io/): Framework de simulación de eventos discretos en Python.
- **Banks, J. et al. (2005).** *Discrete-Event System Simulation*. Prentice Hall.
- **Law, A. M. (2014).** *Simulation Modeling and Analysis*. McGraw-Hill.
- **Material de la cátedra:** Apuntes y presentaciones del Prof. Gustavo Rivadera.

### 5.6. Anexos

#### Anexo A - Configuración de Escenarios

```python
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
```

#### Anexo B - Repositorio del Código

**GitHub:** `https://github.com/MorenaCaparros/Modelos-y-Simulacion-Asociacion-Civil`

Archivos principales:
- `simulacion_apoyo_escolar.py` (664 líneas) - Simulación principal
- `app.py` (379 líneas) - Dashboard Streamlit (opcional)
- `README.md` - Documentación del proyecto
- `requirements.txt` - Dependencias

#### Anexo C - Capturas de Pantalla

**[AGREGAR AQUÍ CAPTURAS DEL DASHBOARD STREAMLIT]**

1. Vista general del dashboard con escenarios predefinidos
2. Tabla comparativa de KPIs
3. Gráfico de ocupación de voluntarios
4. Panel de diagnóstico con semáforos

---

**FIN DEL INFORME**
