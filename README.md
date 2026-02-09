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
de niños que llegan con dificultades de aprendizaje, y validar la
logica de asignacion antes de implementarla en software real.

### Que se modela

- **Niños (entidades)**: llegan al azar (proceso de Poisson), cada uno con
  una dificultad (Leve/Moderada/Grave) y un area (Matematica/Lectura/Grafismo),
  asignadas con distribuciones de probabilidad configurables.
- **Voluntarios (recursos)**: tienen un nivel de expertise (1-3) y un area.
  Cuando estan ocupados no pueden atender a otro niño.
- **Equipo Profesional (servidor)**: evalua a cada niño antes de asignarle
  voluntario. Son pocos, asi que pueden generar cuello de botella.
- **Matching**: se busca un voluntario cuyo nivel sea >= la dificultad
  del niño y que coincida en el area. Si no hay match exacto, se puede
  asignar un generalista (politica flexible) o el niño espera (politica estricta).

### Escenarios

| Escenario | Que prueba |
|---|---|
| Base | Operacion normal: 3 niños/sem, 8 voluntarios, 2 profesionales |
| A - Deficit | Muchos niños graves, pocos voluntarios basicos, 1 profesional |
| B - Crecimiento | 200% mas de matricula, mismos recursos |

Ademas se comparan las dos politicas de asignacion:
- **Generalista**: si no hay match optimo, se asigna cualquier voluntario libre.
- **Estricto**: el niño espera hasta que haya un voluntario adecuado (o se va).

### KPIs que mide

1. Tiempo promedio de espera en cola (desglosado por dificultad)
2. Tasa de mal matching (% de asignaciones no optimas)
3. Ocupacion de cada voluntario
4. Ocupacion del Equipo Profesional

### Como correrlo

**Simulacion por consola:**
```bash
pip install -r requirements.txt
python simulacion_apoyo_escolar.py
```

**Dashboard visual (Streamlit) — opcional:**
```bash
pip install -r requirements.txt
streamlit run app.py
```
> **Nota:** El archivo `app.py` es solo un agregado visual para explorar
> los resultados de forma interactiva. No es parte del contenido evaluable
> del trabajo; toda la simulacion y los resultados se obtienen ejecutando
> `simulacion_apoyo_escolar.py` por consola.

### Tecnologias
- Python 3
- SimPy 4
- Streamlit (dashboard)
- Pandas (tablas)
