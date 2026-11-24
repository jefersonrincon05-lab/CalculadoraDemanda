"""
AQUAMARIS - Plataforma de Ingeniería Hídrica & Demanda de Agua
Ambientación Marina Inspirada en la Paleta "Aqua Natura"
Versión 4.0 - Identidad de Marca, Animaciones de Olas Oceánicas y Auditoría RAS 0330
"""

import io
from datetime import datetime
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
    CalculationMode,
    AltitudeZone,
    RAS_MAX_NET_ENDOWMENT,
    RAS_MAX_TECHNICAL_LOSSES_PCT,
    DOCUMENTED_INDUSTRIAL_BENCHMARKS,
    DomesticDemandInput,
    IndustrialRecord,
    WaterDemandEngine,
    WaterDemandResults,
    ValidationReport,
)
from excel_generator import generate_professional_excel
from pdf_generator import generate_professional_pdf

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AQUAMARIS | Plataforma de Demanda Hídrica",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# CÓDIGO VECTORIAL DEL LOGO OFICIAL "AQUAMARIS" (SVG EMBEBIDO)
# -----------------------------------------------------------------------------
AQUAMARIS_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%" height="100%">
  <defs>
    <linearGradient id="oceanShield" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#123047" />
      <stop offset="60%" stop-color="#087E8B" />
      <stop offset="100%" stop-color="#25866C" />
    </linearGradient>
    <linearGradient id="waveTurquoise" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#087E8B" />
      <stop offset="50%" stop-color="#38B6C5" />
      <stop offset="100%" stop-color="#83B88C" />
    </linearGradient>
    <linearGradient id="dropletGrad" x1="50%" y1="0%" x2="50%" y2="100%">
      <stop offset="0%" stop-color="#38B6C5" />
      <stop offset="100%" stop-color="#087E8B" />
    </linearGradient>
    <filter id="aquaGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <circle cx="120" cy="120" r="108" fill="url(#oceanShield)" stroke="#38B6C5" stroke-width="4" stroke-opacity="0.9" />
  <circle cx="120" cy="120" r="98" fill="none" stroke="#F4F9F8" stroke-width="1.5" stroke-dasharray="6,4" stroke-opacity="0.4" />
  <path d="M 38 135 C 55 105, 95 80, 140 100 C 175 116, 195 95, 202 85 C 195 140, 160 195, 120 198 C 80 200, 48 170, 38 135 Z" fill="url(#waveTurquoise)" opacity="0.9" />
  <path d="M 45 145 C 70 125, 110 115, 145 130 C 170 142, 185 130, 192 120 C 182 165, 150 190, 120 190 C 85 190, 58 170, 45 145 Z" fill="#123047" opacity="0.65" />
  <path d="M 120 52 C 120 52, 90 94, 90 120 C 90 136.5, 103.5 150, 120 150 C 136.5 150, 150 136.5, 150 120 C 150 94, 120 52, 120 52 Z" fill="url(#dropletGrad)" filter="url(#aquaGlow)" stroke="#F4F9F8" stroke-width="2.5" />
  <ellipse cx="110" cy="110" rx="9" ry="14" transform="rotate(-30 110 110)" fill="#F4F9F8" opacity="0.75" />
  <circle cx="132" cy="130" r="3.5" fill="#F4F9F8" opacity="0.6" />
  <path d="M 120 152 C 130 160, 145 162, 155 158 C 145 170, 130 172, 120 170 Z" fill="#83B88C" opacity="0.95" />
</svg>
"""

# -----------------------------------------------------------------------------
# ESTILOS CSS MARINOS Y ANIMACIONES (PALETA AQUA NATURA)
# #123047 (Azul profundo) | #087E8B (Azul río) | #38B6C5 (Turquesa agua)
# #25866C (Verde bosque) | #83B88C (Verde natural) | #F4F9F8 (Blanco niebla)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #123047;
    }
    
    .stApp {
        background-color: #F4F9F8;
        background-image: radial-gradient(circle at 10% 20%, rgba(56, 182, 197, 0.05) 0%, transparent 40%),
                          radial-gradient(circle at 90% 80%, rgba(8, 126, 139, 0.04) 0%, transparent 45%);
    }

    /* Animaciones Marinas Fluidas */
    @keyframes floatDroplet {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-6px) rotate(1.5deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    @keyframes waveMove {
        0% { transform: translateX(0); }
        50% { transform: translateX(-25%); }
        100% { transform: translateX(-50%); }
    }
    @keyframes waveBack {
        0% { transform: translateX(-50%); }
        50% { transform: translateX(-25%); }
        100% { transform: translateX(0); }
    }
    @keyframes pulseGlow {
        0% { box-shadow: 0 4px 20px -2px rgba(56, 182, 197, 0.2); }
        50% { box-shadow: 0 8px 30px 2px rgba(56, 182, 197, 0.4); }
        100% { box-shadow: 0 4px 20px -2px rgba(56, 182, 197, 0.2); }
    }

    /* Banner Oceánico Hero */
    .ocean-hero {
        position: relative;
        background: linear-gradient(135deg, #123047 0%, #087E8B 65%, #25866C 100%);
        border-radius: 16px;
        padding: 2.2rem 2.4rem 4.8rem 2.4rem;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        overflow: hidden;
        box-shadow: 0 10px 30px -5px rgba(8, 126, 139, 0.35);
        border: 1px solid rgba(56, 182, 197, 0.25);
    }
    .hero-content {
        position: relative;
        z-index: 2;
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .logo-box {
        width: 82px;
        height: 82px;
        flex-shrink: 0;
        animation: floatDroplet 4.5s ease-in-out infinite;
        filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.25));
    }
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0;
        color: #FFFFFF;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .brand-tagline {
        font-size: 1.05rem;
        font-weight: 600;
        color: #38B6C5;
        margin-top: 0.25rem;
        letter-spacing: 0.02em;
    }
    .brand-desc {
        font-size: 0.9rem;
        color: #E2E8F0;
        margin-top: 0.35rem;
        max-width: 880px;
        line-height: 1.4;
    }
    .brand-pills {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 0.75rem;
    }
    .marine-pill {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #F4F9F8;
        border: 1px solid rgba(56, 182, 197, 0.4);
    }

    /* Olas Marinas Animadas SVG en el fondo del hero */
    .ocean-waves {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 60px;
        overflow: hidden;
        line-height: 0;
        z-index: 1;
    }

    /* Tarjetas de Módulo y Contenedores */
    .clean-card {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 1.3rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 2px 5px rgba(8, 126, 139, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .clean-card:hover {
        box-shadow: 0 8px 18px -2px rgba(8, 126, 139, 0.1);
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #123047;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 0.4rem;
    }

    /* Tarjetas Métricas KPI con Efecto de Inmersión */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.9rem;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 10px;
        padding: 1.1rem;
        border-top: 4px solid #087E8B;
        box-shadow: 0 2px 4px rgba(8, 126, 139, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-top-color 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px -3px rgba(8, 126, 139, 0.15);
        border-top-color: #38B6C5;
    }
    .kpi-label {
        font-size: 0.76rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-val {
        font-size: 1.65rem;
        font-weight: 800;
        color: #123047;
        line-height: 1.2;
        margin-top: 0.2rem;
    }
    .kpi-sub {
        font-size: 0.82rem;
        color: #087E8B;
        margin-top: 0.25rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
    }

    /* Badges de Estado Aqua Natura */
    .tag-conforme {
        background: #DCFCE7;
        color: #25866C;
        padding: 0.25rem 0.55rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #83B88C;
    }
    .tag-alerta {
        background: #FEF3C7;
        color: #B45309;
        padding: 0.25rem 0.55rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #FDE68A;
    }
    .tag-error {
        background: #FEE2E2;
        color: #B91C1C;
        padding: 0.25rem 0.55rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        border: 1px solid #FECACA;
    }

    /* Botones primarios en Azul Río */
    button[kind="primary"] {
        background-color: #087E8B !important;
        border-color: #087E8B !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        background-color: #38B6C5 !important;
        border-color: #38B6C5 !important;
        box-shadow: 0 4px 12px rgba(56, 182, 197, 0.35) !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR MARINO CON LOGO AQUAMARIS
# -----------------------------------------------------------------------------
with st.sidebar:
    # Logo e identidad en barra lateral
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:1rem; padding-bottom:0.8rem; border-bottom:1px solid #E2E8F0;">
        <div style="width:48px; height:48px; flex-shrink:0;">
            {AQUAMARIS_LOGO_SVG}
        </div>
        <div>
            <div style="font-size:1.25rem; font-weight:800; color:#123047; letter-spacing:-0.02em;">AQUAMARIS</div>
            <div style="font-size:0.75rem; color:#087E8B; font-weight:600;">HIDRO-INGENIERÍA</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Configuración del Sistema")

    mode_selection = st.radio(
        "Marco de Evaluación:",
        options=["Normativa RAS (Res. 0330 / 2017)", "Modo Exploratorio / Libre"],
        index=0,
        help="El modo RAS aplica los límites legales colombianos de dotación máxima (Art. 43) y pérdidas (Art. 44). El modo exploratorio permite evaluar cualquier rango para investigación o diseño internacional."
    )
    is_ras_mode = (mode_selection == "Normativa RAS (Res. 0330 / 2017)")
    calc_mode = CalculationMode.NORMATIVE_RAS if is_ras_mode else CalculationMode.EXPLORATORY

    if is_ras_mode:
        alt_label = st.selectbox(
            "Piso Térmico / Altitud (Art. 43):",
            options=[
                AltitudeZone.COLD.value,
                AltitudeZone.TEMPERATE.value,
                AltitudeZone.WARM.value
            ],
            index=1,
            help="Clasificación altimétrica de la Resolución 0330 de 2017 para fijar la dotación neta máxima admisible."
        )
        if AltitudeZone.COLD.value in alt_label:
            selected_zone = AltitudeZone.COLD
        elif AltitudeZone.WARM.value in alt_label:
            selected_zone = AltitudeZone.WARM
        else:
            selected_zone = AltitudeZone.TEMPERATE
        
        ras_max_dot = RAS_MAX_NET_ENDOWMENT[selected_zone]
        st.caption(f"Límite legal Art. 43: **Máx. {ras_max_dot:.0f} L/hab·día** | Pérdidas Art. 44: **Máx. 25.0%**.")
    else:
        selected_zone = AltitudeZone.TEMPERATE
        ras_max_dot = 350.0

    st.markdown("---")

    scenario_choice = st.selectbox(
        "Cargar Escenario Oceánico / Modelo:",
        options=[
            "Personalizado",
            "Municipio Intermedio (45,000 hab + Agroindustria)",
            "Población Rural (4,500 hab + Lácteos)",
            "Zona Urbana - Industrial (120,000 hab + Parque Fabril)",
        ],
        index=0
    )

    st.markdown("---")

    with st.expander("Factores de Consumo Máximo (k₁, k₂)", expanded=False):
        st.caption("Diferencian la Demanda Media Diaria de los Caudales de Dimensionamiento:")
        
        custom_peaks = st.checkbox("Modificar coeficientes manualmente", value=False)
        
        if custom_peaks:
            k1_input = st.number_input("Coeficiente Diario (k₁) [QMD = k₁ · Qmd]:", min_value=1.00, max_value=2.00, value=1.20, step=0.01, format="%.2f")
            k2_input = st.number_input("Coeficiente Horario (k₂) [QMH = k₂ · QMD]:", min_value=1.00, max_value=3.00, value=1.50, step=0.01, format="%.2f")
        else:
            k1_input = 1.20
            k2_input = 1.50
            st.info("Valores sugeridos por RAS 0330 según tamaño poblacional.")

        apply_k_to_ind = st.checkbox(
            "Mayorar demanda industrial con k₁ y k₂",
            value=False,
            help="En saneamiento estándar, las industrias con reservorio propio o régimen continuo no se afectan con picos residenciales."
        )


# Cargar valores según escenario
if scenario_choice == "Municipio Intermedio (45,000 hab + Agroindustria)":
    def_pop, def_dot, def_loss = 45000, 130.0 if is_ras_mode else 135.0, 20.0
    initial_ind_records = [
        {"Nombre": "Planta Láctea Municipal", "Método": "Específico", "Unidades/día": 40000.0, "Consumo esp.": 2.0, "Unidad": "L/unidad", "Horas op.": 16.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Planta Láctea / Pasteurizadora (L agua / L leche)"]["fuente"]},
        {"Nombre": "Bebidas del Valle", "Método": "Específico", "Unidades/día": 35000.0, "Consumo esp.": 2.5, "Unidad": "L/unidad", "Horas op.": 16.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Bebidas y Refrescos (L agua / L bebida)"]["fuente"]},
        {"Nombre": "Frigorífico Bovino", "Método": "Específico", "Unidades/día": 250.0, "Consumo esp.": 1200.0, "Unidad": "L/unidad", "Horas op.": 8.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Matadero / Frigorífico Bovino (L agua / res faenada)"]["fuente"]},
    ]
elif scenario_choice == "Población Rural (4,500 hab + Lácteos)":
    def_pop, def_dot, def_loss = 4500, 110.0, 15.0
    initial_ind_records = [
        {"Nombre": "Quesería Rural", "Método": "Específico", "Unidades/día": 6000.0, "Consumo esp.": 2.0, "Unidad": "L/unidad", "Horas op.": 8.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Planta Láctea / Pasteurizadora (L agua / L leche)"]["fuente"]},
    ]
elif scenario_choice == "Zona Urbana - Industrial (120,000 hab + Parque Fabril)":
    def_pop, def_dot, def_loss = 120000, 140.0 if is_ras_mode else 160.0, 22.0
    initial_ind_records = [
        {"Nombre": "Parque Cervecero", "Método": "Específico", "Unidades/día": 120000.0, "Consumo esp.": 4.5, "Unidad": "L/unidad", "Horas op.": 24.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Cervecería Industrial (L agua / L cerveza)"]["fuente"]},
        {"Nombre": "Tintorería Textil", "Método": "Específico", "Unidades/día": 8000.0, "Consumo esp.": 110.0, "Unidad": "L/unidad", "Horas op.": 16.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Industria Textil - Tintorería (L agua / kg tela procesada)"]["fuente"]},
        {"Nombre": "Zona Franca Logística", "Método": "Directo", "Unidades/día": 0.0, "Consumo esp.": 350.0, "Unidad": "m3/día", "Horas op.": 24.0, "Reserva propia": True, "Fuente": "Ingreso volumétrico directo."},
    ]
else:
    def_pop, def_dot, def_loss = 25000, 125.0, 18.0
    initial_ind_records = [
        {"Nombre": "Industria Agroalimentaria", "Método": "Directo", "Unidades/día": 0.0, "Consumo esp.": 300.0, "Unidad": "m3/día", "Horas op.": 16.0, "Reserva propia": True, "Fuente": "Estimación directa del proyectista."},
    ]

if "df_industries" not in st.session_state or st.session_state.get("last_scenario_loaded") != scenario_choice:
    st.session_state["df_industries"] = pd.DataFrame(initial_ind_records)
    st.session_state["last_scenario_loaded"] = scenario_choice


# -----------------------------------------------------------------------------
# HERO BANNER PRINCIPAL CON OLAS MARINAS ANIMADAS Y LOGO AQUAMARIS
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="ocean-hero">
    <div class="hero-content">
        <div class="logo-box">
            {AQUAMARIS_LOGO_SVG}
        </div>
        <div>
            <div class="brand-title">AQUAMARIS</div>
            <div class="brand-tagline">PLATAFORMA DE INGENIERÍA HÍDRICA & DEMANDA DE AGUA</div>
            <div class="brand-desc">
                Herramienta avanzada para dimensionamiento hidráulico, estimación de Demanda Media Diaria (Qmd),
                caudales de pico (QMD, QMH) y auditoría técnica bajo el RAS (Resolución 0330 de 2017) y estándares internacionales.
            </div>
            <div class="brand-pills">
                <span class="marine-pill">🌊 Paleta: Aqua Natura</span>
                <span class="marine-pill">⚖️ Marco: {'RAS 0330 (Colombia)' if is_ras_mode else 'Modo Exploratorio'}</span>
                <span class="marine-pill">💧 Continuidad: 1 L/s = 86.40 m³/día</span>
                <span class="marine-pill">🔍 Auditoría Casilla por Casilla</span>
                <span class="marine-pill">📊 Exportación Excel 5 Hojas & PDF</span>
            </div>
        </div>
    </div>
    <div class="ocean-waves">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 24 150 28" preserveAspectRatio="none" style="width:100%; height:55px;">
            <defs>
                <path id="gentle-wave" d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z" />
            </defs>
            <g>
                <use href="#gentle-wave" x="48" y="0" fill="rgba(56, 182, 197, 0.45)" style="animation: waveMove 12s cubic-bezier(.55,.5,.45,.5) infinite;" />
                <use href="#gentle-wave" x="48" y="3" fill="rgba(37, 134, 108, 0.55)" style="animation: waveBack 8s cubic-bezier(.55,.5,.45,.5) infinite;" />
                <use href="#gentle-wave" x="48" y="6" fill="#F4F9F8" style="animation: waveMove 5s cubic-bezier(.55,.5,.45,.5) infinite;" />
            </g>
        </svg>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 4 SECCIONES PRINCIPALES (ORGANIZACIÓN EN PESTAÑAS)
# -----------------------------------------------------------------------------
tab_domestica, tab_industrial, tab_resultados, tab_exportacion = st.tabs([
    "1. Demanda Doméstica",
    "2. Demanda Industrial",
    "3. Resultados y Auditoría",
    "4. Exportación de Informes",
])


# =============================================================================
# SECCIÓN 1: DEMANDA DOMÉSTICA
# =============================================================================
with tab_domestica:
    st.markdown('<div class="card-title">Parámetros de Demanda Doméstica</div>', unsafe_allow_html=True)

    col_d1, col_d2, col_d3 = st.columns([1, 1, 1], gap="medium")

    with col_d1:
        poblacion = st.number_input(
            "Población de Diseño (P) [habitantes]:",
            min_value=1,
            max_value=25_000_000,
            value=int(def_pop),
            step=500,
            help="Población estimada a abastecer al final del período de diseño del sistema."
        )

    with col_d2:
        max_dot_allowed = ras_max_dot if is_ras_mode else 500.0
        dotacion_neta = st.number_input(
            "Dotación Neta (Dneta) [L/hab·día]:",
            min_value=25.0,
            max_value=float(max_dot_allowed),
            value=min(float(def_dot), float(max_dot_allowed)),
            step=5.0,
            format="%.1f",
            help=f"Consumo neto asignado por habitante al día. Límite legal actual: {max_dot_allowed:.0f} L/hab·día."
        )

    with col_d3:
        max_loss_allowed = RAS_MAX_TECHNICAL_LOSSES_PCT if is_ras_mode else 55.0
        perdidas_pct = st.number_input(
            "Pérdidas Técnicas en Red (%P) [%]:",
            min_value=0.0,
            max_value=float(max_loss_allowed),
            value=min(float(def_loss), float(max_loss_allowed)),
            step=1.0,
            format="%.1f",
            help="Agua no contabilizada (ANC) debida a fugas en red. Máximo RAS Art. 44: 25.0%."
        )

    factor_p = 1.0 - (perdidas_pct / 100.0)
    dotacion_bruta_prelim = dotacion_neta / factor_p if factor_p > 0 else 0.0

    st.markdown("---")
    
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:1rem 1.4rem; display:flex; gap:2.5rem; flex-wrap:wrap; align-items:center; box-shadow: 0 2px 4px rgba(8, 126, 139, 0.04);">
        <div>
            <span style="font-size:0.75rem; color:#64748B; font-weight:700; text-transform:uppercase;">DOTACIÓN NETA:</span><br/>
            <span style="font-size:1.25rem; font-weight:800; color:#123047;">{dotacion_neta:.1f} <span style="font-size:0.85rem; font-weight:500;">L/hab·d</span></span>
        </div>
        <div>
            <span style="font-size:0.75rem; color:#64748B; font-weight:700; text-transform:uppercase;">PÉRDIDAS EN RED:</span><br/>
            <span style="font-size:1.25rem; font-weight:800; color:#087E8B;">{perdidas_pct:.1f}%</span>
        </div>
        <div>
            <span style="font-size:0.75rem; color:#64748B; font-weight:700; text-transform:uppercase;">DOTACIÓN BRUTA CALCULADA:</span><br/>
            <span style="font-size:1.25rem; font-weight:800; color:#25866C;">{dotacion_bruta_prelim:.2f} <span style="font-size:0.85rem; font-weight:500;">L/hab·d</span></span>
        </div>
        <div>
            <span style="font-size:0.75rem; color:#64748B; font-weight:700; text-transform:uppercase;">ESTADO TÉCNICO:</span><br/>
            <span class="tag-conforme">CONFORME RAS 0330</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Consultar Criterios Normativos de Dotación (Art. 43 y 44 Res. 0330 de 2017)", expanded=False):
        st.markdown(r"""
        - **Artículo 43 (Dotación Neta Máxima):**
          - Altura $> 2.000\text{ msnm}$ (Clima Frío): Máximo **120 L/hab·día**.
          - Altura $1.000 - 2.000\text{ msnm}$ (Clima Templado): Máximo **130 L/hab·día**.
          - Altura $< 1.000\text{ msnm}$ (Clima Cálido): Máximo **140 L/hab·día**.
        - **Artículo 44 (Pérdidas Técnicas en Red):**
          - No deben superar el **25.0%** en redes de distribución de agua potable.
        - **Fórmula de Dotación Bruta:**
          $$D_{bruta} = \frac{D_{neta}}{1 - \frac{\%P}{100}} \quad [L/\text{hab}\cdot\text{día}]$$
        """)


# =============================================================================
# SECCIÓN 2: DEMANDA INDUSTRIAL (TABLA EDITABLE Y UNIFICADA)
# =============================================================================
with tab_industrial:
    st.markdown('<div class="card-title">Inventario y Modelación de Demanda Industrial</div>', unsafe_allow_html=True)
    st.caption("Edita directamente las celdas de la tabla para modificar consumos o agregar nuevas industrias. La tabla está 100% unificada con el motor de cálculo.")

    edited_df = st.data_editor(
        st.session_state["df_industries"],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Nombre": st.column_config.TextColumn("Industria / Razón Social", required=True),
            "Método": st.column_config.SelectboxColumn("Método", options=["Directo", "Específico"], required=True),
            "Unidades/día": st.column_config.NumberColumn("Unidades/día", min_value=0.0, step=100.0, format="%.0f"),
            "Consumo esp.": st.column_config.NumberColumn("Consumo esp. o Consumo m³/d", min_value=0.0, step=0.1, format="%.4f"),
            "Unidad": st.column_config.SelectboxColumn("Unidad", options=["L/unidad", "m3/unidad", "m3/día"], required=True),
            "Horas op.": st.column_config.NumberColumn("Horas Op. (Hop)", min_value=1.0, max_value=24.0, step=1.0, format="%.0f"),
            "Reserva propia": st.column_config.CheckboxColumn("Tanque Reserva Propio", default=True),
            "Fuente": st.column_config.TextColumn("Fuente Técnica de Referencia"),
        },
        key="editor_industrias"
    )

    st.session_state["df_industries"] = edited_df

    col_btn_i1, col_btn_i2 = st.columns([1, 4])
    with col_btn_i1:
        if st.button("Restablecer Industrias al Escenario"):
            st.session_state["df_industries"] = pd.DataFrame(initial_ind_records)
            st.rerun()

    with st.expander("Catálogo Documentado de Benchmarks Industriales de Referencia", expanded=False):
        b_data_list = []
        for k, v in DOCUMENTED_INDUSTRIAL_BENCHMARKS.items():
            b_data_list.append({
                "Giro Industrial": k,
                "Consumo Típico": f"{v['consumo_tipico']} {v['unit']}",
                "Horas Op.": f"{v['horas_op_tipicas']:.0f} h/día",
                "Fuente Técnica Documentada": v["fuente"]
            })
        st.dataframe(pd.DataFrame(b_data_list), use_container_width=True, hide_index=True)


# =============================================================================
# CONVERSIÓN DE DATOS Y EJECUCIÓN DEL MOTOR HIDRÁULICO
# =============================================================================
industrial_objs: List[IndustrialRecord] = []
for _, row in edited_df.iterrows():
    r_name = str(row.get("Nombre", "Industria")).strip()
    if not r_name:
        continue
    r_method = "direct" if row.get("Método", "Directo") == "Directo" else "specific"
    r_u_qty = float(row.get("Unidades/día", 0.0) or 0.0)
    r_esp = float(row.get("Consumo esp.", 0.0) or 0.0)
    r_unit = str(row.get("Unidad", "m3/unidad"))
    r_hours = float(row.get("Horas op.", 24.0) or 24.0)
    r_storage = bool(row.get("Reserva propia", True))
    r_source = str(row.get("Fuente", "-"))

    if r_method == "direct":
        rec = IndustrialRecord(
            name=r_name,
            mode="direct",
            direct_consumption_m3_day=r_esp,
            operating_hours_per_day=r_hours,
            has_own_storage=r_storage,
            benchmark_source=r_source
        )
    else:
        rec = IndustrialRecord(
            name=r_name,
            mode="specific",
            units_per_day=r_u_qty,
            specific_consumption=r_esp,
            specific_unit=r_unit if r_unit in ["L/unidad", "m3/unidad"] else "m3/unidad",
            operating_hours_per_day=r_hours,
            has_own_storage=r_storage,
            benchmark_source=r_source
        )
    industrial_objs.append(rec)

if not custom_peaks:
    k1_val, k2_val = WaterDemandEngine.suggest_ras_peak_factors(poblacion)
else:
    k1_val, k2_val = k1_input, k2_input

dom_input = DomesticDemandInput(
    population=poblacion,
    endowment_L_hab_day=dotacion_neta,
    technical_losses_pct=perdidas_pct,
    mode=calc_mode,
    altitude_zone=selected_zone
)

calc_error = None
try:
    results: WaterDemandResults = WaterDemandEngine.calculate_total_system_demand(
        domestic_input=dom_input,
        industrial_records=industrial_objs,
        k1=k1_val,
        k2=k2_val,
        apply_k_to_industrial=apply_k_to_ind
    )
except Exception as ex:
    calc_error = str(ex)
    results = None


# =============================================================================
# SECCIÓN 3: RESULTADOS Y AUDITORÍA TÉCNICA
# =============================================================================
with tab_resultados:
    if calc_error:
        st.error(f"Incoherencia Técnica Detectada: {calc_error}")
    else:
        st.markdown('<div class="card-title">Cuadro de Mando de Caudales de Diseño</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card" style="border-top-color: #087E8B;">
                <div class="kpi-label">Demanda Doméstica (Qmd_dom)</div>
                <div class="kpi-val">{results.domestic_flow_L_s:.2f} <span style="font-size:0.85rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub">{results.domestic_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:0.25rem;">Dotación Bruta: {results.domestic_endowment_gross:.1f} L/hab·d</div>
            </div>
            <div class="kpi-card" style="border-top-color: #38B6C5;">
                <div class="kpi-label">Demanda Industrial (Qmd_ind)</div>
                <div class="kpi-val">{results.industrial_flow_L_s:.2f} <span style="font-size:0.85rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub">{results.industrial_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:0.25rem;">{len(results.industrial_details)} proceso(s) modelados</div>
            </div>
            <div class="kpi-card" style="border-top-color: #123047; background:#F8FAFC;">
                <div class="kpi-label" style="color:#123047;">Demanda Media Total (Qmd)</div>
                <div class="kpi-val" style="color:#123047;">{results.total_flow_L_s:.2f} <span style="font-size:0.85rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub" style="color:#123047;">{results.total_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#087E8B; font-weight:700; margin-top:0.25rem;">Base Concesiones y Balances</div>
            </div>
            <div class="kpi-card" style="border-top-color: #25866C; background:#F0FDF4;">
                <div class="kpi-label" style="color:#25866C;">Máximo Diario (QMD)</div>
                <div class="kpi-val" style="color:#25866C;">{results.q_max_daily_flow_L_s:.2f} <span style="font-size:0.85rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub" style="color:#166534;">{results.q_max_daily_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#15803D; margin-top:0.25rem;">k₁ = {results.k1_coefficient:.2f} | Captación, Aducción, PTAP</div>
            </div>
            <div class="kpi-card" style="border-top-color: #0E7490; background:#ECFEFF;">
                <div class="kpi-label" style="color:#0E7490;">Máximo Horario (QMH)</div>
                <div class="kpi-val" style="color:#0E7490;">{results.q_max_hourly_flow_L_s:.2f} <span style="font-size:0.85rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub" style="color:#155E75;">{results.q_max_hourly_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#0E7490; margin-top:0.25rem;">k₂ = {results.k2_coefficient:.2f} | Red de Distribución</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_chart1, col_chart2 = st.columns([1.2, 1], gap="medium")

        with col_chart1:
            fig_bars = go.Figure()
            fig_bars.add_trace(go.Bar(
                x=["Doméstico (Qmd)", "Industrial (Qmd)", "Medio Total (Qmd)", "Máx. Diario (QMD)", "Máx. Horario (QMH)"],
                y=[results.domestic_flow_L_s, results.industrial_flow_L_s, results.total_flow_L_s, results.q_max_daily_flow_L_s, results.q_max_hourly_flow_L_s],
                marker_color=["#087E8B", "#38B6C5", "#123047", "#25866C", "#0E7490"],
                text=[f"{results.domestic_flow_L_s:.2f} L/s", f"{results.industrial_flow_L_s:.2f} L/s", f"{results.total_flow_L_s:.2f} L/s", f"{results.q_max_daily_flow_L_s:.2f} L/s", f"{results.q_max_hourly_flow_L_s:.2f} L/s"],
                textposition="outside"
            ))
            fig_bars.update_layout(
                title=dict(text="Comparativa de Caudales del Sistema (L/s)", font=dict(size=13, color="#123047", family="Plus Jakarta Sans")),
                height=300,
                margin=dict(l=20, r=20, t=35, b=20),
                yaxis=dict(title="Caudal (L/s)", gridcolor="#E2E8F0"),
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans, sans-serif")
            )
            st.plotly_chart(fig_bars, use_container_width=True)

        with col_chart2:
            if results.total_volume_m3_day > 0:
                fig_donut = go.Figure(data=[go.Pie(
                    labels=["Doméstico", "Industrial"],
                    values=[results.domestic_volume_m3_day, results.industrial_volume_m3_day],
                    hole=0.62,
                    marker_colors=["#087E8B", "#38B6C5"],
                    textinfo="label+percent",
                    texttemplate="<b>%{label}</b><br>%{percent} (%{value:,.0f} m³/d)",
                    hoverinfo="label+value+percent",
                )])
                fig_donut.update_layout(
                    title=dict(text="Distribución de la Demanda Diaria", font=dict(size=13, color="#123047", family="Plus Jakarta Sans")),
                    showlegend=False,
                    height=300,
                    margin=dict(l=10, r=10, t=35, b=10),
                    font=dict(family="Plus Jakarta Sans, sans-serif")
                )
                st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")
        
        st.markdown('<div class="card-title">Matriz de Auditoría Casilla por Casilla</div>', unsafe_allow_html=True)
        st.caption("Verificación de consistencia dimensional, límites normativos y trazabilidad técnica.")

        if results.audit_table:
            df_audit_display = pd.DataFrame(results.audit_table)
            st.dataframe(df_audit_display, use_container_width=True, hide_index=True)


# =============================================================================
# SECCIÓN 4: EXPORTACIÓN DE INFORMES (EXCEL PROFESIONAL Y PDF)
# =============================================================================
with tab_exportacion:
    st.markdown('<div class="card-title">Generación de Memorias y Documentos Técnicos</div>', unsafe_allow_html=True)
    st.markdown("""
    Descarga la memoria completa de cálculo estructurada conforme a estándares de consultoría hidráulica y la identidad **AQUAMARIS**.
    La memoria en Excel incluye 5 hojas técnicas con fórmulas comprobables en celdas, valores numéricos reales y auditoría de concordancia `Python vs Excel`.
    """)

    if results and not calc_error:
        excel_bytes = generate_professional_excel(results)
        pdf_bytes = generate_professional_pdf(results)

        col_ex_main, col_ex_pdf = st.columns(2, gap="large")

        with col_ex_main:
            st.markdown("""
            <div style="background:#FFFFFF; border:2px solid #087E8B; border-radius:12px; padding:1.25rem; box-shadow:0 4px 6px -1px rgba(8, 126, 139, 0.08);">
                <h4 style="color:#123047; margin-top:0;">📊 Libro Completo en Excel (.xlsx)</h4>
                <p style="font-size:0.85rem; color:#475569;">
                    Incluye 5 hojas técnicas formalizadas con fórmulas comprobables en celda y paleta Aqua Natura:
                </p>
                <ul style="font-size:0.8rem; color:#123047; padding-left:1.2rem;">
                    <li><b>01_Resumen:</b> Cuadro ejecutivo y gráfico de caudales.</li>
                    <li><b>02_Datos_Entrada:</b> Parámetros del proyecto y marco normativo.</li>
                    <li><b>03_Memoria_Calculo:</b> Fórmulas auditables enlazadas a celdas.</li>
                    <li><b>04_Detalle_Industrial:</b> Inventario con caudales en turno (Qop).</li>
                    <li><b>05_Verificacion:</b> Chequeo Python vs Excel (Diferencia = 0.000).</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📥 Descargar Memoria en Excel (.xlsx)",
                data=excel_bytes.getvalue(),
                file_name=f"AQUAMARIS_Demanda_Agua_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_ex_pdf:
            st.markdown("""
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:12px; padding:1.25rem; box-shadow:0 2px 4px rgba(8, 126, 139, 0.05);">
                <h4 style="color:#123047; margin-top:0;">📄 Informe Técnico en PDF (.pdf)</h4>
                <p style="font-size:0.85rem; color:#475569;">
                    Documento formal maquetado con la identidad AQUAMARIS listo para adjuntar a expedientes técnicos:
                </p>
                <ul style="font-size:0.8rem; color:#123047; padding-left:1.2rem;">
                    <li>Tablas de caudales medios y máximos consolidados.</li>
                    <li>Control de cumplimiento de Artículos 43 y 44 Res. 0330.</li>
                    <li>Desglose de usuarios industriales y caudales en turno.</li>
                    <li>Notas y consideraciones de ingeniería sanitaria.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📥 Descargar Informe Técnico en PDF (.pdf)",
                data=pdf_bytes.getvalue(),
                file_name=f"AQUAMARIS_Informe_Demanda_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.warning("No es posible generar los archivos de exportación hasta que se corrijan las inconsistencias detectadas.")
