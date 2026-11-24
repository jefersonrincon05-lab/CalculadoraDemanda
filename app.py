"""
AQUAMARIS - Plataforma de Ingeniería Hídrica & Demanda de Agua
Ambientación Marina Inmersiva - Paleta "Aqua Natura"
Versión 5.0 - Sistema Tipográfico Profesional (Manrope, Inter, JetBrains Mono) & Alto Contraste
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
# CÓDIGO VECTORIAL DEL LOGO OFICIAL "AQUAMARIS" (SVG COMPACTO)
# -----------------------------------------------------------------------------
AQUAMARIS_LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="100%" height="100%">'
    '<defs>'
    '<linearGradient id="oceanShield" x1="0%" y1="0%" x2="100%" y2="100%">'
    '<stop offset="0%" stop-color="#123047" />'
    '<stop offset="60%" stop-color="#087E8B" />'
    '<stop offset="100%" stop-color="#25866C" />'
    '</linearGradient>'
    '<linearGradient id="waveTurquoise" x1="0%" y1="100%" x2="100%" y2="0%">'
    '<stop offset="0%" stop-color="#087E8B" />'
    '<stop offset="50%" stop-color="#38B6C5" />'
    '<stop offset="100%" stop-color="#83B88C" />'
    '</linearGradient>'
    '<linearGradient id="dropletGrad" x1="50%" y1="0%" x2="50%" y2="100%">'
    '<stop offset="0%" stop-color="#38B6C5" />'
    '<stop offset="100%" stop-color="#087E8B" />'
    '</linearGradient>'
    '<filter id="aquaGlow" x="-20%" y="-20%" width="140%" height="140%">'
    '<feGaussianBlur stdDeviation="5" result="blur" />'
    '<feComposite in="SourceGraphic" in2="blur" operator="over" />'
    '</filter>'
    '</defs>'
    '<circle cx="120" cy="120" r="108" fill="url(#oceanShield)" stroke="#38B6C5" stroke-width="4" stroke-opacity="0.9" />'
    '<circle cx="120" cy="120" r="98" fill="none" stroke="#F4F9F8" stroke-width="1.5" stroke-dasharray="6,4" stroke-opacity="0.4" />'
    '<path d="M 38 135 C 55 105, 95 80, 140 100 C 175 116, 195 95, 202 85 C 195 140, 160 195, 120 198 C 80 200, 48 170, 38 135 Z" fill="url(#waveTurquoise)" opacity="0.9" />'
    '<path d="M 45 145 C 70 125, 110 115, 145 130 C 170 142, 185 130, 192 120 C 182 165, 150 190, 120 190 C 85 190, 58 170, 45 145 Z" fill="#123047" opacity="0.65" />'
    '<path d="M 120 52 C 120 52, 90 94, 90 120 C 90 136.5, 103.5 150, 120 150 C 136.5 150, 150 136.5, 150 120 C 150 94, 120 52, 120 52 Z" fill="url(#dropletGrad)" filter="url(#aquaGlow)" stroke="#F4F9F8" stroke-width="2.5" />'
    '<ellipse cx="110" cy="110" rx="9" ry="14" transform="rotate(-30 110 110)" fill="#F4F9F8" opacity="0.75" />'
    '<circle cx="132" cy="130" r="3.5" fill="#F4F9F8" opacity="0.6" />'
    '<path d="M 120 152 C 130 160, 145 162, 155 158 C 145 170, 130 172, 120 170 Z" fill="#83B88C" opacity="0.95" />'
    '</svg>'
)

# -----------------------------------------------------------------------------
# SISTEMA TIPOGRÁFICO PROFESIONAL & ESTILOS MARINOS DE ALTO CONTRASTE
# Fuentes: Manrope (Títulos) | Inter (General & UI) | JetBrains Mono (Numérico)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0');
    
    /* Tipografía Base Global */
    html, body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 15px;
        color: #F8FAFC !important;
        -webkit-font-smoothing: antialiased;
    }

    /* Fondo Oceánico Profundo Inmersivo */
    .stApp {
        background: linear-gradient(180deg, #071626 0%, #092032 25%, #0B2C42 55%, #093C52 85%, #08495A 100%) fixed !important;
        color: #F8FAFC !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Partículas de Agua y Burbujas */
    .ocean-glimmer {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 0;
        background: radial-gradient(ellipse at 30% 15%, rgba(56, 182, 197, 0.15) 0%, transparent 60%),
                    radial-gradient(ellipse at 80% 65%, rgba(8, 126, 139, 0.18) 0%, transparent 55%);
        animation: oceanGlimmer 7s ease-in-out infinite;
    }
    @keyframes oceanGlimmer {
        0% { opacity: 0.3; }
        50% { opacity: 0.65; }
        100% { opacity: 0.3; }
    }

    .ocean-bubble-field {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }
    .ocean-bubble {
        position: absolute;
        bottom: -50px;
        background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.95), rgba(56, 182, 197, 0.45) 40%, rgba(8, 126, 139, 0.15) 75%, rgba(56, 182, 197, 0.65) 100%);
        border-radius: 50%;
        box-shadow: 0 0 12px rgba(56, 182, 197, 0.55), inset 0 0 6px rgba(255, 255, 255, 0.85);
        pointer-events: none;
        animation: bubbleRise linear infinite;
    }
    @keyframes bubbleRise {
        0% { transform: translateY(0) translateX(0) scale(0.65); opacity: 0; }
        12% { opacity: 0.85; }
        50% { transform: translateY(-50vh) translateX(30px) scale(1.0); opacity: 0.85; }
        85% { opacity: 0.7; }
        100% { transform: translateY(-112vh) translateX(-25px) scale(1.2); opacity: 0; }
    }

    .b1  { left: 3%;  width: 14px; height: 14px; animation-duration: 9s;   animation-delay: 0s; }
    .b2  { left: 8%;  width: 24px; height: 24px; animation-duration: 15s;  animation-delay: 2s; }
    .b3  { left: 15%; width: 10px; height: 10px; animation-duration: 8.5s; animation-delay: 4.5s; }
    .b4  { left: 22%; width: 30px; height: 30px; animation-duration: 18s;  animation-delay: 1s; }
    .b5  { left: 28%; width: 16px; height: 16px; animation-duration: 11s;  animation-delay: 6s; }
    .b6  { left: 34%; width: 12px; height: 12px; animation-duration: 10s;  animation-delay: 3s; }
    .b7  { left: 40%; width: 22px; height: 22px; animation-duration: 14s;  animation-delay: 7.5s; }
    .b8  { left: 46%; width: 8px;  height: 8px;  animation-duration: 7s;   animation-delay: 2.5s; }
    .b9  { left: 52%; width: 26px; height: 26px; animation-duration: 16.5s;animation-delay: 5s; }
    .b10 { left: 58%; width: 15px; height: 15px; animation-duration: 12s;  animation-delay: 0.5s; }
    .b11 { left: 64%; width: 20px; height: 20px; animation-duration: 14.5s;animation-delay: 8s; }
    .b12 { left: 70%; width: 9px;  height: 9px;  animation-duration: 8.5s; animation-delay: 3.5s; }
    .b13 { left: 76%; width: 28px; height: 28px; animation-duration: 17s;  animation-delay: 6.5s; }
    .b14 { left: 82%; width: 13px; height: 13px; animation-duration: 9.5s; animation-delay: 1.5s; }
    .b15 { left: 88%; width: 32px; height: 32px; animation-duration: 19s;  animation-delay: 4.5s; }
    .b16 { left: 93%; width: 16px; height: 16px; animation-duration: 11.5s;animation-delay: 9s; }
    .b17 { left: 97%; width: 11px; height: 11px; animation-duration: 8s;   animation-delay: 5.5s; }
    .b18 { left: 18%; width: 18px; height: 18px; animation-duration: 13.5s;animation-delay: 10.5s; }
    .b19 { left: 49%; width: 14px; height: 14px; animation-duration: 10.5s;animation-delay: 8.5s; }
    .b20 { left: 73%; width: 22px; height: 22px; animation-duration: 15s;  animation-delay: 11.5s; }

    /* Barra Lateral Marina */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #051321 0%, #071C2E 60%, #09263A 100%) !important;
        border-right: 1px solid rgba(56, 182, 197, 0.3) !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-family: 'Manrope', sans-serif !important;
        color: #FFFFFF !important;
        font-size: 20px !important;
        font-weight: 700 !important;
    }

    /* JERARQUÍA TIPOGRÁFICA Y CONTROL DE CONTRASTE */
    h1 {
        font-family: 'Manrope', sans-serif !important;
        font-size: 32px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.02em !important;
    }
    h2 {
        font-family: 'Manrope', sans-serif !important;
        font-size: 22px !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
    }
    h3 {
        font-family: 'Manrope', sans-serif !important;
        font-size: 19px !important;
        font-weight: 600 !important;
        color: #38B6C5 !important;
    }
    h4 {
        font-family: 'Manrope', sans-serif !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
    }

    p, li, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        color: #F1F5F9 !important;
        line-height: 1.55 !important;
    }

    /* Preservar iconos nativos de Streamlit (Material Symbols / Material Icons) */
    [class*="material-symbols"],
    [class*="material-icons"],
    [data-testid*="stIcon"],
    [data-testid*="Icon"],
    [data-testid="stExpanderToggleIcon"],
    .material-symbols-rounded,
    .material-symbols-outlined,
    [data-testid="stExpander"] summary span:first-child,
    [data-testid="stExpander"] summary i {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-size: 20px !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
        text-rendering: optimizeLegibility !important;
        font-feature-settings: 'liga' !important;
        fill: #38B6C5 !important;
        color: #38B6C5 !important;
    }

    /* Etiquetas de Widgets con Máximo Contraste */
    [data-testid="stWidgetLabel"] label, [data-testid="stWidgetLabel"] p, label {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #F8FAFC !important;
        letter-spacing: 0.01em !important;
    }

    /* Textos Secundarios y Subtítulos Explicativos (Alto Contraste) */
    .stCaption, [data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"], small {
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #CBD5E1 !important;
        line-height: 1.5 !important;
    }

    /* Entradas Numéricas y Formularios (JetBrains Mono para valores) */
    [data-testid="stNumberInput"] > div > div,
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div {
        background-color: #0A2236 !important;
        background: #0A2236 !important;
        border: 1px solid rgba(56, 182, 197, 0.5) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="input"] > div:focus-within {
        border-color: #38B6C5 !important;
        box-shadow: 0 0 12px rgba(56, 182, 197, 0.5) !important;
        outline: none !important;
    }
    div[data-baseweb="input"] input {
        color: #FFFFFF !important;
        background-color: transparent !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="input"] button {
        color: #38B6C5 !important;
        background-color: rgba(56, 182, 197, 0.15) !important;
        border-color: rgba(56, 182, 197, 0.35) !important;
    }
    div[data-baseweb="input"] button:hover {
        background-color: #087E8B !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="input"] button svg {
        fill: #38B6C5 !important;
    }

    /* CONTROLES SELECTBOX Y DESPLEGABLES - ALTO CONTRASTE TOTAL */
    [data-testid="stSelectbox"] > div > div,
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] div[role="combobox"],
    div[data-baseweb="select"] > div:first-child {
        background-color: #0A2236 !important;
        background: #0A2236 !important;
        border: 1px solid rgba(56, 182, 197, 0.5) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    [data-testid="stSelectbox"] > div > div:focus-within {
        border-color: #38B6C5 !important;
        box-shadow: 0 0 12px rgba(56, 182, 197, 0.5) !important;
        outline: none !important;
    }

    /* Texto seleccionado en la casilla de selección */
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] p,
    div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 600 !important;
    }

    /* Icono de flecha del selector */
    div[data-baseweb="select"] svg {
        fill: #38B6C5 !important;
        color: #38B6C5 !important;
    }

    /* El menú desplegable flotante (BaseWeb Popover al abrir el selectbox) */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="menu"],
    div[data-baseweb="menu"] > ul,
    ul[role="listbox"] {
        background-color: #071A2C !important;
        background: #071A2C !important;
        border: 1px solid #38B6C5 !important;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.85) !important;
        border-radius: 8px !important;
        padding: 6px !important;
    }

    /* Opciones dentro del menú desplegable */
    li[role="option"],
    div[role="option"] {
        background-color: #071A2C !important;
        background: #071A2C !important;
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        margin-bottom: 2px !important;
        padding: 9px 14px !important;
        transition: background-color 0.15s ease !important;
    }

    li[role="option"] *,
    div[role="option"] * {
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important;
    }

    /* Opción seleccionada o con cursor encima (Hover) */
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"],
    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {
        background-color: #087E8B !important;
        background: #087E8B !important;
        color: #FFFFFF !important;
    }

    li[role="option"]:hover *,
    li[role="option"][aria-selected="true"] *,
    div[role="option"]:hover *,
    div[role="option"][aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* Icono de ayuda (?) con alto contraste */
    [data-testid="stTooltipIcon"] svg,
    [data-testid="stTooltipIcon"] {
        fill: #38B6C5 !important;
        color: #38B6C5 !important;
    }
    div[data-testid="stTooltipContent"] {
        background-color: #071A2C !important;
        border: 1px solid #38B6C5 !important;
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
    }

    /* Radio Buttons y Checkboxes */
    div[role="radiogroup"] label p, div[data-testid="stCheckbox"] label p {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #F8FAFC !important;
    }
    div[role="radiogroup"] div[data-checked="true"] {
        background-color: #38B6C5 !important;
        border-color: #38B6C5 !important;
    }

    /* Pestañas de Módulos (Manrope + Inter) */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(7, 22, 38, 0.85) !important;
        border: 1px solid rgba(56, 182, 197, 0.35) !important;
        border-radius: 10px !important;
        padding: 5px !important;
        gap: 6px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #CBD5E1 !important;
        font-family: 'Manrope', sans-serif !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        border-radius: 8px !important;
        padding: 9px 18px !important;
        border: none !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #38B6C5 !important;
        background: rgba(56, 182, 197, 0.12) !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        background: linear-gradient(135deg, rgba(8, 126, 139, 0.8) 0%, rgba(37, 134, 108, 0.8) 100%) !important;
        border: 1px solid rgba(56, 182, 197, 0.6) !important;
        box-shadow: 0 4px 14px rgba(8, 126, 139, 0.45) !important;
        font-weight: 700 !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Botones de Acción (Inter con peso equilibrado) */
    button[kind="primary"], .stButton > button {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #087E8B 0%, #25866C 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #38B6C5 !important;
        box-shadow: 0 4px 15px rgba(8, 126, 139, 0.4) !important;
        border-radius: 8px !important;
        padding: 0.55rem 1.2rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s ease !important;
    }
    button[kind="primary"]:hover, .stButton > button:hover {
        background: linear-gradient(135deg, #38B6C5 0%, #087E8B 100%) !important;
        box-shadow: 0 6px 22px rgba(56, 182, 197, 0.6) !important;
        transform: translateY(-2px);
    }
    .stDownloadButton > button {
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #087E8B 0%, #25866C 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #38B6C5 !important;
        border-radius: 8px !important;
        padding: 0.55rem 1.2rem !important;
        letter-spacing: 0.01em !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #38B6C5 0%, #087E8B 100%) !important;
        box-shadow: 0 6px 20px rgba(56, 182, 197, 0.5) !important;
        transform: translateY(-2px);
    }

    /* Acordeones / Desplegables (st.expander) */
    [data-testid="stExpander"] {
        background: rgba(14, 38, 59, 0.88) !important;
        border: 1px solid rgba(56, 182, 197, 0.35) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    [data-testid="stExpander"] summary {
        display: flex !important;
        align-items: center !important;
        gap: 0.6rem !important;
        padding: 0.65rem 0.9rem !important;
        cursor: pointer !important;
        color: #38B6C5 !important;
    }
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] p,
    [data-testid="stExpander"] summary span {
        color: #38B6C5 !important;
        font-family: 'Manrope', sans-serif !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }
    [data-testid="stExpander"] summary svg {
        fill: #38B6C5 !important;
        min-width: 18px !important;
    }
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
        color: #E2E8F0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] b {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Tablas y Data Editor */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        background: rgba(10, 28, 44, 0.95) !important;
        border: 1px solid rgba(56, 182, 197, 0.45) !important;
        border-radius: 10px !important;
        color: #F8FAFC !important;
    }
    [data-testid="stDataFrame"] *, [data-testid="stDataEditor"] * {
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
    }

    /* Banner Oceánico Hero */
    .ocean-hero {
        position: relative;
        background: linear-gradient(135deg, #071A2C 0%, #0A3249 50%, #085566 100%);
        border-radius: 16px;
        padding: 2.2rem 2.4rem 4.8rem 2.4rem;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        overflow: hidden;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(56, 182, 197, 0.45);
    }
    .hero-content {
        position: relative;
        z-index: 2;
        display: flex;
        align-items: center;
        gap: 1.8rem;
    }
    .logo-box {
        width: 86px;
        height: 86px;
        flex-shrink: 0;
        animation: floatDroplet 4.5s ease-in-out infinite;
        filter: drop-shadow(0 8px 16px rgba(56, 182, 197, 0.4));
    }
    .brand-title {
        font-family: 'Manrope', sans-serif;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #FFFFFF;
        text-shadow: 0 0 20px rgba(56, 182, 197, 0.6);
        line-height: 1.15;
    }
    .brand-tagline {
        font-family: 'Manrope', sans-serif;
        font-size: 19px;
        font-weight: 700;
        color: #38B6C5;
        margin-top: 0.35rem;
        letter-spacing: 0.03em;
    }
    .brand-desc {
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        color: #F1F5F9;
        margin-top: 0.45rem;
        max-width: 920px;
        line-height: 1.55;
    }
    .brand-pills {
        display: flex;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-top: 0.9rem;
    }
    .marine-pill {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 600;
        background: rgba(8, 126, 139, 0.35);
        backdrop-filter: blur(8px);
        padding: 0.3rem 0.85rem;
        border-radius: 9999px;
        color: #E0F2FE;
        border: 1px solid rgba(56, 182, 197, 0.45);
    }
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

    /* Nombres de Módulos y Títulos de Sección (Manrope 20 a 22px) */
    .card-title {
        font-family: 'Manrope', sans-serif;
        font-size: 20px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.9rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        border-bottom: 2px solid rgba(56, 182, 197, 0.35);
        padding-bottom: 0.45rem;
        letter-spacing: -0.01em;
    }

    /* KPI Grid y Resultados Principales (JetBrains Mono 28 a 32px) */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(195px, 1fr));
        gap: 1rem;
        margin-bottom: 1.3rem;
    }
    .kpi-card {
        background: rgba(14, 38, 59, 0.92);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 182, 197, 0.35);
        border-radius: 12px;
        padding: 1.2rem;
        border-top: 4px solid #087E8B;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-top-color 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(56, 182, 197, 0.3);
        border-top-color: #38B6C5;
    }
    .kpi-label {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 600;
        color: #CBD5E1;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 30px;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1.2;
        margin-top: 0.3rem;
    }
    .kpi-unit {
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        font-weight: 600;
        color: #38B6C5;
    }
    .kpi-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
        color: #38B6C5;
        margin-top: 0.3rem;
        font-weight: 600;
    }
    .kpi-note {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        color: #E2E8F0;
        margin-top: 0.35rem;
    }

    /* Badges de Cumplimiento Técnico */
    .tag-conforme {
        font-family: 'Inter', sans-serif;
        background: rgba(37, 134, 108, 0.35);
        color: #83B88C;
        padding: 0.32rem 0.75rem;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 700;
        border: 1px solid #25866C;
        letter-spacing: 0.03em;
    }

    /* Alertas con Alto Contraste */
    div[data-testid="stAlert"] {
        background-color: rgba(10, 32, 50, 0.95) !important;
        border: 1px solid rgba(56, 182, 197, 0.45) !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stAlert"] * {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 15px !important;
    }

    /* Responsividad Celulares */
    @media (max-width: 768px) {
        .brand-title {
            font-size: 24px !important;
        }
        .brand-tagline {
            font-size: 16px !important;
        }
        .card-title {
            font-size: 18px !important;
        }
        .kpi-val {
            font-size: 24px !important;
        }
        .hero-content {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }
        .logo-box {
            width: 60px;
            height: 60px;
        }
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR MARINO CON LOGO AQUAMARIS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:1rem; padding-bottom:0.8rem; border-bottom:1px solid rgba(56, 182, 197, 0.3);">'
        f'<div style="width:48px; height:48px; flex-shrink:0;">{AQUAMARIS_LOGO_SVG}</div>'
        f'<div><div style="font-family:\'Manrope\', sans-serif; font-size:22px; font-weight:800; color:#FFFFFF; letter-spacing:-0.02em;">AQUAMARIS</div>'
        f'<div style="font-family:\'Inter\', sans-serif; font-size:12px; color:#38B6C5; font-weight:700; letter-spacing:0.06em;">HIDRO-INGENIERÍA</div></div></div>',
        unsafe_allow_html=True
    )

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
# PARTÍCULAS DE AGUA FLOTANTES Y BURBUJAS ACTIVAS
# -----------------------------------------------------------------------------
particles_html = (
    '<div class="ocean-glimmer"></div>'
    '<div class="ocean-bubble-field">'
    '<div class="ocean-bubble b1"></div><div class="ocean-bubble b2"></div>'
    '<div class="ocean-bubble b3"></div><div class="ocean-bubble b4"></div>'
    '<div class="ocean-bubble b5"></div><div class="ocean-bubble b6"></div>'
    '<div class="ocean-bubble b7"></div><div class="ocean-bubble b8"></div>'
    '<div class="ocean-bubble b9"></div><div class="ocean-bubble b10"></div>'
    '<div class="ocean-bubble b11"></div><div class="ocean-bubble b12"></div>'
    '<div class="ocean-bubble b13"></div><div class="ocean-bubble b14"></div>'
    '<div class="ocean-bubble b15"></div><div class="ocean-bubble b16"></div>'
    '<div class="ocean-bubble b17"></div><div class="ocean-bubble b18"></div>'
    '<div class="ocean-bubble b19"></div><div class="ocean-bubble b20"></div>'
    '</div>'
)
st.markdown(particles_html, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# HERO BANNER PRINCIPAL CON OLAS MARINAS Y LOGO AQUAMARIS
# -----------------------------------------------------------------------------
marco_label = "RAS 0330 (Colombia)" if is_ras_mode else "Modo Exploratorio"
hero_html = f"""<div class="ocean-hero">
<div class="hero-content">
<div class="logo-box">{AQUAMARIS_LOGO_SVG}</div>
<div>
<h1 class="brand-title">AQUAMARIS</h1>
<div class="brand-tagline">PLATAFORMA DE INGENIERÍA HÍDRICA &amp; DEMANDA DE AGUA</div>
<p class="brand-desc">
Herramienta avanzada para dimensionamiento hidráulico, estimación de Demanda Media Diaria (Qmd),
caudales de pico (QMD, QMH) y auditoría técnica bajo el RAS (Resolución 0330 de 2017) y estándares internacionales.
</p>
<div class="brand-pills">
<span class="marine-pill">⚖️ Marco: {marco_label}</span>
<span class="marine-pill">💧 Continuidad: 1 L/s = 86.40 m³/día</span>
<span class="marine-pill">🔍 Auditoría Casilla por Casilla</span>
<span class="marine-pill">📊 Exportación Excel 5 Hojas &amp; PDF</span>
</div>
</div>
</div>
<div class="ocean-waves">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 24 150 28" preserveAspectRatio="none" style="width:100%; height:55px;">
<defs>
<path id="gentle-wave" d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z" />
</defs>
<g>
<use href="#gentle-wave" x="48" y="0" fill="rgba(56, 182, 197, 0.35)" style="animation: waveMove 12s cubic-bezier(.55,.5,.45,.5) infinite;" />
<use href="#gentle-wave" x="48" y="3" fill="rgba(37, 134, 108, 0.45)" style="animation: waveBack 8s cubic-bezier(.55,.5,.45,.5) infinite;" />
<use href="#gentle-wave" x="48" y="6" fill="#092032" style="animation: waveMove 5s cubic-bezier(.55,.5,.45,.5) infinite;" />
</g>
</svg>
</div>
</div>"""
st.markdown(hero_html, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 5 SECCIONES PRINCIPALES (ORGANIZACIÓN EN PESTAÑAS)
# -----------------------------------------------------------------------------
tab_domestica, tab_industrial, tab_resultados, tab_formulas, tab_exportacion = st.tabs([
    "1. Demanda Doméstica",
    "2. Demanda Industrial",
    "3. Resultados y Auditoría",
    "4. Memoria de Fórmulas y Teoría",
    "5. Exportación de Informes",
])


# =============================================================================
# SECCIÓN 1: DEMANDA DOMÉSTICA
# =============================================================================
with tab_domestica:
    st.markdown('<div class="card-title">💧 Parámetros de Demanda Doméstica</div>', unsafe_allow_html=True)

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
    
    st.markdown(f"""<div style="background:rgba(14, 38, 59, 0.92); backdrop-filter:blur(10px); border:1px solid rgba(56, 182, 197, 0.35); border-radius:12px; padding:1.2rem 1.6rem; display:flex; gap:2.5rem; flex-wrap:wrap; align-items:center; box-shadow:0 8px 24px rgba(0, 0, 0, 0.4);">
