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
    ESCENARIO_BASE_ESTRICTO,
)

# -- Configuracion de la pagina --
st.set_page_config(
    page_title="Centro de Apoyo Escolar - Simulacion",
    page_icon="🏫",
    layout="wide",
)

# -- Estilos CSS custom --
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    div[data-testid="stMetric"] label { font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)


# =====================================================================
#  SIDEBAR - Parametros
# =====================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/school.png", width=64)
    st.title("⚙️ Parametros")
    st.caption("Ajusta los valores y hace clic en **Simular**")

    st.divider()

    # Escenario predefinido o custom
    modo = st.radio(
        "Modo de simulacion",
        ["Escenarios predefinidos", "Parametros custom"],
        index=0,
    )

    if modo == "Escenarios predefinidos":
        escenarios_sel = st.multiselect(
            "Escenarios a correr",
            ["Base (Normal)", "A - Deficit", "B - Crecimiento", "Base (Estricto)"],
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
    boton = st.button("🚀 Simular", use_container_width=True, type="primary")


# =====================================================================
#  HEADER
# =====================================================================
st.markdown("## 🏫 Centro de Apoyo Escolar")
st.markdown(
    "**Modelos y Simulacion** · Universidad Catolica de Salta · "
    "Morena Caparros · 2026"
)
st.divider()


# =====================================================================
#  FUNCIONES AUXILIARES
# =====================================================================

MAPA_ESCENARIOS = {
    "Base (Normal)": ESCENARIO_BASE,
    "A - Deficit": ESCENARIO_A,
    "B - Crecimiento": ESCENARIO_B,
    "Base (Estricto)": ESCENARIO_BASE_ESTRICTO,
}

COLORES_ESCENARIOS = {
    "Base (Normal)": "#4C78A8",
    "A - Deficit": "#E45756",
    "B - Crecimiento": "#F58518",
    "Base (Estricto)": "#72B7B2",
}


def construir_config_custom():
    """Arma un config dict con los parametros del sidebar custom."""
    # Generar voluntarios simples distribuidos entre areas
    areas = ["matematica", "lectura", "grafismo"]
    vols = []
    for i in range(n_vol):
        vols.append({
            "nombre": f"Vol-{i+1:02d}",
            "expertise": (i % 3) + 1,       # rota 1, 2, 3
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
    """Muestra las 4 metric cards de un escenario."""
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⏱️ Espera prom.", f"{r['espera_prom']:.1f} sem")
    c2.metric("❌ Mal matching", f"{r['mal_matching']:.0f}%")
    c3.metric("👥 Ocup. Voluntarios", f"{r['ocup_vol']:.0f}%")
    c4.metric("🩺 Ocup. Eq. Prof.", f"{r['ocup_prof']:.0f}%")


def mostrar_detalle(r):
    """Muestra tablas y graficos de detalle de un escenario."""

    # Fila de numeros generales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Llegaron", r["llegaron"])
    c2.metric("Atendidos", r["atendidos"])
    c3.metric("Sin atencion", r["no_atendidos"])
    c4.metric("En proceso", r["en_proceso"])

    col_izq, col_der = st.columns(2)

    # --- Grafico de matching ---
    with col_izq:
        st.markdown("##### 🎯 Distribucion de Matching")
        match_data = pd.DataFrame({
            "Tipo": ["Optimo", "Suboptimo", "Generalista"],
            "Cantidad": [r["optimos"], r["suboptimos"], r["generalistas"]],
        })
        st.bar_chart(match_data.set_index("Tipo"), height=250)

    # --- Espera por dificultad ---
    with col_der:
        st.markdown("##### 📊 Espera por Dificultad (sem)")
        dif_data = pd.DataFrame([
            {"Dificultad": k, "Espera prom (sem)": v["promedio"], "Niños": v["cantidad"]}
            for k, v in r["espera_por_dificultad"].items()
        ])
        st.bar_chart(dif_data.set_index("Dificultad")["Espera prom (sem)"], height=250)

    # --- Ocupacion de voluntarios ---
    st.markdown("##### 🧑‍🏫 Ocupacion de Voluntarios")
    vol_df = pd.DataFrame(r["voluntarios"])
    vol_df["etiqueta"] = vol_df["nombre"] + " (E" + vol_df["expertise"].astype(str) + ", " + vol_df["area"] + ")"
    st.bar_chart(vol_df.set_index("etiqueta")["ocupacion"], height=280)


# =====================================================================
#  EJECUTAR SIMULACION
# =====================================================================

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
        # Custom
        with st.spinner("Corriendo simulacion..."):
            config = construir_config_custom()
            r = correr_simulacion(config, silencioso=True)
            resultados.append(r)

    st.success(f"Simulacion completa — {len(resultados)} escenario(s)")
    st.divider()

    # -----------------------------------------------------------------
    #  Si hay multiples escenarios: tabla comparativa primero
    # -----------------------------------------------------------------
    if len(resultados) > 1:
        st.markdown("### 📋 Comparativa de Escenarios")

        comp_df = pd.DataFrame(resultados)[
            ["nombre", "llegaron", "atendidos", "no_atendidos",
             "espera_prom", "espera_max", "mal_matching", "ocup_vol", "ocup_prof"]
        ]
        comp_df.columns = [
            "Escenario", "Llegaron", "Atendidos", "Sin atencion",
            "Espera prom (sem)", "Espera max (sem)",
            "Mal matching (%)", "Ocup. Vol (%)", "Ocup. Prof (%)",
        ]
        st.dataframe(
            comp_df.set_index("Escenario"),
            use_container_width=True,
        )

        # Grafico comparativo de KPIs clave
        st.markdown("### 📊 KPIs Comparados")
        kpi_comp = pd.DataFrame({
            "Escenario": [r["nombre"] for r in resultados],
            "Espera prom (sem)": [r["espera_prom"] for r in resultados],
            "Mal matching (%)": [r["mal_matching"] for r in resultados],
            "Ocup. Vol (%)": [r["ocup_vol"] for r in resultados],
            "Ocup. Prof (%)": [r["ocup_prof"] for r in resultados],
        })
        st.bar_chart(
            kpi_comp.set_index("Escenario"),
            height=350,
        )
        st.divider()

    # -----------------------------------------------------------------
    #  Detalle por escenario (tabs)
    # -----------------------------------------------------------------
    if len(resultados) == 1:
        r = resultados[0]
        st.markdown(f"### 📈 Resultados: {r['nombre']}")
        mostrar_metricas(r)
        mostrar_detalle(r)
    else:
        tabs = st.tabs([r["nombre"] for r in resultados])
        for tab, r in zip(tabs, resultados):
            with tab:
                mostrar_metricas(r)
                mostrar_detalle(r)

    # -----------------------------------------------------------------
    #  Diagnostico
    # -----------------------------------------------------------------
    st.divider()
    st.markdown("### 🩺 Diagnostico")
    for r in resultados:
        with st.expander(f"**{r['nombre']}**", expanded=len(resultados) == 1):
            alertas = []
            if r["ocup_prof"] > 85:
                alertas.append(f"🔴 Eq. Profesional **SATURADO** ({r['ocup_prof']:.0f}%)")
            else:
                alertas.append(f"🟢 Eq. Profesional con capacidad ({r['ocup_prof']:.0f}%)")

            if r["mal_matching"] > 40:
                alertas.append(f"🔴 Mal matching **ALTO** ({r['mal_matching']:.0f}%)")
            elif r["mal_matching"] > 20:
                alertas.append(f"🟡 Mal matching moderado ({r['mal_matching']:.0f}%)")
            else:
                alertas.append(f"🟢 Mal matching aceptable ({r['mal_matching']:.0f}%)")

            if r["espera_prom"] > 4:
                alertas.append(f"🔴 Espera **MUY ALTA** ({r['espera_prom']:.1f} sem)")
            else:
                alertas.append(f"🟢 Espera aceptable ({r['espera_prom']:.1f} sem)")

            if r["no_atendidos"] > 0:
                alertas.append(f"🟡 {r['no_atendidos']} niños se fueron sin atencion")

            for a in alertas:
                st.markdown(f"- {a}")

else:
    # Estado inicial - pantalla de bienvenida
    st.info(
        "👈 Configura los parametros en el panel izquierdo y "
        "hace clic en **Simular** para ver los resultados."
    )

    # Mostrar una descripcion rapida del modelo
    with st.expander("ℹ️ Sobre este modelo", expanded=True):
        st.markdown("""
        Este dashboard corre una **Simulacion de Eventos Discretos** (SimPy)
        del Centro de Apoyo Escolar de una Asociacion Civil.

        **Entidades:** Niños que llegan con una dificultad (Leve/Moderada/Grave)
        y un area (Matematica/Lectura/Grafismo).

        **Recursos:** Voluntarios con expertise (1-3) y area de especialidad.

        **Servidor:** Equipo Profesional que evalua a cada niño antes de asignarle
        un voluntario (cuello de botella).

        **Regla de matching:** El expertise del voluntario debe ser ≥ la dificultad
        del niño, y coincidir en el area.

        **Escenarios predefinidos:**
        - **Base**: operacion normal (3 niños/sem, 8 vol, 2 prof)
        - **A - Deficit**: muchos casos graves, pocos voluntarios, 1 profesional
        - **B - Crecimiento**: 200% mas matricula, mismos recursos
        - **Base (Estricto)**: sin asignacion generalista (el niño espera o se va)
        """)
