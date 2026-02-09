"""
Dashboard Streamlit para la simulacion del Centro de Apoyo Escolar.
Permite al docente (o cualquiera) ajustar parametros y ver resultados
de forma visual sin tocar el codigo.
"""

import streamlit as st
import pandas as pd
from simulacion_apoyo_escolar import (
    correr_simulacion,
    VOLUNTARIOS_BASE,
    ESCENARIO_BASE,
    ESCENARIO_A,
    ESCENARIO_B,
    ESCENARIO_C,
    ESCENARIO_D,
    ESCENARIO_BASE_ESTRICTO,
)


# -- Configuracion de la pagina --
st.set_page_config(
    page_title="Centro de Apoyo Escolar - Simulacion",
    page_icon=":material/school:",
    layout="wide",
)


# -- Helper para iconos Material inline --
def icon(name, size=20, color="#444"):
    """Devuelve HTML de un icono Material Symbols Rounded."""
    return (
        f'<span class="material-symbols-rounded" '
        f'style="font-size:{size}px;vertical-align:middle;color:{color};'
        f'margin-right:4px;">{name}</span>'
    )


def header_con_icono(icono_name, texto, nivel=3, color="#444"):
    """Renderiza un heading con un icono Material a la izquierda."""
    tag = f"h{nivel}"
    st.markdown(
        f"<{tag} style='display:flex;align-items:center;gap:8px;'>"
        f"{icon(icono_name, size=24, color=color)}{texto}</{tag}>",
        unsafe_allow_html=True,
    )