<div>
<span style="font-family:'Inter', sans-serif; font-size:13px; color:#CBD5E1; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">DOTACIÓN NETA:</span><br/>
<span style="font-family:'JetBrains Mono', monospace; font-size:26px; font-weight:700; color:#FFFFFF;">{dotacion_neta:.1f} <span style="font-family:'Inter', sans-serif; font-size:14px; color:#38B6C5; font-weight:600;">L/hab·d</span></span>
</div>
<div>
<span style="font-family:'Inter', sans-serif; font-size:13px; color:#CBD5E1; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">PÉRDIDAS EN RED:</span><br/>
<span style="font-family:'JetBrains Mono', monospace; font-size:26px; font-weight:700; color:#38B6C5;">{perdidas_pct:.1f}%</span>
</div>
<div>
<span style="font-family:'Inter', sans-serif; font-size:13px; color:#CBD5E1; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">DOTACIÓN BRUTA CALCULADA:</span><br/>
<span style="font-family:'JetBrains Mono', monospace; font-size:26px; font-weight:700; color:#83B88C;">{dotacion_bruta_prelim:.2f} <span style="font-family:'Inter', sans-serif; font-size:14px; color:#83B88C; font-weight:600;">L/hab·d</span></span>
</div>
<div>
<span style="font-family:'Inter', sans-serif; font-size:13px; color:#CBD5E1; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">ESTADO TÉCNICO:</span><br/>
<span class="tag-conforme">CONFORME RAS 0330</span>
</div>
</div>""", unsafe_allow_html=True)

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
# SECCIÓN 2: DEMANDA INDUSTRIAL (INVENTARIO, ASISTENTE Y BENCHMARKS)
# =============================================================================
with tab_industrial:
    st.markdown('<div class="card-title">🏭 Inventario y Modelación de Demanda Industrial</div>', unsafe_allow_html=True)
    st.markdown("""
    Modela el consumo de agua del sector productivo. Puedes agregar industrias manualmente en la tabla, cargar paquetes típicos de sector
    o utilizar el **Asistente por Giro Industrial** con consumos específicos tomados de literatura técnica formal (PNUMA, Banco Mundial, FAO, CEPIS/OPS, IPPC BREF, ACI).
    """)

    # -------------------------------------------------------------------------
    # ASISTENTE DE INCORPORACIÓN RÁPIDA POR GIRO INDUSTRIAL
    # -------------------------------------------------------------------------
    with st.expander("➕ Asistente de Incorporación Rápida por Giro Industrial (Benchmarks Técnicos)", expanded=True):
        st.markdown("<p style='font-size:14px; color:#CBD5E1; margin-bottom:0.6rem;'>Selecciona un sector productivo documentado para precargar su consumo específico y régimen de operación recomendado:</p>", unsafe_allow_html=True)
        
        catalog_keys = [k for k in DOCUMENTED_INDUSTRIAL_BENCHMARKS.keys() if k != "Personalizada"]
        
        col_bench1, col_bench2 = st.columns([1.5, 1], gap="medium")
        with col_bench1:
            selected_benchmark_key = st.selectbox(
                "Giro Industrial / Sector Productivo Documentado:",
                options=catalog_keys,
                index=0,
                key="select_benchmark_key"
            )
        bench_info = DOCUMENTED_INDUSTRIAL_BENCHMARKS[selected_benchmark_key]
        
        with col_bench2:
            st.markdown(f"""<div style="background:rgba(8, 126, 139, 0.25); border:1px solid rgba(56, 182, 197, 0.45); border-radius:8px; padding:0.65rem 0.9rem; margin-top:0.25rem;">
