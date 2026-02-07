# Modelos y Simulación — Asociación Civil

## Simulación de Eventos Discretos: Centro de Apoyo Escolar

**Universidad Católica de Salta** — Licenciatura en Ciencia de Datos  
**Materia:** Modelos y Simulación  
**Docente:** Gustavo Ramiro Rivadera  
**Alumno:** Morena Caparros  

---

### Descripción

Este proyecto implementa un modelo de **Simulación de Eventos Discretos (DES)** con **SimPy** para validar la lógica de asignación y la capacidad operativa del Centro de Apoyo Escolar de una Asociación Civil, antes de su informatización definitiva.

### Componentes modelados

| Componente | Descripción |
|---|---|
| **Niños** (entidades de flujo) | Atributos aleatorios: Dificultad (Leve/Moderada/Grave) y Área (Matemática/Lectura/Grafismo) |
| **Voluntarios** (recursos) | Clasificados por Nivel de Expertise (1-3) y Área de competencia |
| **Equipo Profesional** (servidor) | Recurso limitado que evalúa y valida cada asignación (cuello de botella) |
| **Algoritmo de Matching** | Regla: Skill >= Dificultad en el área correcta. Política configurable: estricto vs. generalista |

### Escenarios de prueba (Sección 4.3 del anteproyecto)

| Escenario | Descripción |
|---|---|
| **Base** | Operación normal: 3 niños/semana, 8 voluntarios, 2 profesionales |
| **A — Déficit** | Alta demanda (5 niños/sem), mayoría graves, 4 voluntarios básicos, 1 profesional |
| **B — Crecimiento** | Aumento 200% en matrícula (9 niños/sem), mismos recursos |

### KPIs medidos

1. **Tiempo promedio de espera en cola** antes de recibir asignación.
2. **Tasa de Mal Matching** — % de niños atendidos por voluntarios no óptimos.
3. **Ocupación de Voluntarios** — desglosada por voluntario individual.
4. **Ocupación del Equipo Profesional** — detecta saturación del servidor.

### Instalación y ejecución

```bash
pip install -r requirements.txt
python simulacion_apoyo_escolar.py
```

### Tecnologías
- Python 3.10+
- [SimPy 4.x](https://simpy.readthedocs.io/) — Simulación de Eventos Discretos
