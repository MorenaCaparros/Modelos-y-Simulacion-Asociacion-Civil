# Modelos y Simulacion - Asociacion Civil

## Centro de Apoyo Escolar - Simulacion

**Universidad Catolica de Salta** - Lic. en Ciencia de Datos  
**Materia:** Modelos y Simulacion  
**Docente:** Gustavo Ramiro Rivadera  
**Alumno:** Morena Caparros  

---

### De que trata

Se simula el funcionamiento de un Centro de Apoyo Escolar usando
SimPy (Simulacion de Eventos Discretos). El objetivo es ver si la
cantidad de voluntarios y profesionales alcanza para cubrir la demanda
de niños que llegan con dificultades de aprendizaje.

### Que se modela

- **Niños**: llegan al azar (Poisson), cada uno con una dificultad
  (Leve/Moderada/Grave) y un area (Matematica/Lectura/Grafismo).
- **Voluntarios**: tienen un nivel de expertise (1-3) y un area.
  Cuando estan ocupados no pueden atender a otro niño.
- **Equipo Profesional**: evalua a cada niño antes de asignarle
  voluntario. Son pocos, asi que pueden generar cuello de botella.
- **Matching**: se busca un voluntario cuyo nivel sea >= la dificultad
  del niño y que coincida en el area.

### Escenarios

| Escenario | Que prueba |
|---|---|
| Base | Operacion normal: 3 niños/sem, 8 voluntarios, 2 profesionales |
| A - Deficit | Muchos niños graves, pocos voluntarios basicos, 1 profesional |
| B - Crecimiento | 200% mas de matricula, mismos recursos |

### KPIs que mide

1. Tiempo promedio de espera en cola
2. Tasa de mal matching (% de asignaciones no optimas)
3. Ocupacion de cada voluntario
4. Ocupacion del Equipo Profesional

### Como correrlo

```bash
pip install -r requirements.txt
python simulacion_apoyo_escolar.py
```

### Tecnologias
- Python 3
- SimPy