<div style="font-size:12px; color:#38B6C5; font-weight:700;">BENCHMARK DOCUMENTADO:</div>
<div style="font-size:14px; color:#FFFFFF; font-weight:600;">{bench_info['consumo_tipico']} {bench_info['unit']} | {bench_info['horas_op_tipicas']:.0f} h/día</div>
<div style="font-size:11px; color:#CBD5E1; margin-top:2px;">Fuente: {bench_info['fuente'][:85]}...</div>
</div>""", unsafe_allow_html=True)

        col_in1, col_in2, col_in3, col_in4 = st.columns([1.4, 1.1, 1, 1], gap="medium")
        with col_in1:
            default_name = selected_benchmark_key.split("(")[0].strip()
            new_ind_name = st.text_input("Nombre de la Instalación / Razón Social:", value=f"{default_name} 01", key="input_new_ind_name")
        with col_in2:
            unit_name = bench_info["unit"]
            default_units = 10000.0 if "L" in unit_name else 100.0
            if "res" in selected_benchmark_key.lower():
                default_units = 250.0
            elif "ave" in selected_benchmark_key.lower():
                default_units = 15000.0
            elif "cerdo" in selected_benchmark_key.lower():
                default_units = 400.0
            elif "cama" in selected_benchmark_key.lower():
                default_units = 200.0
            elif "huésped" in selected_benchmark_key.lower():
                default_units = 350.0
            elif "vehículo" in selected_benchmark_key.lower():
                default_units = 150.0
            new_ind_units = st.number_input(f"Producción Diaria ({unit_name}):", min_value=1.0, value=default_units, step=50.0, format="%.0f", key="input_new_ind_units")
        with col_in3:
            new_ind_esp = st.number_input(f"Consumo Esp. ({unit_name}):", min_value=0.0001, value=float(bench_info["consumo_tipico"]), step=0.1, format="%.4f", key="input_new_ind_esp")
        with col_in4:
            new_ind_hours = st.number_input("Horas Turno (Hop):", min_value=1.0, max_value=24.0, value=float(bench_info["horas_op_tipicas"]), step=1.0, format="%.0f", key="input_new_ind_hours")

        col_chk, col_add = st.columns([1.6, 1], gap="medium")
        with col_chk:
            new_ind_storage = st.checkbox("¿Dispone de tanque de reserva propio? (Recomendado: Amortigua picos residenciales)", value=True, key="input_new_ind_storage")
        with col_add:
            if st.button("➕ Incorporar Industria a la Tabla", key="btn_add_industry"):
                new_row = {
                    "Nombre": new_ind_name.strip() or "Nueva Industria",
                    "Método": "Específico",
                    "Unidades/día": float(new_ind_units),
                    "Consumo esp.": float(new_ind_esp),
                    "Unidad": bench_info["unit"],
                    "Horas op.": float(new_ind_hours),
                    "Reserva propia": bool(new_ind_storage),
                    "Fuente": bench_info["fuente"]
                }
                curr_df = st.session_state["df_industries"].copy()
                curr_df = curr_df[curr_df["Nombre"].notna() & (curr_df["Nombre"].astype(str).str.strip() != "") & (curr_df["Nombre"].astype(str).str.strip() != "None")]
                st.session_state["df_industries"] = pd.concat([curr_df, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Industria '{new_ind_name}' agregada al inventario.")
                st.rerun()

    # -------------------------------------------------------------------------
    # PLANTILLAS RÁPIDAS DE GIROS INDUSTRIALES TÍPICOS
    # -------------------------------------------------------------------------
    st.markdown("<div style='font-size:14px; font-weight:600; color:#CBD5E1; margin:1rem 0 0.4rem 0;'>Plantillas Rápidas por Sector Económico:</div>", unsafe_allow_html=True)
    p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5, gap="small")
    with p_col1:
        if st.button("🥛 Lácteo & Bebidas"):
            st.session_state["df_industries"] = pd.DataFrame([
                {"Nombre": "Planta Pasteurizadora", "Método": "Específico", "Unidades/día": 50000.0, "Consumo esp.": 2.0, "Unidad": "L/unidad", "Horas op.": 16.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Planta Láctea / Pasteurizadora (L agua / L leche)"]["fuente"]},
                {"Nombre": "Embotelladora de Refrescos", "Método": "Específico", "Unidades/día": 30000.0, "Consumo esp.": 2.5, "Unidad": "L/unidad", "Horas op.": 16.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Bebidas y Refrescos (L agua / L bebida)"]["fuente"]},
            ])
            st.rerun()
    with p_col2:
        if st.button("🥩 Cárnico & Aves"):
            st.session_state["df_industries"] = pd.DataFrame([
                {"Nombre": "Frigorífico Bovino", "Método": "Específico", "Unidades/día": 300.0, "Consumo esp.": 1200.0, "Unidad": "L/unidad", "Horas op.": 8.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Matadero / Frigorífico Bovino (L agua / res faenada)"]["fuente"]},
                {"Nombre": "Beneficio Avícola", "Método": "Específico", "Unidades/día": 20000.0, "Consumo esp.": 25.0, "Unidad": "L/unidad", "Horas op.": 12.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Planta de Beneficio Avícola (L agua / ave faenada)"]["fuente"]},
            ])
            st.rerun()
    with p_col3:
        if st.button("🧵 Textil & Lavandería"):
            st.session_state["df_industries"] = pd.DataFrame([
                {"Nombre": "Tintorería Textil", "Método": "Específico", "Unidades/día": 10000.0, "Consumo esp.": 110.0, "Unidad": "L/unidad", "Horas op.": 16.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Industria Textil - Tintorería (L agua / kg tela procesada)"]["fuente"]},
                {"Nombre": "Lavandería Industrial", "Método": "Específico", "Unidades/día": 3000.0, "Consumo esp.": 20.0, "Unidad": "L/unidad", "Horas op.": 12.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Lavandería Industrial (L agua / kg ropa lavada)"]["fuente"]},
            ])
            st.rerun()
    with p_col4:
        if st.button("🏗️ Concreto & Papel"):
            st.session_state["df_industries"] = pd.DataFrame([
                {"Nombre": "Planta Concretera", "Método": "Específico", "Unidades/día": 350.0, "Consumo esp.": 0.20, "Unidad": "m3/unidad", "Horas op.": 10.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Central de Concreto Hidráulico (m³ agua / m³ concreto)"]["fuente"]},
                {"Nombre": "Molino Papelero", "Método": "Específico", "Unidades/día": 20.0, "Consumo esp.": 25.0, "Unidad": "m3/unidad", "Horas op.": 24.0, "Reserva propia": True, "Fuente": DOCUMENTED_INDUSTRIAL_BENCHMARKS["Fabricación de Papel y Cartón (m³ agua / ton papel)"]["fuente"]},
            ])
            st.rerun()
    with p_col5:
        if st.button("🔄 Restablecer"):
            st.session_state["df_industries"] = pd.DataFrame(initial_ind_records)
            st.rerun()

    st.markdown("---")

    # -------------------------------------------------------------------------
    # TABLA EDITABLE (FILTRANDO AUTOMÁTICAMENTE FILAS VACÍAS O NONE)
    # -------------------------------------------------------------------------
    st.markdown("<div style='font-size:15px; font-weight:700; color:#FFFFFF; margin-bottom:0.4rem;'>📋 Matriz de Inventario Industrial Activo:</div>", unsafe_allow_html=True)
    st.caption("Puedes editar libremente cualquier celda en la tabla. Las filas con datos incompletos o vacías se ignoran automáticamente.")

    clean_table_df = st.session_state["df_industries"].copy()
    clean_table_df = clean_table_df[
        clean_table_df["Nombre"].notna() &
        (clean_table_df["Nombre"].astype(str).str.strip() != "") &
        (clean_table_df["Nombre"].astype(str).str.strip().str.lower() != "none")
    ]
    if clean_table_df.empty:
        clean_table_df = pd.DataFrame(initial_ind_records)

    edited_df = st.data_editor(
        clean_table_df,
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

    with st.expander("📖 Catálogo Técnico Completo de Benchmarks Industriales de Referencia (17 Giros)", expanded=False):
        b_data_list = []
        for k, v in DOCUMENTED_INDUSTRIAL_BENCHMARKS.items():
            if k == "Personalizada":
                continue
            b_data_list.append({
                "Giro Industrial / Sector": k,
                "Consumo Típico": f"{v['consumo_tipico']} {v['unit']}",
                "Horas Op.": f"{v['horas_op_tipicas']:.0f} h/día",
                "Fuente Técnica Formal": v["fuente"]
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
        st.markdown('<div class="card-title">📊 Cuadro de Mando de Caudales de Diseño</div>', unsafe_allow_html=True)

        st.markdown(f"""<div class="kpi-grid">
