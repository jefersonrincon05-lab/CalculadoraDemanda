"""
Calculadora de Demanda Doméstica e Industrial de Agua
Versión 2.0 - Suite Profesional de Ingeniería Sanitaria e Hidráulica
Con Auditoría Casilla por Casilla, Validación Estricta y Nueva Interfaz Moderna
"""

import io
from typing import List, Dict, Any, Optional
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
    ValidationReport,
)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Calculadora de Demanda de Agua | Ingeniería Hidráulica",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# ESTILOS CSS AVANZADOS Y MODERNIZACIÓN DE LA INTERFAZ
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Estilos globales y paleta de colores de ingeniería */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Encabezado principal tipo SaaS técnico */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0369a1 100%);
        border-radius: 16px;
        padding: 1.8rem 2.2rem;
        color: #ffffff;
        margin-bottom: 1.6rem;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-top: 0.5rem;
        margin-bottom: 0.8rem;
        font-weight: 400;
        max-width: 900px;
    }
    .hero-pills {
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        margin-top: 0.8rem;
    }
    .hero-pill {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        padding: 0.3rem 0.8rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }

    /* Tarjetas de parámetros y módulos */
    .module-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.4rem;
        margin-bottom: 1.3rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .module-card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.07);
    }
    .module-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Badges de estado de validación */
    .badge-valid {
        background-color: #dcfce7;
        color: #15803d;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #bbf7d0;
    }
    .badge-warn {
        background-color: #fef3c7;
        color: #b45309;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #fde68a;
    }
    .badge-error {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #fecaca;
    }

    /* Tarjetas métricas premium */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        border-top: 4px solid #0284c7;
    }
    .kpi-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 0.85rem;
        color: #475569;
        margin-top: 0.3rem;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Contenedor de auditoría */
    .audit-box {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# BENCHMARKS DE CONSUMO ESPECÍFICO INDUSTRIAL
# -----------------------------------------------------------------------------
BENCHMARK_INDUSTRIAS = {
    "Personalizada": {"unit": "m3/unidad", "consumo": 1.0, "horas": 24.0},
    "Bebidas y Refrescos (L de agua / L bebida)": {"unit": "L/unidad", "consumo": 2.5, "horas": 16.0},
    "Cervecería Industrial (L agua / L cerveza)": {"unit": "L/unidad", "consumo": 4.5, "horas": 24.0},
    "Planta Láctea / Pasteurizadora (L agua / L leche procesada)": {"unit": "L/unidad", "consumo": 2.0, "horas": 16.0},
    "Matadero Bovino (L agua / animal sacrificado)": {"unit": "L/unidad", "consumo": 1200.0, "horas": 8.0},
    "Matadero Porcino (L agua / animal sacrificado)": {"unit": "L/unidad", "consumo": 450.0, "horas": 8.0},
    "Planta Avícola (L agua / ave procesada)": {"unit": "L/unidad", "consumo": 25.0, "horas": 12.0},
    "Industria Textil - Tintorería (L agua / kg tela)": {"unit": "L/unidad", "consumo": 110.0, "horas": 16.0},
    "Fabricación de Papel y Cartón (m³ agua / ton papel)": {"unit": "m3/unidad", "consumo": 25.0, "horas": 24.0},
    "Central de Concreto Hidráulico (m³ agua / m³ concreto)": {"unit": "m3/unidad", "consumo": 0.20, "horas": 10.0},
    "Curtiduría de Pieles (m³ agua / ton piel)": {"unit": "m3/unidad", "consumo": 35.0, "horas": 12.0},
}


# -----------------------------------------------------------------------------
# BARRA LATERAL (SIDEBAR): PREAJUSTES Y COEFICIENTES DE PICO
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎛️ Control de Escenarios")
    
    scenario = st.selectbox(
        "Cargar Escenario Modelo:",
        options=[
            "Personalizado",
            "Municipio Intermedio (45,000 hab + Agroindustria)",
            "Población Rural (4,500 hab + Lácteos)",
            "Zona Urbana - Industrial (120,000 hab + Textil/Bebidas)",
        ],
        index=0,
        help="Carga configuraciones típicas validadas para agilizar comparaciones técnicas."
    )

    st.markdown("---")
    st.markdown("### ⚡ Coeficientes de Variación (Picos)")
    st.caption("Diferencian la **Demanda Media Diaria** de los **Caudales de Diseño**:")

    k1_val = st.number_input(
        "Coeficiente Diario (k₁) [QMD = k₁ · Qmd]:",
        min_value=1.00,
        max_value=2.00,
        value=1.20,
        step=0.01,
        format="%.2f",
        help="Rango normativo sanitario típico: 1.15 a 1.30. Por definición física k₁ ≥ 1.00."
    )

    k2_val = st.number_input(
        "Coeficiente Horario (k₂) [QMH = k₂ · QMD]:",
        min_value=1.00,
        max_value=3.00,
        value=1.50,
        step=0.01,
        format="%.2f",
        help="Rango normativo sanitario típico: 1.40 a 1.60. Por definición física k₂ ≥ 1.00."
    )

    apply_k_to_industrial = st.checkbox(
        "Aplicar factores k₁ y k₂ a la industria",
        value=False,
        help="Recomendación técnica: Dejar desmarcado si la industria dispone de reservorios de compensación propios o régimen uniforme."
    )

    st.markdown("---")
    st.markdown("### 🛡️ Estado del Motor Hidráulico")
    peak_validation = WaterDemandEngine.validate_peak_factors(k1_val, k2_val)
    if peak_validation.is_valid:
        if peak_validation.warnings:
            for w in peak_validation.warnings:
                st.warning(f"⚠️ {w}")
        else:
            st.success("✅ Factores k₁ y k₂ en rango técnico óptimo.")
    else:
        for err in peak_validation.errors:
            st.error(f"❌ {err}")


# Configurar variables por escenario
if scenario == "Municipio Intermedio (45,000 hab + Agroindustria)":
    init_pop, init_dot, init_losses = 45000, 140.0, 20.0
    init_industries = [
        IndustrialRecord("Planta Láctea Municipal", mode="specific", units_per_day=40000.0, specific_consumption=2.0, specific_unit="L/unidad", operating_hours_per_day=16.0),
        IndustrialRecord("Bebidas del Valle", mode="specific", units_per_day=35000.0, specific_consumption=2.5, specific_unit="L/unidad", operating_hours_per_day=16.0),
        IndustrialRecord("Frigorífico Bovino", mode="specific", units_per_day=250.0, specific_consumption=1200.0, specific_unit="L/unidad", operating_hours_per_day=8.0),
    ]
elif scenario == "Población Rural (4,500 hab + Lácteos)":
    init_pop, init_dot, init_losses = 4500, 110.0, 15.0
    init_industries = [
        IndustrialRecord("Quesería Artesanal", mode="specific", units_per_day=5000.0, specific_consumption=2.5, specific_unit="L/unidad", operating_hours_per_day=8.0),
    ]
elif scenario == "Zona Urbana - Industrial (120,000 hab + Textil/Bebidas)":
    init_pop, init_dot, init_losses = 120000, 160.0, 25.0
    init_industries = [
        IndustrialRecord("Parque Cervecero", mode="specific", units_per_day=150000.0, specific_consumption=4.5, specific_unit="L/unidad", operating_hours_per_day=24.0),
        IndustrialRecord("Tintorería Textil", mode="specific", units_per_day=8000.0, specific_consumption=110.0, specific_unit="L/unidad", operating_hours_per_day=16.0),
        IndustrialRecord("Papelera Industrial", mode="specific", units_per_day=60.0, specific_consumption=25.0, specific_unit="m3/unidad", operating_hours_per_day=24.0),
        IndustrialRecord("Zona Franca Logística", mode="direct", direct_consumption_m3_day=450.0, operating_hours_per_day=24.0),
    ]
else:
    init_pop, init_dot, init_losses = 25000, 135.0, 18.0
    init_industries = [
        IndustrialRecord("Industria Agroalimentaria", mode="direct", direct_consumption_m3_day=350.0, operating_hours_per_day=16.0),
    ]

if "industries_list" not in st.session_state or st.session_state.get("last_scenario") != scenario:
    st.session_state["industries_list"] = init_industries
    st.session_state["last_scenario"] = scenario


# -----------------------------------------------------------------------------
# HERO BANNER PRINCIPAL (NUEVA INTERFAZ MODERNA)
# -----------------------------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">💧 Calculadora de Demanda Doméstica e Industrial de Agua</div>
    <div class="hero-subtitle">
        Plataforma técnica de ingeniería hidráulica y saneamiento urbano para cálculo riguroso de Demanda Media Diaria (Qmd),
        caudales de pico (QMD, QMH), auditoría matemática casilla por casilla y validación estricta de parámetros normativos.
    </div>
    <div class="hero-pills">
        <span class="hero-pill">⚙️ Conversión Exacta: 1 L/s = 86.40 m³/día</span>
        <span class="hero-pill">🛡️ Validación Anti-Incoherencias Activa</span>
        <span class="hero-pill">🔍 Auditoría Casilla por Casilla</span>
        <span class="hero-pill">📊 Visualizaciones Plotly</span>
        <span class="hero-pill">📑 Exportación Multiformato</span>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# NAVEGACIÓN PRINCIPAL EN PESTAÑAS
# -----------------------------------------------------------------------------
tab_main, tab_audit, tab_ind_mgr, tab_theory, tab_export = st.tabs([
    "🎛️ Centro de Simulación y Resultados",
    "🔍 Auditoría Matemática Casilla por Casilla",
    "🏭 Gestión de Industrias y Caudal en Turno",
    "📐 Fundamentos Teóricos y Fórmulas",
    "📥 Exportación de Memorias y Datos",
])


# =============================================================================
# TAB 1: SIMULACIÓN Y RESULTADOS (REDiseño MODERNO)
# =============================================================================
with tab_main:
    col_inputs, col_outputs = st.columns([1.1, 1.4], gap="large")

    with col_inputs:
        # --- MÓDULO DOMÉSTICO ---
        st.markdown("""
        <div class="module-card">
            <div class="module-header">🏠 1. Módulo de Demanda Doméstica</div>
            <p style="color:#64748b; font-size:0.88rem; margin-bottom:1rem;">
                Ingreso de población proyectada, dotación neta per cápita y pérdidas de red.
            </p>
        """, unsafe_allow_html=True)

        col_p, col_d = st.columns(2)
        with col_p:
            input_pop = st.number_input(
                "Población de Diseño (hab):",
                min_value=1,
                max_value=50_000_000,
                value=int(init_pop),
                step=500,
                help="Número de habitantes proyectados a abastecer en el horizonte de diseño (debe ser ≥ 1)."
            )

        with col_d:
            input_dot = st.number_input(
                "Dotación Neta (L/hab·día):",
                min_value=25.0,
                max_value=500.0,
                value=float(init_dot),
                step=5.0,
                format="%.1f",
                help="Consumo neto por habitante al día. Rango estricto admitido: 25.0 a 500.0 L/hab·día (mínimo vital OMS)."
            )

        # Validación visual inmediata de dotación
        if input_dot < 70.0:
            st.markdown('<span class="badge-warn">⚠️ Dotación muy restrictiva (nivel rural básico)</span>', unsafe_allow_html=True)
        elif input_dot > 250.0:
            st.markdown('<span class="badge-warn">⚠️ Dotación elevada (clima cálido o alto estrato)</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-valid">✅ Dotación en rango normativo estándar (70 - 250 L/hab·día)</span>', unsafe_allow_html=True)

        input_losses = st.slider(
            "Pérdidas Técnicas / Físicas en Red (%):",
            min_value=0.0,
            max_value=55.0,
            value=float(init_losses),
            step=0.5,
            help="Agua no contabilizada (ANC) debida a fugas. Máximo admisible: 55% para evitar divergencias numéricas."
        )

        # Calificación de eficiencia de pérdidas
        if input_losses < 15.0:
            st.markdown('<span class="badge-valid">🟢 Excelente eficiencia técnica de red (< 15%)</span>', unsafe_allow_html=True)
        elif input_losses <= 30.0:
            st.markdown('<span class="badge-valid">🔵 Eficiencia técnica aceptable (15% - 30%)</span>', unsafe_allow_html=True)
        elif input_losses <= 45.0:
            st.markdown('<span class="badge-warn">🟡 Pérdidas elevadas: requiere detección de fugas (30% - 45%)</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge-error">🔴 Pérdidas críticas en red (> 45%)</span>', unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # --- MÓDULO INDUSTRIAL ---
        st.markdown("""
        <div class="module-card">
            <div class="module-header">🏭 2. Módulo de Demanda Industrial</div>
            <p style="color:#64748b; font-size:0.88rem; margin-bottom:1rem;">
                Configura el consumo mediante ingreso directo, consumo específico o lista consolidada.
            </p>
        """, unsafe_allow_html=True)

        ind_input_mode = st.radio(
            "Modalidad de Evaluación Industrial:",
            options=[
                "Consumo Directo (m³/día)",
                "Consumo Específico por Producto",
                "Inventario Multiproceso (Recomendado)",
            ],
            index=2 if len(st.session_state["industries_list"]) > 1 else 0
        )

        active_industries: List[IndustrialRecord] = []

        if ind_input_mode == "Consumo Directo (m³/día)":
            c_direct = st.number_input(
                "Consumo Industrial Diario (m³/día):",
                min_value=0.0,
                max_value=500_000.0,
                value=350.0,
                step=10.0,
                help="Volumen total demandado por industrias en 24 horas."
            )
            c_hours = st.slider("Horas de operación diaria fabril:", min_value=1.0, max_value=24.0, value=16.0, step=1.0)
            active_industries = [IndustrialRecord(name="Consolidado Industrial", mode="direct", direct_consumption_m3_day=c_direct, operating_hours_per_day=c_hours)]

        elif ind_input_mode == "Consumo Específico por Producto":
            ind_preset_key = st.selectbox("Giro Industrial o Tipología:", options=list(BENCHMARK_INDUSTRIAS.keys()))
            b_data = BENCHMARK_INDUSTRIAS[ind_preset_key]

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                u_qty = st.number_input("Unidades producidas al día:", min_value=0.0, value=30000.0 if "L" in b_data["unit"] else 50.0, step=100.0)
            with col_u2:
                u_unit = st.selectbox("Unidad de consumo específico:", ["L/unidad", "m3/unidad"], index=0 if b_data["unit"] == "L/unidad" else 1)
                u_rate = st.number_input(f"Consumo específico ({u_unit}):", min_value=0.0, value=float(b_data["consumo"]), step=0.1, format="%.4f")

            h_oper = st.slider("Horas diarias de actividad del proceso:", min_value=1.0, max_value=24.0, value=float(b_data["horas"]), step=1.0)
            active_industries = [IndustrialRecord(name=ind_preset_key, mode="specific", units_per_day=u_qty, specific_consumption=u_rate, specific_unit=u_unit, operating_hours_per_day=h_oper)]

        else:
            n_ind = len(st.session_state["industries_list"])
            st.info(f"📋 Se están evaluando **{n_ind} industria(s)** configuradas. Puedes añadir, modificar o remover en la pestaña 'Gestión de Industrias'.")
            active_industries = st.session_state["industries_list"]

        st.markdown("</div>", unsafe_allow_html=True)

    # --- INSTANCIACIÓN Y CÁLCULO CONTROLADO ---
    calculation_success = False
    calc_error_msg = ""
    dom_obj = DomesticDemandInput(population=input_pop, endowment_L_hab_day=input_dot, technical_losses_pct=input_losses)

    try:
        results: WaterDemandResults = WaterDemandEngine.calculate_total_system_demand(
            domestic_input=dom_obj,
            industrial_records=active_industries,
            k1=k1_val,
            k2=k2_val,
            apply_k_to_industrial=apply_k_to_industrial
        )
        calculation_success = True
    except Exception as ex:
        calculation_success = False
        calc_error_msg = str(ex)

    with col_outputs:
        if not calculation_success:
            st.markdown(f"""
            <div class="module-card" style="border-left: 5px solid #ef4444; background: #fff5f5;">
                <div class="module-header" style="color: #b91c1c;">🚫 Cálculo Bloqueado por Datos Incoherentes</div>
                <p style="color: #7f1d1d; font-size: 0.95rem;">
                    El motor hidráulico ha detectado inconsistencias que impiden generar resultados válidos:
                </p>
                <div style="background: #ffffff; padding: 0.8rem; border-radius: 8px; border: 1px solid #fecaca; font-family: monospace; font-size: 0.85rem; color: #991b1b;">
                    {calc_error_msg}
                </div>
                <p style="margin-top: 0.8rem; font-size: 0.85rem; color: #64748b;">
                    Por favor, corrige los valores en los campos señalados para reanudar el cálculo.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # TABLERO DE RESULTADOS PRINCIPALES
            st.markdown("### 📊 Resultados Hidráulicos Consolidados")

            # Fila 1: KPIs Principales (Doméstico, Industrial, Total Qmd)
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-card" style="border-top-color: #0284c7;">
                    <div class="kpi-title">🏠 Demanda Doméstica</div>
                    <div class="kpi-value">{results.domestic_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                    <div class="kpi-sub">{results.domestic_volume_m3_day:,.1f} m³/día</div>
                    <div style="font-size:0.75rem; color:#64748b; margin-top:0.2rem;">D. Bruta: {results.domestic_endowment_gross:.1f} L/hab·d</div>
                </div>
                <div class="kpi-card" style="border-top-color: #0d9488;">
                    <div class="kpi-title">🏭 Demanda Industrial</div>
                    <div class="kpi-value">{results.industrial_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                    <div class="kpi-sub">{results.industrial_volume_m3_day:,.1f} m³/día</div>
                    <div style="font-size:0.75rem; color:#64748b; margin-top:0.2rem;">{len(results.industrial_details)} proceso(s) activos</div>
                </div>
                <div class="kpi-card" style="border-top-color: #16a34a; background: #f0fdf4;">
                    <div class="kpi-title" style="color:#15803d;">💧 Demanda Media Total (Qmd)</div>
                    <div class="kpi-value" style="color:#15803d;">{results.total_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                    <div class="kpi-sub" style="color:#166534;">{results.total_volume_m3_day:,.1f} m³/día</div>
                    <div style="font-size:0.75rem; color:#15803d; margin-top:0.2rem;">Base Concesión / Balances</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Fila 2: Caudales Máximos de Diseño (QMD y QMH)
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-card" style="border-top-color: #f59e0b; background: #fffbeb;">
                    <div class="kpi-title" style="color:#b45309;">⚡ Caudal Máximo Diario (QMD)</div>
                    <div class="kpi-value" style="color:#b45309;">{results.q_max_daily_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                    <div class="kpi-sub" style="color:#78350f;">{results.q_max_daily_volume_m3_day:,.1f} m³/día</div>
                    <div style="font-size:0.75rem; color:#92400e; margin-top:0.3rem;">
                        <b>Diseño:</b> Captación, Aducción, PTAP y Tanques (k₁ = {results.k1_coefficient:.2f})
                    </div>
                </div>
                <div class="kpi-card" style="border-top-color: #ef4444; background: #fef2f2;">
                    <div class="kpi-title" style="color:#b91c1c;">🔥 Caudal Máximo Horario (QMH)</div>
                    <div class="kpi-value" style="color:#b91c1c;">{results.q_max_hourly_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                    <div class="kpi-sub" style="color:#7f1d1d;">{results.q_max_hourly_volume_m3_day:,.1f} m³/día</div>
                    <div style="font-size:0.75rem; color:#991b1b; margin-top:0.3rem;">
                        <b>Diseño:</b> Red de Distribución y Bombeo de Red (k₂ = {results.k2_coefficient:.2f})
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Visualizaciones Plotly Mejoradas
            chart_col1, chart_col2 = st.tabs(["📊 Comparativa de Caudales (L/s)", "🍩 Distribución Porcentual (%)"])

            with chart_col1:
                fig_bars = go.Figure()
                fig_bars.add_trace(go.Bar(
                    x=["Doméstico (Qmd)", "Industrial (Qmd)", "Medio Total (Qmd)", "Máx. Diario (QMD)", "Máx. Horario (QMH)"],
                    y=[
                        results.domestic_flow_L_s,
                        results.industrial_flow_L_s,
                        results.total_flow_L_s,
                        results.q_max_daily_flow_L_s,
                        results.q_max_hourly_flow_L_s
                    ],
                    marker=dict(
                        color=["#38bdf8", "#2dd4bf", "#0284c7", "#f59e0b", "#ef4444"],
                        line=dict(color="#0f172a", width=1)
                    ),
                    text=[
                        f"{results.domestic_flow_L_s:.2f} L/s",
                        f"{results.industrial_flow_L_s:.2f} L/s",
                        f"{results.total_flow_L_s:.2f} L/s",
                        f"{results.q_max_daily_flow_L_s:.2f} L/s",
                        f"{results.q_max_hourly_flow_L_s:.2f} L/s"
                    ],
                    textposition="outside"
                ))
                fig_bars.update_layout(
                    height=320,
                    margin=dict(l=20, r=20, t=25, b=20),
                    yaxis=dict(title="Caudal de Diseño (L/s)", gridcolor="#f1f5f9"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif")
                )
                st.plotly_chart(fig_bars, use_container_width=True)

            with chart_col2:
                if results.total_volume_m3_day > 0:
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=["Demanda Doméstica", "Demanda Industrial"],
                        values=[results.domestic_volume_m3_day, results.industrial_volume_m3_day],
                        hole=0.58,
                        marker_colors=["#0284c7", "#0d9488"],
                        textinfo="label+percent",
                        texttemplate="<b>%{label}</b><br>%{percent} (%{value:,.1f} m³/d)",
                        hoverinfo="label+value+percent",
                    )])
                    fig_donut.update_layout(
                        showlegend=False,
                        height=320,
                        margin=dict(l=10, r=10, t=10, b=10),
                        font=dict(family="Inter, sans-serif")
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)


# =============================================================================
# TAB 2: AUDITORÍA MATEMÁTICA CASILLA POR CASILLA
# =============================================================================
with tab_audit:
    st.markdown("### 🔍 Matriz de Auditoría Casilla por Casilla")
    st.markdown("""
    Esta tabla evalúa cada celda de entrada del proyecto. Garantiza la **trazabilidad dimensional**,
    el cumplimiento de los **rangos técnicos admisibles** y previene la incorporación de datos incoherentes o no normativos.
    """)

    if calculation_success and results.audit_table:
        df_audit = pd.DataFrame(results.audit_table)
        st.dataframe(df_audit, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 🧮 Demostración y Trazabilidad Paso a Paso del Cálculo")

        trace_p = results.domestic_population
        trace_dn = results.domestic_endowment_net
        trace_loss = results.domestic_losses_pct
        trace_db = results.domestic_endowment_gross
        trace_vdom = results.domestic_volume_m3_day
        trace_qdom = results.domestic_flow_L_s
        trace_vind = results.industrial_volume_m3_day
        trace_qind = results.industrial_flow_L_s

        st.markdown(f"""
        <div class="audit-box">
            <h5 style="color:#0f172a; margin-bottom:0.5rem;">Paso 1: Cálculo de Dotación Bruta</h5>
            <code>D_bruta = D_neta / (1 - %Pérdidas/100) = {trace_dn:.2f} / (1 - {trace_loss/100:.4f}) = <b>{trace_db:.4f} L/hab·día</b></code>
            <br/><br/>
            <h5 style="color:#0f172a; margin-bottom:0.5rem;">Paso 2: Cálculo del Volumen Doméstico Diario</h5>
            <code>V_dom = (Población × D_bruta) / 1000 = ({trace_p:,} × {trace_db:.4f}) / 1000 = <b>{trace_vdom:,.4f} m³/día</b></code>
            <br/><br/>
            <h5 style="color:#0f172a; margin-bottom:0.5rem;">Paso 3: Conversión de Volumen Doméstico a Caudal Continuo (24 horas)</h5>
            <code>Q_dom = V_dom / 86.40 = {trace_vdom:,.4f} / 86.40 = <b>{trace_qdom:.4f} L/s</b></code>
            <br/><br/>
            <h5 style="color:#0f172a; margin-bottom:0.5rem;">Paso 4: Conversión y Agregación Industrial</h5>
            <code>Q_ind = V_ind / 86.40 = {trace_vind:,.4f} / 86.40 = <b>{trace_qind:.4f} L/s</b></code>
            <br/><br/>
            <h5 style="color:#0f172a; margin-bottom:0.5rem;">Paso 5: Balance Total de Demanda Media Diaria (Qmd)</h5>
            <code>Qmd_total = Q_dom + Q_ind = {trace_qdom:.4f} + {trace_qind:.4f} = <b>{results.total_flow_L_s:.4f} L/s</b> ({results.total_volume_m3_day:,.2f} m³/día)</code>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No se puede generar la auditoría matemática debido a errores en los campos de entrada.")


# =============================================================================
# TAB 3: GESTIÓN DE INDUSTRIAS Y CAUDAL EN TURNO
# =============================================================================
with tab_ind_mgr:
    st.markdown("### 🏭 Administrador de Procesos Industriales y Caudal en Turno")
    st.markdown("""
    En ingeniería sanitaria, si una industria trabaja en turnos restringidos (ej. 8 horas al día),
    su tubería de acometida debe dimensionarse para el **Caudal en Turno Operativo ($Q_{op}$)** y no para el promedio de 24 horas.
    """)

    col_add_ind, col_list_ind = st.columns([1, 1.4], gap="large")

    with col_add_ind:
        st.markdown("#### ➕ Registrar Nueva Industria")
        with st.form("form_new_industry", clear_on_submit=True):
            new_name = st.text_input("Razón Social o Denominación:", value="Fábrica de Alimentos")
            new_method = st.selectbox("Método:", ["Consumo Específico", "Consumo Directo"])

            if new_method == "Consumo Directo":
                new_direct_val = st.number_input("Consumo total (m³/día):", min_value=0.0, value=150.0, step=10.0)
                new_u_qty = 0.0
                new_u_rate = 0.0
                new_u_unit = "m3/unidad"
            else:
                new_direct_val = 0.0
                col_u_sub1, col_u_sub2 = st.columns(2)
                with col_u_sub1:
                    new_u_qty = st.number_input("Unidades/día:", min_value=0.0, value=2000.0, step=100.0)
                with col_u_sub2:
                    new_u_unit = st.selectbox("Unidad:", ["L/unidad", "m3/unidad"])
                    new_u_rate = st.number_input("Consumo por unidad:", min_value=0.0, value=25.0, step=0.1)

            new_hours = st.slider("Horas de operación al día (Hop):", min_value=1.0, max_value=24.0, value=8.0, step=1.0)
            btn_add = st.form_submit_button("Guardar Industria en el Inventario")

            if btn_add:
                try:
                    new_ind_rec = IndustrialRecord(
                        name=new_name,
                        mode="direct" if new_method == "Consumo Directo" else "specific",
                        direct_consumption_m3_day=new_direct_val,
                        units_per_day=new_u_qty,
                        specific_consumption=new_u_rate,
                        specific_unit=new_u_unit,
                        operating_hours_per_day=new_hours
                    )
                    rep_ind = new_ind_rec.validate_strict()
                    if rep_ind.is_valid:
                        st.session_state["industries_list"].append(new_ind_rec)
                        st.success(f"✅ Industria '{new_name}' registrada exitosamente.")
                        st.rerun()
                    else:
                        st.error("; ".join(rep_ind.errors))
                except Exception as e:
                    st.error(f"Error al registrar: {e}")

    with col_list_ind:
        st.markdown("#### 📋 Inventario Actual de Industrias")
        if st.session_state["industries_list"]:
            ind_rows = []
            for idx, item in enumerate(st.session_state["industries_list"]):
                vol_m3 = item.calculate_volume_m3_day()
                q_24h = item.calculate_flow_L_s()
                q_op = item.calculate_operating_flow_L_s()
                ind_rows.append({
                    "ID": idx + 1,
                    "Industria": item.name,
                    "Método": "Directo" if item.mode == "direct" else "Específico",
                    "Horas Op.": f"{item.operating_hours_per_day:.0f} h/día",
                    "Volumen (m³/día)": f"{vol_m3:,.2f}",
                    "Qmd 24h (L/s)": f"{q_24h:.3f}",
                    "Q Turno Operativo (L/s)": f"{q_op:.3f}"
                })

            df_ind_view = pd.DataFrame(ind_rows)
            st.dataframe(df_ind_view, use_container_width=True, hide_index=True)

            col_btn_d1, col_btn_d2 = st.columns(2)
            with col_btn_d1:
                sel_del = st.selectbox(
                    "Seleccionar elemento a borrar:",
                    options=range(1, len(st.session_state["industries_list"]) + 1),
                    format_func=lambda x: f"ID {x}: {st.session_state['industries_list'][x-1].name}"
                )
                if st.button("🗑️ Eliminar Industria"):
                    st.session_state["industries_list"].pop(sel_del - 1)
                    st.rerun()

            with col_btn_d2:
                if st.button("🔄 Reiniciar Lista a Valores de Escenario"):
                    st.session_state["industries_list"] = list(init_industries)
                    st.rerun()
        else:
            st.warning("No hay industrias en la lista activa.")


# =============================================================================
# TAB 4: FUNDAMENTOS TEÓRICOS Y FÓRMULAS
# =============================================================================
with tab_theory:
    st.markdown("### 📐 Fundamentación Teórica y Ecuaciones Hidráulicas")
    st.markdown("""
    El cálculo del abastecimiento de agua se basa en el balance de masas y la continuidad hidráulica.
    A continuación se detallan las ecuaciones normativas y la derivación de constantes.
    """)

    col_theo1, col_theo2 = st.columns(2, gap="large")

    with col_theo1:
        st.markdown("#### 1. Demanda Media Diaria Doméstica ($Q_{md, dom}$)")
        st.latex(r"D_{bruta} = \frac{D_{neta}}{1 - \frac{\%P}{100}} \quad \left[\frac{\text{L}}{\text{hab}\cdot\text{día}}\right]")
        st.latex(r"V_{dom} = \frac{P \times D_{bruta}}{1\,000} \quad \left[\frac{\text{m}^3}{\text{día}}\right]")
        st.latex(r"Q_{md, dom} = \frac{P \times D_{bruta}}{86\,400} = \frac{V_{dom} \times 1\,000}{86\,400} = \frac{V_{dom}}{86.40} \quad \left[\frac{\text{L}}{\text{s}}\right]")

        st.markdown("---")
        st.markdown("#### 2. Demanda Media Diaria Industrial ($Q_{ind}$)")
        st.latex(r"V_{ind} = \sum_{i=1}^n (U_i \times c_{e,i}) \quad \left[\frac{\text{m}^3}{\text{día}}\right]")
        st.latex(r"Q_{md, ind} = \frac{V_{ind}}{86.40} \quad \left[\frac{\text{L}}{\text{s}}\right]")
        st.latex(r"Q_{op, ind} = \frac{V_{ind} \times 1\,000}{H_{op} \times 3\,600} \quad \left[\frac{\text{L}}{\text{s}}\right]")
        st.caption("Donde $H_{op}$ son las horas de funcionamiento diario de la fábrica.")

    with col_theo2:
        st.markdown("#### 3. Derivación del Factor $86.40$")
        st.markdown(r"""
        Dado que:
        - $1 \text{ día} = 24 \text{ h} \times 60 \text{ min} \times 60 \text{ s} = 86\,400 \text{ segundos}$.
        - $1 \text{ m}^3 = 1\,000 \text{ Litros}$.
        """)
        st.latex(r"\text{Factor} = \frac{86\,400 \text{ s/día}}{1\,000 \text{ L/m}^3} = 86.40")
        st.latex(r"V \left[\frac{\text{m}^3}{\text{día}}\right] = Q \left[\frac{\text{L}}{\text{s}}\right] \times 86.40")

        st.markdown("---")
        st.markdown("#### 4. Asignación de Caudales en Obras de Infraestructura")
        st.markdown(r"""
        - **$Q_{md}$ (Demanda Media Diaria):** Asignación de concesión de aguas superficiales/subterráneas y balances de cuenca.
        - **$Q_{MD} = k_1 \cdot Q_{md}$:** Caudal de diseño para captaciones, desarenadores, líneas de aducción, PTAP y tanques de reserva.
        - **$Q_{MH} = k_2 \cdot Q_{MD}$:** Caudal de diseño para red de distribución, tuberías secundarias y estaciones de bombeo directo.
        """)


# =============================================================================
# TAB 5: EXPORTACIÓN DE MEMORIAS Y DATOS
# =============================================================================
with tab_export:
    st.markdown("### 📥 Generación y Exportación de Memorias Técnicas")
    st.markdown("Genera archivos listos para adjuntar a expedientes de licitación, memorias de cálculo o modelos EPANET.")

    if calculation_success:
        summary_rows = [
            {"Parámetro": "Población de Diseño", "Unidad": "habitantes", "Valor": f"{results.domestic_population:,}"},
            {"Parámetro": "Dotación Neta", "Unidad": "L/hab·día", "Valor": f"{results.domestic_endowment_net:.2f}"},
            {"Parámetro": "Pérdidas Técnicas en Red", "Unidad": "%", "Valor": f"{results.domestic_losses_pct:.1f}%"},
            {"Parámetro": "Dotación Bruta Resultante", "Unidad": "L/hab·día", "Valor": f"{results.domestic_endowment_gross:.2f}"},
            {"Parámetro": "Demanda Media Doméstica (Caudal)", "Unidad": "L/s", "Valor": f"{results.domestic_flow_L_s:.3f}"},
            {"Parámetro": "Demanda Media Doméstica (Volumen)", "Unidad": "m³/día", "Valor": f"{results.domestic_volume_m3_day:,.2f}"},
            {"Parámetro": "Demanda Media Industrial (Caudal)", "Unidad": "L/s", "Valor": f"{results.industrial_flow_L_s:.3f}"},
            {"Parámetro": "Demanda Media Industrial (Volumen)", "Unidad": "m³/día", "Valor": f"{results.industrial_volume_m3_day:,.2f}"},
            {"Parámetro": "Demanda Media Total Qmd (Caudal)", "Unidad": "L/s", "Valor": f"{results.total_flow_L_s:.3f}"},
            {"Parámetro": "Demanda Media Total Qmd (Volumen)", "Unidad": "m³/día", "Valor": f"{results.total_volume_m3_day:,.2f}"},
            {"Parámetro": "Caudal Máximo Diario (QMD)", "Unidad": "L/s", "Valor": f"{results.q_max_daily_flow_L_s:.3f}"},
            {"Parámetro": "Caudal Máximo Horario (QMH)", "Unidad": "L/s", "Valor": f"{results.q_max_hourly_flow_L_s:.3f}"},
            {"Parámetro": "Factor Variación Diaria (k1)", "Unidad": "adimensional", "Valor": f"{results.k1_coefficient:.2f}"},
            {"Parámetro": "Factor Variación Horaria (k2)", "Unidad": "adimensional", "Valor": f"{results.k2_coefficient:.2f}"},
        ]
        df_export_sum = pd.DataFrame(summary_rows)
        st.dataframe(df_export_sum, use_container_width=True, hide_index=True)

        col_ex1, col_ex2, col_ex3 = st.columns(3)

        with col_ex1:
            csv_str = io.StringIO()
            df_export_sum.to_csv(csv_str, index=False, encoding="utf-8-sig")
            st.download_button(
                "📄 Descargar Resumen en CSV",
                data=csv_str.getvalue(),
                file_name="demanda_agua_resumen.csv",
                mime="text/csv"
            )

        with col_ex2:
            excel_bio = io.BytesIO()
            with pd.ExcelWriter(excel_bio, engine="openpyxl") as writer:
                df_export_sum.to_excel(writer, sheet_name="Resumen_Demanda", index=False)
                if results.industrial_details:
                    df_ind_sheet = pd.DataFrame(results.industrial_details)
                    df_ind_sheet.to_excel(writer, sheet_name="Detalle_Industrial", index=False)
                if results.audit_table:
                    df_aud_sheet = pd.DataFrame(results.audit_table)
                    df_aud_sheet.to_excel(writer, sheet_name="Auditoria_Casillas", index=False)
            st.download_button(
                "📊 Descargar Libro Completo en Excel (.xlsx)",
                data=excel_bio.getvalue(),
                file_name="memoria_calculo_demanda_agua.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col_ex3:
            memo_txt = f"""================================================================================
MEMORIA DE CÁLCULO: DEMANDA DOMÉSTICA E INDUSTRIAL DE AGUA
================================================================================
Fecha de Emisión: 2026-11-23
Herramienta: Calculadora de Demanda Doméstica e Industrial de Agua v2.0

1. COMPONENTE DOMÉSTICA:
- Población de Diseño: {results.domestic_population:,} habitantes
- Dotación Neta: {results.domestic_endowment_net:.2f} L/hab·día
- Pérdidas Técnicas en Red: {results.domestic_losses_pct:.1f} %
- Dotación Bruta: {results.domestic_endowment_gross:.2f} L/hab·día
- Demanda Media Doméstica: {results.domestic_flow_L_s:.3f} L/s ({results.domestic_volume_m3_day:,.2f} m³/día)

2. COMPONENTE INDUSTRIAL:
- Demanda Media Industrial 24h: {results.industrial_flow_L_s:.3f} L/s ({results.industrial_volume_m3_day:,.2f} m³/día)
- Industrias registradas: {len(results.industrial_details)}

3. BALANCE TOTAL DEL SISTEMA (Qmd):
- Caudal Medio Diario Total (Qmd): {results.total_flow_L_s:.3f} L/s
- Volumen Diario Total: {results.total_volume_m3_day:,.2f} m³/día
- Distribución: {results.domestic_pct:.1f}% Doméstica | {results.industrial_pct:.1f}% Industrial

4. CAUDALES MÁXIMOS PARA OBRAS DE INFRAESTRUCTURA:
- Factor Diario k1: {results.k1_coefficient:.2f}
- Factor Horario k2: {results.k2_coefficient:.2f}
- Caudal Máximo Diario (QMD): {results.q_max_daily_flow_L_s:.3f} L/s ({results.q_max_daily_volume_m3_day:,.2f} m³/día)
  [Aplica a: Captaciones, Desarenadores, Aducciones, PTAP y Tanques de Reserva]
- Caudal Máximo Horario (QMH): {results.q_max_hourly_flow_L_s:.3f} L/s ({results.q_max_hourly_volume_m3_day:,.2f} m³/día)
  [Aplica a: Red de Distribución y Equipos de Bombeo a Red]
================================================================================
"""
            st.download_button(
                "📝 Descargar Memoria Técnica (.txt)",
                data=memo_txt,
                file_name="memoria_tecnica_demanda.txt",
                mime="text/plain"
            )
    else:
        st.warning("No se puede generar la memoria de cálculo debido a inconsistencias en los datos.")
