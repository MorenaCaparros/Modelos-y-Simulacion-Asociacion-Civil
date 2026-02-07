# Modelos-y-Simulacion-Asociacion-Civil

## 🏫 Simulación de Eventos Discretos — Centro de Apoyo Escolar

Trabajo Práctico de la materia **Modelos y Simulación**.

### Descripción

Este proyecto simula el funcionamiento de un Centro de Apoyo Escolar de una Asociación Civil utilizando **SimPy** (Simulación de Eventos Discretos en Python).

Se modela:
- La **llegada estocástica** de niños (proceso de Poisson).
- La **atención por voluntarios** (recurso compartido limitado).
- La **duración de cada clase** (distribución normal truncada).

### Resultados que genera
- ⏳ Tiempo promedio de espera en cola.
- 📊 Porcentaje de ocupación de los voluntarios.
- ⚠️ Recomendación sobre si la cantidad de voluntarios es suficiente.

### Variables de control

| Variable | Descripción | Default |
|---|---|---|
| `NUM_VOLUNTARIOS` | Cantidad de voluntarios disponibles | 3 |
| `TIEMPO_SIMULACION` | Duración de la simulación (minutos) | 480 (8 hs) |
| `TASA_LLEGADA` | Tasa λ de llegadas (niños/min) | 1/10 |
| `DURACION_CLASE_MEDIA` | Duración media de cada clase (min) | 45 |
| `DURACION_CLASE_DESVIO` | Desvío estándar de la duración (min) | 10 |
| `SEMILLA` | Semilla para reproducibilidad | 42 |

### Instalación y ejecución

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la simulación
python simulacion_apoyo_escolar.py
```

### Tecnologías
- Python 3.10+
- [SimPy](https://simpy.readthedocs.io/) — Simulación de Eventos Discretos