<div class="kpi-card" style="border-top-color: #087E8B;">
<div class="kpi-label">Demanda Doméstica (Qmd_dom)</div>
<div class="kpi-val">{results.domestic_flow_L_s:.2f} <span class="kpi-unit">L/s</span></div>
<div class="kpi-sub">{results.domestic_volume_m3_day:,.1f} m³/día</div>
<div class="kpi-note">Dotación Bruta: {results.domestic_endowment_gross:.1f} L/hab·d</div>
</div>
<div class="kpi-card" style="border-top-color: #38B6C5;">
<div class="kpi-label">Demanda Industrial (Qmd_ind)</div>
<div class="kpi-val" style="color: #38B6C5;">{results.industrial_flow_L_s:.2f} <span class="kpi-unit">L/s</span></div>
<div class="kpi-sub">{results.industrial_volume_m3_day:,.1f} m³/día</div>
<div class="kpi-note">{len(results.industrial_details)} proceso(s) modelados</div>
</div>
<div class="kpi-card" style="border-top-color: #38B6C5; background: rgba(18, 48, 71, 0.95);">
<div class="kpi-label" style="color: #38B6C5;">Demanda Media Total (Qmd)</div>
<div class="kpi-val" style="color: #FFFFFF;">{results.total_flow_L_s:.2f} <span class="kpi-unit">L/s</span></div>
<div class="kpi-sub" style="color: #80DEEA;">{results.total_volume_m3_day:,.1f} m³/día</div>
<div class="kpi-note" style="color: #38B6C5; font-weight:700;">Base Concesiones y Balances</div>
</div>
<div class="kpi-card" style="border-top-color: #25866C; background: rgba(12, 42, 48, 0.95);">
<div class="kpi-label" style="color: #83B88C;">Máximo Diario (QMD)</div>
<div class="kpi-val" style="color: #83B88C;">{results.q_max_daily_flow_L_s:.2f} <span class="kpi-unit">L/s</span></div>
<div class="kpi-sub" style="color: #A7F3D0;">{results.q_max_daily_volume_m3_day:,.1f} m³/día</div>
<div class="kpi-note" style="color: #83B88C;">k₁ = {results.k1_coefficient:.2f} | Captación, Aducción, PTAP</div>
</div>
<div class="kpi-card" style="border-top-color: #087E8B; background: rgba(10, 36, 54, 0.95);">
<div class="kpi-label" style="color: #67E8F9;">Máximo Horario (QMH)</div>
<div class="kpi-val" style="color: #67E8F9;">{results.q_max_hourly_flow_L_s:.2f} <span class="kpi-unit">L/s</span></div>
<div class="kpi-sub" style="color: #BAE6FD;">{results.q_max_hourly_volume_m3_day:,.1f} m³/día</div>
<div class="kpi-note" style="color: #67E8F9;">k₂ = {results.k2_coefficient:.2f} | Red de Distribución</div>
</div>
</div>""", unsafe_allow_html=True)

        col_chart1, col_chart2 = st.columns([1.2, 1], gap="medium")

        with col_chart1:
            fig_bars = go.Figure()
            fig_bars.add_trace(go.Bar(
                x=["Doméstico (Qmd)", "Industrial (Qmd)", "Medio Total (Qmd)", "Máx. Diario (QMD)", "Máx. Horario (QMH)"],
                y=[results.domestic_flow_L_s, results.industrial_flow_L_s, results.total_flow_L_s, results.q_max_daily_flow_L_s, results.q_max_hourly_flow_L_s],
                marker_color=["#087E8B", "#38B6C5", "#80DEEA", "#25866C", "#83B88C"],
                text=[f"{results.domestic_flow_L_s:.2f} L/s", f"{results.industrial_flow_L_s:.2f} L/s", f"{results.total_flow_L_s:.2f} L/s", f"{results.q_max_daily_flow_L_s:.2f} L/s", f"{results.q_max_hourly_flow_L_s:.2f} L/s"],
                textposition="outside",
                textfont=dict(color="#F8FAFC", size=12, family="JetBrains Mono")
            ))
            fig_bars.update_layout(
                title=dict(text="Comparativa de Caudales del Sistema (L/s)", font=dict(size=18, color="#FFFFFF", family="Manrope")),
                height=330,
                margin=dict(l=20, r=20, t=45, b=20),
                yaxis=dict(title="Caudal (L/s)", gridcolor="rgba(56, 182, 197, 0.18)", tickfont=dict(color="#CBD5E1", size=12, family="Inter"), title_font=dict(color="#38B6C5", size=14, family="Inter")),
                xaxis=dict(tickfont=dict(color="#F1F5F9", size=12, family="Inter"), gridcolor="rgba(0,0,0,0)"),
                plot_bgcolor="rgba(10, 30, 48, 0.65)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif")
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
                    textfont=dict(color="#FFFFFF", size=13, family="Inter")
                )])
                fig_donut.update_layout(
                    title=dict(text="Distribución de la Demanda Diaria", font=dict(size=18, color="#FFFFFF", family="Manrope")),
                    showlegend=False,
                    height=330,
                    margin=dict(l=10, r=10, t=45, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif")
                )
                st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")
        
        st.markdown('<div class="card-title">🔍 Matriz de Auditoría Casilla por Casilla</div>', unsafe_allow_html=True)
        st.caption("Verificación de consistencia dimensional, límites normativos y trazabilidad técnica.")

        if results.audit_table:
            df_audit_display = pd.DataFrame(results.audit_table)
            st.dataframe(df_audit_display, use_container_width=True, hide_index=True)


# =============================================================================
# SECCIÓN 4: MEMORIA DE FÓRMULAS Y TEORÍA HIDRÁULICA
# =============================================================================
with tab_formulas:
    st.markdown('<div class="card-title">📐 Memoria de Fórmulas y Fundamentos Hidráulicos</div>', unsafe_allow_html=True)
    st.markdown("""
    Esta sección expone formalmente el sustento matemático, dimensional y normativo implementado en el motor de cálculo de **AQUAMARIS**.
    Todos los modelos se rigen por el principio de conservación de masa (continuidad hidráulica) y el marco normativo colombiano
    establecido en el **Reglamento Técnico del Sector de Agua Potable y Saneamiento Básico (RAS - Resolución 0330 de 2017)** y el **Decreto 1077 de 2015**.
    """)

    col_theo1, col_theo2 = st.columns(2, gap="large")

    with col_theo1:
        st.markdown("""<div style="background:rgba(10, 30, 48, 0.75); border:1px solid rgba(56, 182, 197, 0.3); border-radius:10px; padding:1.2rem; margin-bottom:1.2rem;">
