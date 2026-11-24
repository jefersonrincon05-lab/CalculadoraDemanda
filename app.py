"""
Calculadora de Demanda Doméstica e Industrial de Agua
Aplicación Web Profesional desarrollada en Streamlit y Python

Autor: Ingeniero Especialista en Abastecimiento de Agua e Hidrología
"""

import io
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from hydrology_engine import (
    SECONDS_PER_DAY,
    LITERS_PER_M3,
    FACTOR_LS_TO_M3DAY,
    m3_day_to_L_s,
    L_s_to_m3_day,
    DomesticDemandInput,
    IndustrialRecord,
    WaterDemandEngine,
    WaterDemandResults,
)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Calculadora de Demanda de Agua",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Estilos generales y tipografía */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .section-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background-color: #e0f2fe;
        color: #0369a1;
        margin-bottom: 0.5rem;
    }
    .k-card {
        background-color: #f8fafc;
        border-left: 4px solid #0284c7;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# CONSTANTES Y BENCHMARKS TÍPICOS DE REFERENCIA INDUSTRIAL
# -----------------------------------------------------------------------------
BENCHMARK_INDUSTRIAS = {
    "Personalizada": {"unit": "m3/unidad", "consumo": 1.0},
    "Bebidas y Gaseosas (L de agua / L bebida)": {"unit": "L/unidad", "consumo": 2.5},
    "Cervecería Artesanal / Industrial (L agua / L cerveza)": {"unit": "L/unidad", "consumo": 4.5},
    "Planta Láctea / Pasteurizadora (L agua / L leche procesada)": {"unit": "L/unidad", "consumo": 2.0},
    "Matadero Bovino (L agua / animal sacrificado)": {"unit": "L/unidad", "consumo": 1200.0},
    "Matadero Porcino (L agua / animal sacrificado)": {"unit": "L/unidad", "consumo": 450.0},
    "Planta Avícola (L agua / ave faenada)": {"unit": "L/unidad", "consumo": 25.0},
    "Industria Textil - Tintorería (L agua / kg tela)": {"unit": "L/unidad", "consumo": 110.0},
    "Fabricación de Papel y Cartón (m³ agua / ton papel)": {"unit": "m3/unidad", "consumo": 25.0},
    "Central de Hormigón / Concretera (m³ agua / m³ concreto)": {"unit": "m3/unidad", "consumo": 0.20},
    "Curtiduría de Pieles (m³ agua / ton piel)": {"unit": "m3/unidad", "consumo": 35.0},
}


# -----------------------------------------------------------------------------
# SIDEBAR: CONFIGURACIÓN GENERAL Y PREAJUSTES
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuración del Sistema")
    st.markdown("Herramienta técnica conforme a buenas prácticas de **Ingeniería Sanitaria e Hidráulica**.")

    # Escenarios predefinidos para agilizar pruebas
    scenario = st.selectbox(
        "📂 Cargar Escenario de Prueba:",
        options=[
            "Personalizado",
            "Municipio Intermedio (45,000 hab + Agroindustria)",
            "Población Rural (4,500 hab + Lácteos)",
            "Zona Urbana - Industrial (120,000 hab + Textil/Bebidas)",
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("#### ⚡ Factores de Mayoración de Consumo")
    st.caption("Diferenciación estricta entre **Demanda Media Diaria** y **Caudales de Diseño Máximos**:")

    k1 = st.slider(
        "Coeficiente de Variación Diaria (k₁):",
        min_value=1.00,
        max_value=1.50,
        value=1.20,
        step=0.01,
        help="Relación entre el Caudal Máximo Diario y la Demanda Media Diaria (QMD = k₁ · Qmd). Rango normativo habitual: 1.15 a 1.30."
    )

    k2 = st.slider(
        "Coeficiente de Variación Horaria (k₂):",
        min_value=1.00,
        max_value=2.00,
        value=1.50,
        step=0.01,
        help="Relación entre el Caudal Máximo Horario y el Caudal Máximo Diario (QMH = k₂ · QMD). Rango normativo habitual: 1.40 a 1.60."
    )

    apply_k_to_industrial = st.checkbox(
        "Afectar consumo industrial con factores k₁ y k₂",
        value=False,
        help="En saneamiento estándar, los picos de consumo doméstico no afectan a industrias con régimen continuo o almacenamiento propio. Marque solo si la industria consume con variaciones horarias sincrónicas."
    )

    st.markdown("---")
    st.info("💡 **Principio Hidráulico Clave:**\n\n1 L/s continuo durante 24 horas equivale exactamente a **86.40 m³/día** (86,400 segundos / 1,000 L).")


# Inicialización de variables predeterminadas basadas en el escenario
if scenario == "Municipio Intermedio (45,000 hab + Agroindustria)":
    default_pop = 45000
    default_dot = 140.0
    default_losses = 20.0
    default_ind_mode = "Múltiples Industrias"
    init_industries = [
        IndustrialRecord("Planta Láctea Municipal", mode="specific", units_per_day=40000.0, specific_consumption=2.0, specific_unit="L/unidad"),
        IndustrialRecord("Bebidas del Valle", mode="specific", units_per_day=35000.0, specific_consumption=2.5, specific_unit="L/unidad"),
        IndustrialRecord("Frigorífico Bovino", mode="specific", units_per_day=250.0, specific_consumption=1200.0, specific_unit="L/unidad"),
    ]
elif scenario == "Población Rural (4,500 hab + Lácteos)":
    default_pop = 4500
    default_dot = 110.0
    default_losses = 15.0
    default_ind_mode = "Consumo Específico"
    init_industries = [
        IndustrialRecord("Quesería Artesanal", mode="specific", units_per_day=5000.0, specific_consumption=2.5, specific_unit="L/unidad"),
    ]
elif scenario == "Zona Urbana - Industrial (120,000 hab + Textil/Bebidas)":
    default_pop = 120000
    default_dot = 160.0
    default_losses = 25.0
    default_ind_mode = "Múltiples Industrias"
    init_industries = [
        IndustrialRecord("Parque Cervecero", mode="specific", units_per_day=150000.0, specific_consumption=4.5, specific_unit="L/unidad"),
        IndustrialRecord("Tintorería Textil", mode="specific", units_per_day=8000.0, specific_consumption=110.0, specific_unit="L/unidad"),
        IndustrialRecord("Papelera Industrial", mode="specific", units_per_day=60.0, specific_consumption=25.0, specific_unit="m3/unidad"),
        IndustrialRecord("Zona Franca Logística", mode="direct", direct_consumption_m3_day=450.0),
    ]
else:
    default_pop = 25000
    default_dot = 135.0
    default_losses = 18.0
    default_ind_mode = "Consumo Directo (m³/día)"
    init_industries = [
        IndustrialRecord("Industria Agroalimentaria", mode="direct", direct_consumption_m3_day=350.0),
    ]


# Guardar industrias en session_state para permitir edición dinámica
if "industries_list" not in st.session_state or st.session_state.get("current_scenario") != scenario:
    st.session_state["industries_list"] = init_industries
    st.session_state["current_scenario"] = scenario


# -----------------------------------------------------------------------------
# ENCABEZADO PRINCIPAL
# -----------------------------------------------------------------------------
st.markdown('<div class="main-title">💧 Calculadora de Demanda Doméstica e Industrial de Agua</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Plataforma técnica para estimación de caudales medios diarios ($Q_{md}$), demandas volumétricas ($m^3/\text{día}$) y caudales de diseño de abastecimiento.</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# PESTAÑAS PRINCIPALES DE NAVEGACIÓN
# -----------------------------------------------------------------------------
tab_calc, tab_industrias, tab_teoria, tab_export = st.tabs([
    "📊 Calculadora y Tablero Integrado",
    "🏭 Gestión de Demanda Industrial",
    "📐 Fundamentos Teóricos y Fórmulas",
    "📥 Exportación de Resultados",
])


# =============================================================================
# TAB 1: CALCULADORA Y RESULTADOS
# =============================================================================
with tab_calc:
    col_input, col_results = st.columns([1.1, 1.3], gap="large")

    with col_input:
        st.markdown("### 1️⃣ Parámetros de Entrada")

        # --- MÓDULO DOMÉSTICO ---
        with st.container():
            st.markdown("#### 🏠 Módulo de Demanda Doméstica")
            st.caption("Cálculo a partir de la población servida y la asignación dotacional per cápita.")

            col_p, col_d = st.columns(2)
            with col_p:
                poblacion = st.number_input(
                    "Población de Diseño (hab):",
                    min_value=0,
                    max_value=10_000_000,
                    value=int(default_pop),
                    step=500,
                    help="Número de habitantes proyectados a abastecer en el horizonte de diseño."
                )

            with col_d:
                dotacion_neta = st.number_input(
                    "Dotación Neta (L/hab·día):",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(default_dot),
                    step=5.0,
                    help="Volumen neto de agua diario asignado a cada habitante para sus necesidades básicas."
                )

            with st.expander("ℹ️ Referencias normativas orientativas de dotación", expanded=False):
                st.markdown("""
                *Valores típicos de dotación neta según clima y nivel de servicio (sin carácter obligatorio):*
                - **Clima Frío / Templado (< 15 °C):** 100 - 130 L/hab·día.
                - **Clima Cálido (> 20 °C):** 130 - 170 L/hab·día.
                - **Poblaciones rurales dispersas:** 70 - 100 L/hab·día.
                - **Ciudades metropolitanas:** 150 - 250 L/hab·día.
                """)

            perdidas_pct = st.slider(
                "Pérdidas Técnicas / Físicas en Red (%):",
                min_value=0.0,
                max_value=45.0,
                value=float(default_losses),
                step=1.0,
                help="Agua no contabilizada (ANC) debida a fugas y roturas. Permite calcular la Dotación Bruta: D_bruta = D_neta / (1 - %Pérdidas/100)."
            )

            # Instancia doméstica
            try:
                dom_input = DomesticDemandInput(
                    population=poblacion,
                    endowment_L_hab_day=dotacion_neta,
                    technical_losses_pct=perdidas_pct
                )
                dotacion_bruta = dom_input.get_gross_endowment()
                st.caption(f"🔹 **Dotación Bruta Resultante:** `{dotacion_bruta:.2f} L/hab·día` (considerando `{perdidas_pct:.1f}%` de pérdidas).")
            except Exception as e:
                st.error(f"Error en datos domésticos: {e}")
                dom_input = DomesticDemandInput(0, 0, 0)
                dotacion_bruta = 0.0

        st.markdown("---")

        # --- MÓDULO INDUSTRIAL ---
        with st.container():
            st.markdown("#### 🏭 Módulo de Demanda Industrial")
            st.caption("Selecciona el método de entrada de consumos industriales.")

            modo_ind = st.radio(
                "Método de Ingreso Industrial:",
                options=[
                    "Consumo Directo (m³/día)",
                    "Consumo Específico (Producción × Índice)",
                    "Múltiples Industrias (Detalle Avanzado)"
                ],
                horizontal=True
            )

            current_industries: List[IndustrialRecord] = []

            if modo_ind == "Consumo Directo (m³/día)":
                consumo_directo_m3 = st.number_input(
                    "Consumo Industrial Total (m³/día):",
                    min_value=0.0,
                    max_value=1_000_000.0,
                    value=350.0,
                    step=10.0,
                    help="Volumen total diario requerido por las industrias de la zona."
                )
                current_industries = [
                    IndustrialRecord(
                        name="Sector Industrial Consolidado",
                        mode="direct",
                        direct_consumption_m3_day=consumo_directo_m3
                    )
                ]

            elif modo_ind == "Consumo Específico (Producción × Índice)":
                st.markdown("**Cálculo por proceso productivo:**")
                tipo_benchmark = st.selectbox(
                    "Sector Industrial o Tipo de Planta:",
                    options=list(BENCHMARK_INDUSTRIAS.keys())
                )
                preset_data = BENCHMARK_INDUSTRIAS[tipo_benchmark]

                col_u, col_c = st.columns(2)
                with col_u:
                    unidades_dia = st.number_input(
                        "Unidades producidas al día:",
                        min_value=0.0,
                        value=50000.0 if "L" in preset_data["unit"] else 50.0,
                        step=100.0,
                        help="Ejemplo: Litros producidos, cabezas de ganado, kilogramos o toneladas al día."
                    )

                with col_c:
                    unidad_sel = st.selectbox("Unidad de consumo:", ["L/unidad", "m3/unidad"], index=0 if preset_data["unit"] == "L/unidad" else 1)
                    consumo_esp = st.number_input(
                        f"Consumo Específico ({unidad_sel}):",
                        min_value=0.0,
                        value=float(preset_data["consumo"]),
                        step=0.1,
                        format="%.4f"
                    )

                current_industries = [
                    IndustrialRecord(
                        name=tipo_benchmark,
                        mode="specific",
                        units_per_day=unidades_dia,
                        specific_consumption=consumo_esp,
                        specific_unit=unidad_sel
                    )
                ]

            else:
                # Múltiples industrias
                st.info(f"Se utilizarán las **{len(st.session_state['industries_list'])} industrias** configuradas en la pestaña 'Gestión de Demanda Industrial'. Puedes editarlas o agregar más en dicha pestaña.")
                current_industries = st.session_state["industries_list"]

    # --- CÁLCULO GENERAL ---
    results: WaterDemandResults = WaterDemandEngine.calculate_total_system_demand(
        domestic_input=dom_input,
        industrial_records=current_industries,
        k1=k1,
        k2=k2,
        apply_k_to_industrial=apply_k_to_industrial
    )

    with col_results:
        st.markdown("### 2️⃣ Resultados Hidráulicos Consolidados")

        # Fila de métricas clave: Doméstica, Industrial, Total
        mcol1, mcol2, mcol3 = st.columns(3)

        with mcol1:
            st.markdown('<span class="metric-badge">🏠 DOMÉSTICA</span>', unsafe_allow_html=True)
            st.metric(
                label="Demanda Doméstica Media",
                value=f"{results.domestic_flow_L_s:.2f} L/s",
                delta=f"{results.domestic_volume_m3_day:,.1f} m³/día"
            )

        with mcol2:
            st.markdown('<span class="metric-badge">🏭 INDUSTRIAL</span>', unsafe_allow_html=True)
            st.metric(
                label="Demanda Industrial Media",
                value=f"{results.industrial_flow_L_s:.2f} L/s",
                delta=f"{results.industrial_volume_m3_day:,.1f} m³/día"
            )

        with mcol3:
            st.markdown('<span class="metric-badge" style="background:#dcfce7; color:#15803d;">💧 TOTAL Qmd</span>', unsafe_allow_html=True)
            st.metric(
                label="Demanda Media Diaria (Qmd)",
                value=f"{results.total_flow_L_s:.2f} L/s",
                delta=f"{results.total_volume_m3_day:,.1f} m³/día"
            )

        st.markdown("---")

        # Caudales Máximos de Diseño
        st.markdown("#### 🚀 Caudales de Diseño y Capacidad Máxima")
        st.caption("Diferenciación con la demanda media: utilizados para el dimensionamiento hidráulico de tuberías, plantas y tanques.")

        col_qmd, col_qmh = st.columns(2)
        with col_qmd:
            st.markdown(f"""
            <div class="k-card">
                <b>Caudal Máximo Diario (QMD):</b><br/>
                <span style="font-size: 1.5rem; font-weight: 700; color: #0284c7;">{results.q_max_daily_flow_L_s:.2f} L/s</span><br/>
                <span style="font-size: 0.9rem; color: #64748b;">({results.q_max_daily_volume_m3_day:,.1f} m³/día)</span><br/>
                <small>Factor k₁ = {k1:.2f} | Diseño de captación, aducción y PTAP.</small>
            </div>
            """, unsafe_allow_html=True)

        with col_qmh:
            st.markdown(f"""
            <div class="k-card" style="border-left-color: #0d9488;">
                <b>Caudal Máximo Horario (QMH):</b><br/>
                <span style="font-size: 1.5rem; font-weight: 700; color: #0d9488;">{results.q_max_hourly_flow_L_s:.2f} L/s</span><br/>
                <span style="font-size: 0.9rem; color: #64748b;">({results.q_max_hourly_volume_m3_day:,.1f} m³/día)</span><br/>
                <small>Factor k₂ = {k2:.2f} | Diseño de red de distribución y bombeo.</small>
            </div>
            """, unsafe_allow_html=True)

        # Gráfica Comparativa
        st.markdown("#### 📊 Distribución y Comparativa de Caudales")

        chart_tab1, chart_tab2 = st.tabs(["Proporción Doméstica / Industrial", "Comparativa de Caudales (L/s)"])

        with chart_tab1:
            if results.total_volume_m3_day > 0:
                fig_donut = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Demanda Doméstica", "Demanda Industrial"],
                            values=[results.domestic_volume_m3_day, results.industrial_volume_m3_day],
                            hole=0.55,
                            marker_colors=["#0284c7", "#0d9488"],
                            textinfo="label+percent+value",
                            texttemplate="%{label}<br><b>%{value:,.1f} m³/día</b> (%{percent})",
                            hoverinfo="label+value+percent",
                        )
                    ]
                )
                fig_donut.update_layout(
                    showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=280,
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.warning("Ingrese una población o consumo industrial mayor a cero para visualizar la gráfica.")

        with chart_tab2:
            fig_bar = go.Figure(
                data=[
                    go.Bar(
                        name="Caudales (L/s)",
                        x=["Doméstico (Qmd)", "Industrial (Qmd)", "Total Medio (Qmd)", "Máx. Diario (QMD)", "Máx. Horario (QMH)"],
                        y=[
                            results.domestic_flow_L_s,
                            results.industrial_flow_L_s,
                            results.total_flow_L_s,
                            results.q_max_daily_flow_L_s,
                            results.q_max_hourly_flow_L_s,
                        ],
                        marker_color=["#38bdf8", "#2dd4bf", "#0284c7", "#f59e0b", "#ef4444"],
                        text=[
                            f"{results.domestic_flow_L_s:.2f} L/s",
                            f"{results.industrial_flow_L_s:.2f} L/s",
                            f"{results.total_flow_L_s:.2f} L/s",
                            f"{results.q_max_daily_flow_L_s:.2f} L/s",
                            f"{results.q_max_hourly_flow_L_s:.2f} L/s",
                        ],
                        textposition="auto",
                    )
                ]
            )
            fig_bar.update_layout(
                yaxis_title="Caudal (L/s)",
                margin=dict(l=20, r=20, t=20, b=20),
                height=280,
            )
            st.plotly_chart(fig_bar, use_container_width=True)


# =============================================================================
# TAB 2: GESTIÓN DE DEMANDA INDUSTRIAL
# =============================================================================
with tab_industrias:
    st.markdown("### 🏭 Administrador de Industrias y Procesos Productivos")
    st.markdown("Registra y gestiona múltiples industrias o usuarios no domésticos para obtener una demanda industrial desagregada precisa.")

    col_add, col_table = st.columns([1, 1.4], gap="medium")

    with col_add:
        st.markdown("#### ➕ Agregar Nueva Industria")
        with st.form("form_add_industry", clear_on_submit=True):
            ind_nombre = st.text_input("Nombre de la Industria / Razón Social:", value="Nueva Planta")
            ind_metodo = st.selectbox("Método de Estimación:", ["Consumo Específico", "Consumo Directo"])

            if ind_metodo == "Consumo Directo":
                ind_direct_m3 = st.number_input("Consumo Diario (m³/día):", min_value=0.0, value=100.0, step=10.0)
                ind_unidades = 0.0
                ind_esp_val = 0.0
                ind_esp_unit = "m3/unidad"
            else:
                ind_direct_m3 = 0.0
                col_u_form, col_c_form = st.columns(2)
                with col_u_form:
                    ind_unidades = st.number_input("Unidades/día:", min_value=0.0, value=1000.0, step=100.0)
                with col_c_form:
                    ind_esp_unit = st.selectbox("Unidad:", ["L/unidad", "m3/unidad"])
                    ind_esp_val = st.number_input("Consumo esp.:", min_value=0.0, value=5.0, step=0.1)

            submit_add = st.form_submit_button("Agregar Industria a la Lista")
            if submit_add:
                new_rec = IndustrialRecord(
                    name=ind_nombre,
                    mode="direct" if ind_metodo == "Consumo Directo" else "specific",
                    direct_consumption_m3_day=ind_direct_m3,
                    units_per_day=ind_unidades,
                    specific_consumption=ind_esp_val,
                    specific_unit=ind_esp_unit
                )
                st.session_state["industries_list"].append(new_rec)
                st.success(f"¡Industria '{ind_nombre}' agregada con éxito!")
                st.rerun()

    with col_table:
        st.markdown("#### 📋 Listado Actual de Industrias")
        if st.session_state["industries_list"]:
            table_data = []
            for i, ind in enumerate(st.session_state["industries_list"]):
                vol_m3 = ind.calculate_volume_m3_day()
                q_ls = ind.calculate_flow_L_s()
                desc = (
                    f"Directo: {ind.direct_consumption_m3_day:,.1f} m³/día"
                    if ind.mode == "direct"
                    else f"{ind.units_per_day:,.0f} u/d × {ind.specific_consumption:.2f} {ind.specific_unit}"
                )
                table_data.append({
                    "ID": i + 1,
                    "Industria": ind.name,
                    "Modo": "Directo" if ind.mode == "direct" else "Específico",
                    "Detalle": desc,
                    "Volumen (m³/día)": f"{vol_m3:,.2f}",
                    "Caudal (L/s)": f"{q_ls:.3f}"
                })

            df_ind = pd.DataFrame(table_data)
            st.dataframe(df_ind, use_container_width=True, hide_index=True)

            col_del1, col_del2 = st.columns(2)
            with col_del1:
                idx_to_remove = st.selectbox(
                    "Seleccionar industria para eliminar:",
                    options=range(1, len(st.session_state["industries_list"]) + 1),
                    format_func=lambda x: f"ID {x}: {st.session_state['industries_list'][x-1].name}"
                )
                if st.button("🗑️ Eliminar Seleccionada"):
                    st.session_state["industries_list"].pop(idx_to_remove - 1)
                    st.rerun()
            with col_del2:
                if st.button("⚠️ Restablecer a Escenario Inicial"):
                    st.session_state["industries_list"] = list(init_industries)
                    st.rerun()
        else:
            st.warning("No hay industrias en la lista. Agrega una utilizando el formulario a la izquierda.")


# =============================================================================
# TAB 3: FUNDAMENTOS TEÓRICOS Y FÓRMULAS
# =============================================================================
with tab_teoria:
    st.markdown("### 📐 Fundamentación Teórica y Ecuaciones Hidráulicas")
    st.markdown("""
    En el abastecimiento de agua y la hidrología urbana, es crucial diferenciar entre la **Demanda Media Diaria** (utilizada para balances hídricos y concesiones)
    y los **Caudales Máximos** (utilizados para el dimensionamiento hidráulico de infraestructuras).
    """)

    col_t1, col_t2 = st.columns(2, gap="large")

    with col_t1:
        st.markdown("#### 1. Demanda Media Diaria Doméstica ($Q_{md, dom}$)")
        st.markdown("""
        Representa el consumo promedio en 24 horas continuas del componente residencial:
        """)
        st.latex(r"V_{dom} = \frac{P \times D_{bruta}}{1000} \quad \left[\frac{\text{m}^3}{\text{día}}\right]")
        st.latex(r"Q_{md, dom} = \frac{P \times D_{bruta}}{86\,400} = \frac{V_{dom} \times 1000}{86\,400} \quad \left[\frac{\text{L}}{\text{s}}\right]")

        st.markdown("**Consideración de Pérdidas Técnicas / Físicas:**")
        st.latex(r"D_{bruta} = \frac{D_{neta}}{1 - \frac{\%P}{100}} \quad \left[\frac{\text{L}}{\text{hab}\cdot\text{día}}\right]")
        st.caption(r"Donde $P$ = Población de diseño (hab), $D_{neta}$ = Dotación neta, y $\%P$ = Pérdidas físicas en red.")

        st.markdown("---")
        st.markdown("#### 2. Demanda Industrial ($Q_{ind}$)")
        st.markdown("**a) Método de Consumo Directo:**")
        st.latex(r"Q_{ind} = \frac{V_{ind} \times 1000}{86\,400} = \frac{V_{ind}}{86.4} \quad \left[\frac{\text{L}}{\text{s}}\right]")

        st.markdown("**b) Método de Consumo Específico:**")
        st.latex(r"V_{ind} = \sum_{i=1}^n \left( U_i \times c_{e,i} \right) \quad \left[\frac{\text{m}^3}{\text{día}}\right]")
        st.caption("Donde $U_i$ = Unidades producidas por día, $c_{e,i}$ = Consumo de agua por unidad producida.")

    with col_t2:
        st.markdown("#### 3. Equivalencia y Factor de Conversión Hidráulica")
        st.markdown(r"""
        Dado que:
        - $1 \text{ día} = 24 \times 60 \times 60 = 86\,400 \text{ segundos}$.
        - $1 \text{ m}^3 = 1\,000 \text{ Litros}$.
        """)
        st.latex(r"\text{Factor} = \frac{86\,400}{1\,000} = 86.40")
        st.latex(r"V \, [\text{m}^3/\text{día}] = Q \, [\text{L/s}] \times 86.40")
        st.latex(r"Q \, [\text{L/s}] = \frac{V \, [\text{m}^3/\text{día}]}{86.40}")

        st.markdown("---")
        st.markdown("#### 4. Diferenciación Rigurosa: $Q_{md}$ vs. Caudales Máximos")
        st.markdown(r"""
        No se deben confundir ni inventar coeficientes:
        - **Demanda Media Diaria ($Q_{md}$):** Caudal continuo medio en el año. Se usa para:
          - Balance hídrico de la cuenca hidrográfica.
          - Concesión de aguas y permisos ambientales ante autoridades hídricas.
          - Estimación de volúmenes anuales y facturación.
        - **Caudal Máximo Diario ($Q_{MD} = k_1 \cdot Q_{md}$):**
          - Caudal del día de mayor consumo en el año.
          - Se usa para dimensionar: **Captaciones, Desarenadores, Aducciones, Plantas de Tratamiento (PTAP) y Tanques de Almacenamiento**.
        - **Caudal Máximo Horario ($Q_{MH} = k_2 \cdot Q_{MD}$):**
          - Caudal en la hora pico del día de máximo consumo.
          - Se usa para dimensionar: **Red de distribución, redes matrices y equipos de bombeo directo a red**.
        """)


# =============================================================================
# TAB 4: EXPORTACIÓN Y REPORTES
# =============================================================================
with tab_export:
    st.markdown("### 📥 Generación y Exportación de Informes Técnicos")
    st.markdown("Descarga los resultados en formatos profesionales listos para memorias de cálculo, expedientes técnicos o modelos hidráulicos (EPANET).")

    # Tabla resumen general
    summary_data = [
        {"Parámetro": "Población de Diseño", "Unidad": "habitantes", "Valor": f"{results.domestic_population:,}"},
        {"Parámetro": "Dotación Neta", "Unidad": "L/hab·día", "Valor": f"{results.domestic_endowment_net:.2f}"},
        {"Parámetro": "Pérdidas Técnicas Estimadas", "Unidad": "%", "Valor": f"{results.domestic_losses_pct:.1f}%"},
        {"Parámetro": "Dotación Bruta de Diseño", "Unidad": "L/hab·día", "Valor": f"{results.domestic_endowment_gross:.2f}"},
        {"Parámetro": "Demanda Media Doméstica (Volumen)", "Unidad": "m³/día", "Valor": f"{results.domestic_volume_m3_day:,.2f}"},
        {"Parámetro": "Demanda Media Doméstica (Caudal)", "Unidad": "L/s", "Valor": f"{results.domestic_flow_L_s:.3f}"},
        {"Parámetro": "Demanda Media Industrial (Volumen)", "Unidad": "m³/día", "Valor": f"{results.industrial_volume_m3_day:,.2f}"},
        {"Parámetro": "Demanda Media Industrial (Caudal)", "Unidad": "L/s", "Valor": f"{results.industrial_flow_L_s:.3f}"},
        {"Parámetro": "Demanda Media Diaria Total (Qmd Volumen)", "Unidad": "m³/día", "Valor": f"{results.total_volume_m3_day:,.2f}"},
        {"Parámetro": "Demanda Media Diaria Total (Qmd Caudal)", "Unidad": "L/s", "Valor": f"{results.total_flow_L_s:.3f}"},
        {"Parámetro": "Participación Doméstica", "Unidad": "%", "Valor": f"{results.domestic_pct:.1f}%"},
        {"Parámetro": "Participación Industrial", "Unidad": "%", "Valor": f"{results.industrial_pct:.1f}%"},
        {"Parámetro": "Coeficiente Variación Diaria (k1)", "Unidad": "adimensional", "Valor": f"{results.k1_coefficient:.2f}"},
        {"Parámetro": "Coeficiente Variación Horaria (k2)", "Unidad": "adimensional", "Valor": f"{results.k2_coefficient:.2f}"},
        {"Parámetro": "Caudal Máximo Diario (QMD)", "Unidad": "L/s", "Valor": f"{results.q_max_daily_flow_L_s:.3f}"},
        {"Parámetro": "Caudal Máximo Horario (QMH)", "Unidad": "L/s", "Valor": f"{results.q_max_hourly_flow_L_s:.3f}"},
    ]
    df_summary = pd.DataFrame(summary_data)

    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    col_exp1, col_exp2, col_exp3 = st.columns(3)

    # 1. Exportar a CSV
    with col_exp1:
        csv_buffer = io.StringIO()
        df_summary.to_csv(csv_buffer, index=False, encoding="utf-8-sig")
        st.download_button(
            label="📄 Descargar Resumen en CSV",
            data=csv_buffer.getvalue(),
            file_name="demanda_agua_resumen.csv",
            mime="text/csv"
        )

    # 2. Exportar a Excel con múltiples hojas
    with col_exp2:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_summary.to_excel(writer, sheet_name="Resumen_General", index=False)
            if results.industrial_details:
                df_ind_exp = pd.DataFrame(results.industrial_details)
                df_ind_exp.to_excel(writer, sheet_name="Detalle_Industrial", index=False)
        st.download_button(
            label="📊 Descargar Libro en Excel (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name="memoria_demanda_agua.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # 3. Exportar Memoria Técnica en Markdown / Texto
    with col_exp3:
        report_text = f"""================================================================================
MEMORIA DE CÁLCULO DE DEMANDA DE AGUA POTABLE Y DE USO INDUSTRIAL
================================================================================
Fecha de generación: 2026-11-23
Herramienta: Calculadora de Demanda Doméstica e Industrial de Agua

1. DEMANDA DOMÉSTICA:
--------------------------------------------------------------------------------
- Población de diseño: {results.domestic_population:,} habitantes
- Dotación neta de agua: {results.domestic_endowment_net:.2f} L/hab·día
- Pérdidas técnicas en red: {results.domestic_losses_pct:.1f} %
- Dotación bruta de cálculo: {results.domestic_endowment_gross:.2f} L/hab·día
- Caudal medio doméstico (Qmd_dom): {results.domestic_flow_L_s:.3f} L/s ({results.domestic_volume_m3_day:,.2f} m³/día)

2. DEMANDA INDUSTRIAL:
--------------------------------------------------------------------------------
- Caudal medio industrial (Qmd_ind): {results.industrial_flow_L_s:.3f} L/s ({results.industrial_volume_m3_day:,.2f} m³/día)
- Número de procesos o industrias modeladas: {len(results.industrial_details)}

3. BALANCE TOTAL DE DEMANDA MEDIA DIARIA (Qmd):
--------------------------------------------------------------------------------
- Caudal total medio diario (Qmd): {results.total_flow_L_s:.3f} L/s
- Volumen total medio diario: {results.total_volume_m3_day:,.2f} m³/día
- Distribución: {results.domestic_pct:.1f}% Doméstico | {results.industrial_pct:.1f}% Industrial

4. CAUDALES MÁXIMOS PARA DIMENSIONAMIENTO DE OBRAS CIVILES:
--------------------------------------------------------------------------------
- Coeficiente de variación diaria (k1): {results.k1_coefficient:.2f}
- Coeficiente de variación horaria (k2): {results.k2_coefficient:.2f}
- Caudal Máximo Diario (QMD): {results.q_max_daily_flow_L_s:.3f} L/s ({results.q_max_daily_volume_m3_day:,.2f} m³/día)
  * Destinado a: Captaciones, aducciones, PTAP y tanques de almacenamiento.
- Caudal Máximo Horario (QMH): {results.q_max_hourly_flow_L_s:.3f} L/s ({results.q_max_hourly_volume_m3_day:,.2f} m³/día)
  * Destinado a: Red de distribución y bombeo de red.

================================================================================
"""
        st.download_button(
            label="📝 Descargar Memoria Técnica (.txt)",
            data=report_text,
            file_name="memoria_tecnica_demanda.txt",
            mime="text/plain"
        )