# -- Estilos CSS + Google Material Symbols --
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
<style>
    .block-container { padding-top: 1.5rem; }
    .material-symbols-rounded {
        font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
    div[data-testid="stMetric"] {
        background-color: #f8f9fb;
        border: 1px solid #e8eaed;
        border-radius: 12px;
        padding: 14px 18px;
    }
    div[data-testid="stMetric"] label {
        font-size: 0.82rem;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    .status-dot {
        display: inline-block;
        width: 10px; height: 10px;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }
    .dot-red    { background: #d93025; }
    .dot-yellow { background: #f9ab00; }
    .dot-green  { background: #1e8e3e; }
</style>
""", unsafe_allow_html=True)


# -- Sidebar --
with st.sidebar:
    st.markdown(
        f"<div style='text-align:center;padding:8px 0 4px;'>"
        f"{icon('school', size=40, color='#4285f4')}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"{icon('tune', color='#5f6368')} **Parametros**",
        unsafe_allow_html=True,
    )
    st.caption("Ajusta los valores y hace clic en **Simular**")

    st.divider()

    modo = st.radio(
        "Modo de simulacion",
        ["Escenarios predefinidos", "Parametros custom"],
        index=0,
    )

    if modo == "Escenarios predefinidos":
        escenarios_sel = st.multiselect(
            "Escenarios a correr",
            ["Base (Normal)", "A - Deficit", "B - Crecimiento",
             "C - Reforzado", "D - Demanda baja", "Base (Estricto)"],
            default=["Base (Normal)", "A - Deficit", "B - Crecimiento"],
        )
    else:
        st.subheader("Llegada de niños")
        tasa = st.slider("Tasa de llegada (niños/sem)", 1.0, 15.0, 3.0, 0.5)
        semanas = st.slider("Semanas de simulacion", 12, 104, 52, 4)

        st.subheader("Dificultad (%)")
        p_leve = st.slider("Leve", 0, 100, 50, 5)
        p_moderada = st.slider("Moderada", 0, 100, 35, 5)
        p_grave = 100 - p_leve - p_moderada
        if p_grave < 0:
            st.error("Leve + Moderada no puede superar 100%")
            p_grave = 0
        else:
            st.info(f"Grave: **{p_grave}%**")

        st.subheader("Area (%)")
        p_mate = st.slider("Matematica", 0, 100, 45, 5)
        p_lect = st.slider("Lectura", 0, 100, 35, 5)
        p_graf = 100 - p_mate - p_lect
        if p_graf < 0:
            st.error("Mate + Lectura no puede superar 100%")
            p_graf = 0
        else:
            st.info(f"Grafismo: **{p_graf}%**")

        st.subheader("Recursos")
        n_prof = st.slider("Equipo Profesional (cant.)", 1, 5, 2)
        n_vol = st.slider("Voluntarios", 2, 15, 8)
        permitir_gen = st.toggle("Permitir generalista", value=True)
        semilla = st.number_input("Semilla aleatoria", value=42, step=1)

    st.divider()
    boton = st.button(
        "Simular", use_container_width=True, type="primary",
        icon=":material/play_arrow:",
    )


# -- Header principal --
st.markdown(
    f"<h2 style='display:flex;align-items:center;gap:10px;margin-bottom:0;'>"
    f"{icon('school', size=30, color='#4285f4')}Centro de Apoyo Escolar</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<span style='color:#5f6368;font-size:0.9rem;'>"
    "Modelos y Simulacion · Universidad Catolica de Salta · "
    "Morena Caparros · 2026</span>",
    unsafe_allow_html=True,
)
st.divider()


# -- Datos auxiliares --
MAPA_ESCENARIOS = {
    "Base (Normal)": ESCENARIO_BASE,
    "A - Deficit": ESCENARIO_A,
    "B - Crecimiento": ESCENARIO_B,
    "C - Reforzado": ESCENARIO_C,
    "D - Demanda baja": ESCENARIO_D,
    "Base (Estricto)": ESCENARIO_BASE_ESTRICTO,
}


def construir_config_custom():
    """Arma un config dict con los parametros del sidebar custom."""
    areas = ["matematica", "lectura", "grafismo"]
    vols = []
    for i in range(n_vol):
        vols.append({
            "nombre": f"Vol-{i+1:02d}",
            "expertise": (i % 3) + 1,
            "area": areas[i % 3],
        })
    return {
        "nombre": "Custom",
        "tiempo_simulacion": semanas,
        "semilla": int(semilla),
        "tasa_llegada": tasa,
        "prob_dificultad": [p_leve / 100, p_moderada / 100, p_grave / 100],
        "prob_area": [p_mate / 100, p_lect / 100, p_graf / 100],
        "voluntarios_spec": vols,
        "num_profesionales": n_prof,
        "permitir_generalista": permitir_gen,
        "max_espera_vol": 8,
    }


def mostrar_metricas(r):
    """Muestra las 4 metric cards principales."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Espera promedio", f"{r['espera_prom']:.1f} sem", help="Tiempo medio en cola")
    c2.metric("Mal matching", f"{r['mal_matching']:.0f}%", help="Asignaciones no optimas")
    c3.metric("Ocup. Voluntarios", f"{r['ocup_vol']:.0f}%", help="Uso promedio de voluntarios")
    c4.metric("Ocup. Eq. Profesional", f"{r['ocup_prof']:.0f}%", help="Uso del equipo evaluador")


def mostrar_detalle(r):
    """Tablas y graficos de detalle de un escenario."""

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Llegaron", r["llegaron"])
    c2.metric("Atendidos", r["atendidos"])
    c3.metric("Sin atencion", r["no_atendidos"])
    c4.metric("En proceso", r["en_proceso"])

    col_izq, col_der = st.columns(2)

    with col_izq:
        header_con_icono("target", "Distribucion de Matching", nivel=5)
        match_data = pd.DataFrame({
            "Tipo": ["Optimo", "Suboptimo", "Generalista"],
            "Cantidad": [r["optimos"], r["suboptimos"], r["generalistas"]],
        })
        st.bar_chart(match_data.set_index("Tipo"), height=250, color="#4285f4")

    with col_der:
        header_con_icono("bar_chart", "Espera por Dificultad (sem)", nivel=5)
        dif_data = pd.DataFrame([
            {"Dificultad": k, "Espera prom (sem)": v["promedio"], "Niños": v["cantidad"]}
            for k, v in r["espera_por_dificultad"].items()
        ])
        st.bar_chart(
            dif_data.set_index("Dificultad")["Espera prom (sem)"],
            height=250, color="#f9ab00",
        )

    header_con_icono("groups", "Ocupacion de Voluntarios", nivel=5)
    vol_df = pd.DataFrame(r["voluntarios"])
    vol_df["etiqueta"] = (
        vol_df["nombre"] + " (E" +
        vol_df["expertise"].astype(str) + ", " +
        vol_df["area"] + ")"
    )
    st.bar_chart(vol_df.set_index("etiqueta")["ocupacion"], height=280, color="#1e8e3e")


def dot(color_class):
    """Devuelve un circulo de color para usar como semaforo."""
    return f'<span class="status-dot {color_class}"></span>'


def mostrar_diagnostico(r):
    """Panel de diagnostico con semaforos visuales (circulos de color)."""
    alertas = []

    if r["ocup_prof"] > 85:
        alertas.append(f"{dot('dot-red')} Eq. Profesional **SATURADO** ({r['ocup_prof']:.0f}%)")
    else:
        alertas.append(f"{dot('dot-green')} Eq. Profesional con capacidad ({r['ocup_prof']:.0f}%)")

    if r["mal_matching"] > 40:
        alertas.append(f"{dot('dot-red')} Mal matching **ALTO** ({r['mal_matching']:.0f}%)")
    elif r["mal_matching"] > 20:
        alertas.append(f"{dot('dot-yellow')} Mal matching moderado ({r['mal_matching']:.0f}%)")
    else:
        alertas.append(f"{dot('dot-green')} Mal matching aceptable ({r['mal_matching']:.0f}%)")

    if r["espera_prom"] > 4:
        alertas.append(f"{dot('dot-red')} Espera **MUY ALTA** ({r['espera_prom']:.1f} sem)")
    else:
        alertas.append(f"{dot('dot-green')} Espera aceptable ({r['espera_prom']:.1f} sem)")

    if r["no_atendidos"] > 0:
        alertas.append(f"{dot('dot-yellow')} {r['no_atendidos']} niños se fueron sin atencion")

    for a in alertas:
        st.markdown(f"- {a}", unsafe_allow_html=True)


# -- Ejecucion --
if boton:
    resultados = []

    if modo == "Escenarios predefinidos":
        if not escenarios_sel:
            st.warning("Selecciona al menos un escenario.")
            st.stop()

        with st.spinner("Corriendo simulacion..."):
            for nombre_esc in escenarios_sel:
                config = MAPA_ESCENARIOS[nombre_esc]
                r = correr_simulacion(config, silencioso=True)
                resultados.append(r)
    else:
        with st.spinner("Corriendo simulacion..."):
            config = construir_config_custom()
            r = correr_simulacion(config, silencioso=True)
            resultados.append(r)

    st.success(f"Simulacion completa — {len(resultados)} escenario(s)")
    st.divider()

    # Tabla comparativa (si hay varios escenarios)
    if len(resultados) > 1:
        header_con_icono("compare_arrows", "Comparativa de Escenarios")

        comp_df = pd.DataFrame(resultados)[
            ["nombre", "llegaron", "atendidos", "no_atendidos",
             "espera_prom", "espera_max", "mal_matching", "ocup_vol", "ocup_prof"]
        ]
        comp_df.columns = [
            "Escenario", "Llegaron", "Atendidos", "Sin atencion",
            "Espera prom (sem)", "Espera max (sem)",
            "Mal matching (%)", "Ocup. Vol (%)", "Ocup. Prof (%)",
        ]
        st.dataframe(comp_df.set_index("Escenario"), use_container_width=True)

        header_con_icono("monitoring", "KPIs Comparados")
        kpi_comp = pd.DataFrame({
            "Escenario": [r["nombre"] for r in resultados],
            "Espera prom (sem)": [r["espera_prom"] for r in resultados],
            "Mal matching (%)": [r["mal_matching"] for r in resultados],
            "Ocup. Vol (%)": [r["ocup_vol"] for r in resultados],
            "Ocup. Prof (%)": [r["ocup_prof"] for r in resultados],
        })
        st.bar_chart(kpi_comp.set_index("Escenario"), height=350)
        st.divider()

    # Detalle por escenario
    if len(resultados) == 1:
        r = resultados[0]
        header_con_icono("analytics", f"Resultados: {r['nombre']}")
        mostrar_metricas(r)
        mostrar_detalle(r)
    else:
        tabs = st.tabs([r["nombre"] for r in resultados])
        for tab, r in zip(tabs, resultados):
            with tab:
                mostrar_metricas(r)
                mostrar_detalle(r)

    # Diagnostico
    st.divider()
    header_con_icono("vital_signs", "Diagnostico")
    for r in resultados:
        with st.expander(f"**{r['nombre']}**", expanded=len(resultados) == 1):
            mostrar_diagnostico(r)

else:
    # Pantalla de bienvenida
    st.info(
        "Configura los parametros en el panel izquierdo y "
        "hace clic en **Simular** para ver los resultados."
    )

    with st.expander("Sobre este modelo", expanded=True, icon=":material/info:"):
        st.markdown("""
        Este dashboard corre una **Simulacion de Eventos Discretos** (SimPy)
        del Centro de Apoyo Escolar de una Asociacion Civil.

        **Entidades:** Niños que llegan con una dificultad (Leve/Moderada/Grave)
        y un area (Matematica/Lectura/Grafismo).

        **Recursos:** Voluntarios con expertise (1-3) y area de especialidad.

        **Servidor:** Equipo Profesional que evalua a cada niño antes de asignarle
        un voluntario (cuello de botella).

        **Regla de matching:** El expertise del voluntario debe ser >= la dificultad
        del niño, y coincidir en el area.

        **Escenarios predefinidos:**
        - **Base**: operacion normal (3 niños/sem, 8 vol, 2 prof)
        - **A - Deficit**: muchos casos graves, pocos voluntarios, 1 profesional
        - **B - Crecimiento**: 200% mas matricula, mismos recursos
        - **C - Reforzado**: voluntarios expertos en todas las areas, 3 profesionales
        - **D - Demanda baja**: mitad de llegadas, mayoria leves
        - **Base (Estricto)**: sin asignacion generalista (el niño espera o se va)
        """)