<h4 style="font-family:'Manrope', sans-serif; color:#38B6C5; font-size:18px; margin-top:0;">1. Ecuación de Continuidad y Factor 86.40</h4>
<p style="font-family:'Inter', sans-serif; font-size:14px; color:#E2E8F0; line-height:1.6;">
La relación dimensional fundamental entre el volumen diario acumulado ($V$ en $\\text{m}^3/\\text{día}$) y el caudal continuo equivalente ($Q$ en $\\text{L/s}$) se deduce analíticamente:
</p>
</div>""", unsafe_allow_html=True)

        st.latex(r"Q \, [\text{L/s}] = \frac{V \, [\text{m}^3/\text{día}] \times 1\,000 \, [\text{L/m}^3]}{86\,400 \, [\text{s/día}]} = \frac{V \, [\text{m}^3/\text{día}]}{86.40}")
        st.latex(r"V \, [\text{m}^3/\text{día}] = Q \, [\text{L/s}] \times 86.40")

        st.markdown("""<div style="background:rgba(10, 30, 48, 0.75); border:1px solid rgba(56, 182, 197, 0.3); border-radius:10px; padding:1.2rem; margin-bottom:1.2rem; margin-top:1.2rem;">
<h4 style="font-family:'Manrope', sans-serif; color:#38B6C5; font-size:18px; margin-top:0;">2. Demanda Doméstica (Art. 43 y 44 Res. 0330/2017)</h4>
<p style="font-family:'Inter', sans-serif; font-size:14px; color:#E2E8F0; line-height:1.6;">
<b>a) Dotación Bruta ($D_{\\text{bruta}}$):</b> Incorpora las pérdidas técnicas admisibles en la red de distribución sobre la dotación neta de diseño:
</p>
</div>""", unsafe_allow_html=True)

        st.latex(r"D_{\text{bruta}} = \frac{D_{\text{neta}}}{1 - \frac{\%P}{100}} \quad \left[\frac{\text{L}}{\text{hab}\cdot\text{día}}\right]")

        st.markdown(r"""<p style="font-family:'Inter', sans-serif; font-size:13px; color:#94A3B8; margin-top:-0.5rem; margin-bottom:0.8rem;">
<b>Límites RAS Art. 43:</b> Frío (&gt; 2000 msnm): máx. 120 L/hab·d | Templado (1000 - 2000 msnm): máx. 130 L/hab·d | Cálido (&lt; 1000 msnm): máx. 140 L/hab·d.<br>
<b>Límite RAS Art. 44:</b> Pérdidas técnicas en red %P &le; 25.0%.
</p>""", unsafe_allow_html=True)

        st.markdown("<p style='font-family:Inter; font-size:14px; color:#E2E8F0;'><b>b) Caudal Medio Diario Doméstico ($Q_{md, \\text{dom}}$):</b></p>", unsafe_allow_html=True)
        st.latex(r"Q_{md, \text{dom}} = \frac{P \times D_{\text{bruta}}}{86\,400} = \frac{P \times D_{\text{bruta}}}{86.40 \times 1\,000} \quad [\text{L/s}]")

        st.markdown("<p style='font-family:Inter; font-size:14px; color:#E2E8F0;'><b>c) Volumen Medio Diario Doméstico ($V_{\\text{dom}}$):</b></p>", unsafe_allow_html=True)
        st.latex(r"V_{\text{dom}} = \frac{P \times D_{\text{bruta}}}{1\,000} = Q_{md, \text{dom}} \times 86.40 \quad [\text{m}^3/\text{día}]")

        st.markdown("""<div style="background:rgba(10, 30, 48, 0.75); border:1px solid rgba(56, 182, 197, 0.3); border-radius:10px; padding:1.2rem; margin-bottom:1.2rem; margin-top:1.2rem;">
<h4 style="font-family:'Manrope', sans-serif; color:#38B6C5; font-size:18px; margin-top:0;">3. Demanda Industrial y Caudal en Turno Operativo</h4>
<p style="font-family:'Inter', sans-serif; font-size:14px; color:#E2E8F0; line-height:1.6;">
<b>a) Volumen Diario por Industria ($V_i$):</b> Calculado por estimación directa o por producto de unidades producidas y consumo específico documentado:
</p>
</div>""", unsafe_allow_html=True)

        st.latex(r"V_i = \text{Unidades/día} \times C_{\text{esp}} \quad [\text{m}^3/\text{día}] \quad \implies \quad V_{\text{ind}} = \sum_{i=1}^{n} V_i")
        st.latex(r"Q_{md, \text{ind}} = \frac{V_{\text{ind}}}{86.40} \quad [\text{L/s}]")

        st.markdown("<p style='font-family:Inter; font-size:14px; color:#E2E8F0;'><b>b) Caudal Operativo Instantáneo en Horas de Turno ($Q_{op, i}$):</b></p>", unsafe_allow_html=True)
        st.latex(r"Q_{op, i} = \frac{V_i \times 1\,000}{H_{op, i} \times 3\,600} = \frac{V_i}{3.6 \times H_{op, i}} \quad [\text{L/s}]")
        st.caption("Nota técnica: Si la industria no dispone de tanque de almacenamiento propio, la red de distribución municipal debe suministrar el caudal operativo instantáneo Qop durante las horas del turno.")

    with col_theo2:
        st.markdown("""<div style="background:rgba(10, 30, 48, 0.75); border:1px solid rgba(56, 182, 197, 0.3); border-radius:10px; padding:1.2rem; margin-bottom:1.2rem;">
<h4 style="font-family:'Manrope', sans-serif; color:#38B6C5; font-size:18px; margin-top:0;">4. Integración del Sistema y Coeficientes de Pico ($k_1, k_2$)</h4>
<p style="font-family:'Inter', sans-serif; font-size:14px; color:#E2E8F0; line-height:1.6;">
<b>a) Caudal Medio Diario Total del Sistema ($Q_{md}$):</b>
</p>
</div>""", unsafe_allow_html=True)

        st.latex(r"Q_{md} = Q_{md, \text{dom}} + Q_{md, \text{ind}} \quad [\text{L/s}]")
        st.latex(r"V_{\text{total}} = V_{\text{dom}} + V_{\text{ind}} \quad [\text{m}^3/\text{día}]")

        st.markdown(r"""<p style="font-family:'Inter', sans-serif; font-size:14px; color:#E2E8F0; margin-top:0.6rem;">
<b>b) Caudal Máximo Diario ($Q_{MD}$):</b> Coeficiente $k_1$ según Art. 47 Res. 0330 ($1.10 \le k_1 \le 1.30$). Si las industrias disponen de reserva propia (estándar hidráulico), su demanda no se mayora por los picos residenciales:
</p>""", unsafe_allow_html=True)

        st.latex(r"Q_{MD} = \begin{cases} (Q_{md, \text{dom}} \times k_1) + Q_{md, \text{ind}} & \text{si industria amortigua con reserva} \\ Q_{md} \times k_1 & \text{sin amortiguamiento industrial} \end{cases}")

        st.markdown(r"""<p style="font-family:'Inter', sans-serif; font-size:14px; color:#E2E8F0; margin-top:0.6rem;">
<b>c) Caudal Máximo Horario ($Q_{MH}$):</b> Coeficiente $k_2$ según Art. 47 Res. 0330 ($1.40 \le k_2 \le 1.60$ para poblaciones mayores a 12.500 hab, o hasta 1.80 para menores):
</p>""", unsafe_allow_html=True)

        st.latex(r"Q_{MH} = \begin{cases} (Q_{md, \text{dom}} \times k_1 \times k_2) + Q_{md, \text{ind}} & \text{si industria amortigua con reserva} \\ Q_{MD} \times k_2 = Q_{md} \times k_1 \times k_2 & \text{sin amortiguamiento industrial} \end{cases}")

        st.markdown("""<div style="background:rgba(10, 30, 48, 0.75); border:1px solid rgba(56, 182, 197, 0.3); border-radius:10px; padding:1.2rem; margin-bottom:1.2rem; margin-top:1.2rem;">
<h4 style="font-family:'Manrope', sans-serif; color:#38B6C5; font-size:18px; margin-top:0;">5. Asignación Normativa a Obras Civiles (Art. 48)</h4>
<p style="font-family:'Inter', sans-serif; font-size:13px; color:#CBD5E1; line-height:1.5;">
La Resolución 0330 de 2017 (RAS) establece el caudal de diseño obligatorio para cada componente de la infraestructura:
</p>
<table style="width:100%; font-family:'Inter', sans-serif; font-size:12px; color:#F1F5F9; border-collapse:collapse; margin-top:8px;">
<thead>
<tr style="border-bottom:1px solid #38B6C5; color:#38B6C5; text-align:left;">
<th style="padding:4px 6px;">Componente</th>
<th style="padding:4px 6px;">Caudal de Diseño</th>
<th style="padding:4px 6px;">Base Técnica</th>
</tr>
</thead>
<tbody>
<tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
<td style="padding:5px 6px;"><b>Captación de Agua</b></td>
<td style="padding:5px 6px; font-family:'JetBrains Mono'; color:#83B88C;">QMD (+ pérdidas)</td>
<td style="padding:5px 6px;">Asegura suministro en el día de mayor demanda anual.</td>
</tr>
<tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
<td style="padding:5px 6px;"><b>Desarenador y Aducción</b></td>
<td style="padding:5px 6px; font-family:'JetBrains Mono'; color:#83B88C;">QMD</td>
<td style="padding:5px 6px;">Transporte continuo de agua cruda hacia la planta.</td>
</tr>
<tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
<td style="padding:5px 6px;"><b>Planta Potabilizadora (PTAP)</b></td>
<td style="padding:5px 6px; font-family:'JetBrains Mono'; color:#83B88C;">QMD</td>
<td style="padding:5px 6px;">Capacidad nominal de floculación, sedimentación y filtros.</td>
</tr>
<tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
<td style="padding:5px 6px;"><b>Tanque de Compensación</b></td>
<td style="padding:5px 6px; font-family:'JetBrains Mono'; color:#38B6C5;">Vol. Regulación</td>
<td style="padding:5px 6px;">Amortigua la diferencia entre oferta continua (QMD) y demanda horaria (QMH).</td>
</tr>
<tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
<td style="padding:5px 6px;"><b>Red de Distribución</b></td>
<td style="padding:5px 6px; font-family:'JetBrains Mono'; color:#67E8F9;">QMH (o QMD + Incendio)</td>
<td style="padding:5px 6px;">Debe soportar la hora crítica de máxima simultaneidad doméstica.</td>
</tr>
</tbody>
</table>
</div>""", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SUSTITUCIÓN NUMÉRICA EN VIVO CON LOS DATOS ACTUALES DEL MODELO
    # -------------------------------------------------------------------------
    st.markdown('<div class="card-title" style="margin-top:1.5rem;">🔢 Trazabilidad y Sustitución Numérica en Vivo (Valores del Proyecto)</div>', unsafe_allow_html=True)
    if results and not calc_error:
        k_diag_text_qmd = f"QMD = ({results.domestic_flow_L_s:.2f} × {results.k1_coefficient:.2f}) + {results.industrial_flow_L_s:.2f}" if not apply_k_to_ind else f"QMD = {results.total_flow_L_s:.2f} × {results.k1_coefficient:.2f}"
        k_diag_text_qmh = f"QMH = ({results.domestic_flow_L_s:.2f} × {results.k1_coefficient:.2f} × {results.k2_coefficient:.2f}) + {results.industrial_flow_L_s:.2f}" if not apply_k_to_ind else f"QMH = {results.q_max_daily_flow_L_s:.2f} × {results.k2_coefficient:.2f}"

        st.markdown(f"""
<div style="background:rgba(14, 38, 59, 0.95); border:1px solid #087E8B; border-radius:12px; padding:1.2rem 1.5rem; font-family:'Inter', sans-serif;">
<p style="font-size:14px; color:#CBD5E1; margin-bottom:1rem;">
A continuación se presenta el cálculo paso a paso sustituyendo exactamente los datos de entrada configurados en este momento:
</p>
<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:1.2rem;">

<div style="background:rgba(10, 25, 40, 0.85); border-left:3px solid #38B6C5; border-radius:6px; padding:0.8rem 1rem;">
<div style="font-size:12px; color:#38B6C5; font-weight:700;">PASO 1: DOTACIÓN BRUTA (Art. 44)</div>
<div style="font-family:'JetBrains Mono', monospace; font-size:13px; color:#FFFFFF; margin-top:4px;">
D_bruta = {results.domestic_endowment_net:.1f} / (1 - {results.domestic_losses_pct/100:.4f})<br>
<b style="color:#38B6C5;">D_bruta = {results.domestic_endowment_gross:.2f} L/hab·día</b>
</div>
</div>

<div style="background:rgba(10, 25, 40, 0.85); border-left:3px solid #087E8B; border-radius:6px; padding:0.8rem 1rem;">
<div style="font-size:12px; color:#087E8B; font-weight:700;">PASO 2: CAUDAL Y VOLUMEN DOMÉSTICO</div>
<div style="font-family:'JetBrains Mono', monospace; font-size:13px; color:#FFFFFF; margin-top:4px;">
Qmd_dom = ({results.domestic_population:,} × {results.domestic_endowment_gross:.2f}) / 86,400<br>
<b style="color:#087E8B;">Qmd_dom = {results.domestic_flow_L_s:.2f} L/s</b> ({results.domestic_volume_m3_day:,.1f} m³/d)
</div>
</div>

<div style="background:rgba(10, 25, 40, 0.85); border-left:3px solid #38B6C5; border-radius:6px; padding:0.8rem 1rem;">
<div style="font-size:12px; color:#38B6C5; font-weight:700;">PASO 3: CAUDAL Y VOLUMEN INDUSTRIAL</div>
<div style="font-family:'JetBrains Mono', monospace; font-size:13px; color:#FFFFFF; margin-top:4px;">
V_ind = Σ Vi = {results.industrial_volume_m3_day:,.2f} m³/día<br>
Qmd_ind = {results.industrial_volume_m3_day:,.2f} / 86.40<br>
<b style="color:#38B6C5;">Qmd_ind = {results.industrial_flow_L_s:.2f} L/s</b>
</div>
</div>

<div style="background:rgba(10, 25, 40, 0.85); border-left:3px solid #80DEEA; border-radius:6px; padding:0.8rem 1rem;">
<div style="font-size:12px; color:#80DEEA; font-weight:700;">PASO 4: CAUDAL MEDIO DIARIO TOTAL (Qmd)</div>
<div style="font-family:'JetBrains Mono', monospace; font-size:13px; color:#FFFFFF; margin-top:4px;">
Qmd = {results.domestic_flow_L_s:.2f} + {results.industrial_flow_L_s:.2f}<br>
<b style="color:#80DEEA;">Qmd = {results.total_flow_L_s:.2f} L/s</b> ({results.total_volume_m3_day:,.1f} m³/d)
</div>
</div>

<div style="background:rgba(10, 25, 40, 0.85); border-left:3px solid #25866C; border-radius:6px; padding:0.8rem 1rem;">
<div style="font-size:12px; color:#25866C; font-weight:700;">PASO 5: CAUDAL MÁXIMO DIARIO (QMD)</div>
<div style="font-family:'JetBrains Mono', monospace; font-size:13px; color:#FFFFFF; margin-top:4px;">
k₁ = {results.k1_coefficient:.2f}<br>
{k_diag_text_qmd}<br>
<b style="color:#25866C;">QMD = {results.q_max_daily_flow_L_s:.2f} L/s</b> ({results.q_max_daily_volume_m3_day:,.1f} m³/d)
</div>
</div>

<div style="background:rgba(10, 25, 40, 0.85); border-left:3px solid #83B88C; border-radius:6px; padding:0.8rem 1rem;">
<div style="font-size:12px; color:#83B88C; font-weight:700;">PASO 6: CAUDAL MÁXIMO HORARIO (QMH)</div>
<div style="font-family:'JetBrains Mono', monospace; font-size:13px; color:#FFFFFF; margin-top:4px;">
k₂ = {results.k2_coefficient:.2f}<br>
{k_diag_text_qmh}<br>
<b style="color:#83B88C;">QMH = {results.q_max_hourly_flow_L_s:.2f} L/s</b> ({results.q_max_hourly_volume_m3_day:,.1f} m³/d)
</div>
</div>

</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.info("Corrige las inconsistencias o advertencias en los parámetros de entrada para visualizar la sustitución numérica de este proyecto.")


# =============================================================================
# SECCIÓN 4: EXPORTACIÓN DE INFORMES (EXCEL PROFESIONAL Y PDF)
# =============================================================================
with tab_exportacion:
    st.markdown('<div class="card-title">📥 Generación de Memorias y Documentos Técnicos</div>', unsafe_allow_html=True)
    st.markdown("""
    Descarga la memoria completa de cálculo estructurada conforme a estándares de consultoría hidráulica y la identidad **AQUAMARIS**.
    La memoria en Excel incluye 5 hojas técnicas generadas con la tipografía corporativa **Calibri**, fórmulas comprobables en celdas, valores numéricos reales y auditoría de concordancia `Python vs Excel`.
    """)

    if results and not calc_error:
        excel_bytes = generate_professional_excel(results)
        pdf_bytes = generate_professional_pdf(results)

        col_ex_main, col_ex_pdf = st.columns(2, gap="large")

        with col_ex_main:
            st.markdown("""<div style="background:rgba(14, 38, 59, 0.92); backdrop-filter:blur(10px); border:2px solid #087E8B; border-radius:12px; padding:1.4rem; box-shadow:0 8px 24px rgba(0, 0, 0, 0.45);">
<h4 style="font-family:'Manrope', sans-serif; font-size:19px; color:#38B6C5; margin-top:0;">📊 Libro Completo en Excel (.xlsx)</h4>
<p style="font-family:'Inter', sans-serif; font-size:14px; color:#CBD5E1; line-height:1.5;">
Incluye 5 hojas técnicas formalizadas con tipografía Calibri, fórmulas vivas en celda y diseño corporativo:
</p>
<ul style="font-family:'Inter', sans-serif; font-size:14px; color:#F1F5F9; padding-left:1.2rem; line-height:1.65;">
<li><b style="color:#38B6C5;">01_Resumen:</b> Cuadro ejecutivo y gráfico de caudales.</li>
<li><b style="color:#38B6C5;">02_Datos_Entrada:</b> Parámetros del proyecto y marco normativo.</li>
<li><b style="color:#38B6C5;">03_Memoria_Calculo:</b> Fórmulas auditables enlazadas a celdas.</li>
<li><b style="color:#38B6C5;">04_Detalle_Industrial:</b> Inventario con caudales en turno (Qop).</li>
<li><b style="color:#38B6C5;">05_Verificacion:</b> Chequeo Python vs Excel (Diferencia = 0.000).</li>
</ul>
</div>""", unsafe_allow_html=True)

            st.download_button(
                label="📥 Descargar Memoria en Excel (.xlsx)",
                data=excel_bytes.getvalue(),
                file_name=f"AQUAMARIS_Demanda_Agua_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_ex_pdf:
            st.markdown("""<div style="background:rgba(14, 38, 59, 0.92); backdrop-filter:blur(10px); border:1px solid rgba(56, 182, 197, 0.45); border-radius:12px; padding:1.4rem; box-shadow:0 8px 24px rgba(0, 0, 0, 0.45);">
<h4 style="font-family:'Manrope', sans-serif; font-size:19px; color:#83B88C; margin-top:0;">📄 Informe Técnico en PDF (.pdf)</h4>
<p style="font-family:'Inter', sans-serif; font-size:14px; color:#CBD5E1; line-height:1.5;">
Documento formal maquetado con la identidad AQUAMARIS listo para adjuntar a expedientes técnicos:
</p>
<ul style="font-family:'Inter', sans-serif; font-size:14px; color:#F1F5F9; padding-left:1.2rem; line-height:1.65;">
<li>Tablas de caudales medios y máximos consolidados.</li>
<li>Control de cumplimiento de Artículos 43 y 44 Res. 0330.</li>
<li>Desglose de usuarios industriales y caudales en turno.</li>
<li>Notas y consideraciones de ingeniería sanitaria.</li>
</ul>
</div>""", unsafe_allow_html=True)

            st.download_button(
                label="📥 Descargar Informe Técnico en PDF (.pdf)",
                data=pdf_bytes.getvalue(),
                file_name=f"AQUAMARIS_Informe_Demanda_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.warning("No es posible generar los archivos de exportación hasta que se corrijan las inconsistencias detectadas.")
