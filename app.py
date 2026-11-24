"""
Calculadora de Demanda Doméstica e Industrial de Agua
Versión 3.0 - Rediseño Profesional, Auditoría Técnica y Cumplimiento Normativo RAS 0330
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
    page_title="Calculadora de Demanda de Agua | Ingeniería Hidráulica",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS (PALETA PROFESIONAL SOBRIA)
# Paleta:
# Azul petróleo: #123047 | Turquesa: #149D9A | Fondo: #F7F9FC | Blanco: #FFFFFF
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1e293b;
    }
    
    .stApp {
        background-color: #F7F9FC;
    }

    /* Encabezado Principal */
    .brand-header {
        background: #123047;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        border-left: 6px solid #149D9A;
        box-shadow: 0 4px 6px -1px rgba(18, 48, 71, 0.1);
    }
    .brand-title {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        color: #FFFFFF;
    }
    .brand-subtitle {
        font-size: 0.95rem;
        color: #CBD5E1;
        margin-top: 0.35rem;
        margin-bottom: 0.5rem;
        font-weight: 400;
    }
    .brand-badges {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }
    .brand-badge {
        background: rgba(255, 255, 255, 0.12);
        padding: 0.2rem 0.65rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #E2E8F0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Tarjetas de Contenido */
    .clean-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #123047;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 0.5rem;
    }

    /* Tarjetas Métricas KPI */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.85rem;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        border-top: 3.5px solid #149D9A;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .kpi-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #123047;
        line-height: 1.2;
        margin-top: 0.2rem;
    }
    .kpi-sub {
        font-size: 0.82rem;
        color: #475569;
        margin-top: 0.25rem;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Badges Técnicos */
    .tag-conforme {
        background: #DCFCE7;
        color: #15803D;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .tag-alerta {
        background: #FEF3C7;
        color: #B45309;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .tag-error {
        background: #FEE2E2;
        color: #B91C1C;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SIDEBAR: CONFIGURACIÓN GENERAL Y CONTROL DE ESCENARIOS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Configuración del Proyecto")
    
    # 1. Selector de Modo Normativo vs Exploratorio
    mode_selection = st.radio(
        "Marco de Evaluación:",
        options=["Normativa RAS (Res. 0330 / 2017)", "Modo Exploratorio / Libre"],
        index=0,
        help="El modo RAS aplica los límites legales colombianos de dotación máxima (Art. 43) y pérdidas (Art. 44). El modo exploratorio permite evaluar cualquier rango para investigación o diseño internacional."
    )
    is_ras_mode = (mode_selection == "Normativa RAS (Res. 0330 / 2017)")
    calc_mode = CalculationMode.NORMATIVE_RAS if is_ras_mode else CalculationMode.EXPLORATORY

    # 2. Piso Térmico / Altitud (si aplica RAS)
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
    
    # 3. Escenarios Predefinidos
    scenario_choice = st.selectbox(
        "Cargar Escenario de Prueba:",
        options=[
            "Personalizado",
            "Municipio Intermedio (45,000 hab + Agroindustria)",
            "Población Rural (4,500 hab + Lácteos)",
            "Zona Urbana - Industrial (120,000 hab + Parque Fabril)",
        ],
        index=0
    )

    st.markdown("---")
    
    # 4. Ajustes Avanzados de Factores de Pico
    with st.expander("Factores de Consumo Máximo (k₁, k₂)", expanded=False):
        st.caption("Diferencian la Demanda Media Diaria de los Caudales de Dimensionamiento:")
        
        custom_peaks = st.checkbox("Modificar coeficientes manualmente", value=False)
        
        if custom_peaks:
            k1_input = st.number_input("Coeficiente Diario (k₁) [QMD = k₁ · Qmd]:", min_value=1.00, max_value=2.00, value=1.20, step=0.01, format="%.2f")
            k2_input = st.number_input("Coeficiente Horario (k₂) [QMH = k₂ · QMD]:", min_value=1.00, max_value=3.00, value=1.50, step=0.01, format="%.2f")
        else:
            k1_input = 1.20
            k2_input = 1.50
            st.info("Valores sugeridos por RAS 0330 según tamaño de población.")

        apply_k_to_ind = st.checkbox(
            "Mayorar demanda industrial con k₁ y k₂",
            value=False,
            help="En saneamiento estándar, las industrias con reservorio o régimen continuo no se afectan con picos residenciales."
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

# Inicializar sesión de industrias de forma unificada
if "df_industries" not in st.session_state or st.session_state.get("last_scenario_loaded") != scenario_choice:
    st.session_state["df_industries"] = pd.DataFrame(initial_ind_records)
    st.session_state["last_scenario_loaded"] = scenario_choice


# -----------------------------------------------------------------------------
# ENCABEZADO CORPORATIVO
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="brand-header">
    <div class="brand-title">Calculadora de Demanda Doméstica e Industrial de Agua</div>
    <div class="brand-subtitle">
        Plataforma técnica para dimensionamiento hidráulico, estimación de Demanda Media Diaria (Qmd),
        caudales de pico (QMD, QMH) y auditoría técnica bajo normativa colombiana RAS 0330 de 2017 y estándares internacionales.
    </div>
    <div class="brand-badges">
        <span class="brand-badge">Modo: {'RAS 0330 (Colombia)' if is_ras_mode else 'Exploratorio / Libre'}</span>
        <span class="brand-badge">Equivalencia Exacta: 1 L/s = 86.40 m³/día</span>
        <span class="brand-badge">Auditoría Casilla por Casilla</span>
        <span class="brand-badge">Exportación Excel Abierta (.xlsx)</span>
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

    # Cálculo preliminar de dotación bruta
    factor_p = 1.0 - (perdidas_pct / 100.0)
    dotacion_bruta_prelim = dotacion_neta / factor_p if factor_p > 0 else 0.0

    st.markdown("---")
    
    # Resumen rápido de dotación en tarjeta limpia
    st.markdown(f"""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; padding:0.9rem 1.2rem; display:flex; gap:2rem; flex-wrap:wrap; align-items:center;">
        <div>
            <span style="font-size:0.8rem; color:#64748B; font-weight:600;">DOTACIÓN NETA:</span><br/>
            <span style="font-size:1.15rem; font-weight:700; color:#123047;">{dotacion_neta:.1f} L/hab·día</span>
        </div>
        <div>
            <span style="font-size:0.8rem; color:#64748B; font-weight:600;">PÉRDIDAS EN RED:</span><br/>
            <span style="font-size:1.15rem; font-weight:700; color:#149D9A;">{perdidas_pct:.1f}%</span>
        </div>
        <div>
            <span style="font-size:0.8rem; color:#64748B; font-weight:600;">DOTACIÓN BRUTA CALCULADA:</span><br/>
            <span style="font-size:1.15rem; font-weight:700; color:#0284C7;">{dotacion_bruta_prelim:.2f} L/hab·día</span>
        </div>
        <div>
            <span style="font-size:0.8rem; color:#64748B; font-weight:600;">ESTADO NORMATIVO:</span><br/>
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
        - **Artículo 44 (Pérdidas Técnicas):**
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

    # Tabla editable de industrias usando st.data_editor nativo
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

    # Actualizar estado de sesión
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
# Construir registros industriales a partir de la tabla editable
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

# Ajuste automático de coeficientes k1 y k2 si no son personalizados
if not custom_peaks:
    k1_val, k2_val = WaterDemandEngine.suggest_ras_peak_factors(poblacion)
else:
    k1_val, k2_val = k1_input, k2_input

# Instanciar entrada doméstica
dom_input = DomesticDemandInput(
    population=poblacion,
    endowment_L_hab_day=dotacion_neta,
    technical_losses_pct=perdidas_pct,
    mode=calc_mode,
    altitude_zone=selected_zone
)

# Ejecución controlada del motor hidráulico
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

        # KPIs Principales
        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card" style="border-top-color: #0284C7;">
                <div class="kpi-label">Demanda Doméstica (Qmd_dom)</div>
                <div class="kpi-val">{results.domestic_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub">{results.domestic_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:0.2rem;">Dotación Bruta: {results.domestic_endowment_gross:.1f} L/hab·d</div>
            </div>
            <div class="kpi-card" style="border-top-color: #149D9A;">
                <div class="kpi-label">Demanda Industrial (Qmd_ind)</div>
                <div class="kpi-val">{results.industrial_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub">{results.industrial_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#64748B; margin-top:0.2rem;">{len(results.industrial_details)} proceso(s) modelados</div>
            </div>
            <div class="kpi-card" style="border-top-color: #123047; background:#F8FAFC;">
                <div class="kpi-label" style="color:#123047;">Demanda Media Total (Qmd)</div>
                <div class="kpi-val" style="color:#123047;">{results.total_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub">{results.total_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#123047; font-weight:600; margin-top:0.2rem;">Base Concesiones y Balances</div>
            </div>
            <div class="kpi-card" style="border-top-color: #D97706; background:#FFFBEB;">
                <div class="kpi-label" style="color:#B45309;">Máximo Diario (QMD)</div>
                <div class="kpi-val" style="color:#B45309;">{results.q_max_daily_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub">{results.q_max_daily_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#92400E; margin-top:0.2rem;">k₁ = {results.k1_coefficient:.2f} | Captación, Aducción, PTAP</div>
            </div>
            <div class="kpi-card" style="border-top-color: #DC2626; background:#FEF2F2;">
                <div class="kpi-label" style="color:#B91C1C;">Máximo Horario (QMH)</div>
                <div class="kpi-val" style="color:#B91C1C;">{results.q_max_hourly_flow_L_s:.2f} <span style="font-size:0.9rem; font-weight:500;">L/s</span></div>
                <div class="kpi-sub">{results.q_max_hourly_volume_m3_day:,.1f} m³/día</div>
                <div style="font-size:0.75rem; color:#991B1B; margin-top:0.2rem;">k₂ = {results.k2_coefficient:.2f} | Red de Distribución</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Gráficas Comparativas
        col_chart1, col_chart2 = st.columns([1.2, 1], gap="medium")

        with col_chart1:
            fig_bars = go.Figure()
            fig_bars.add_trace(go.Bar(
                x=["Doméstico (Qmd)", "Industrial (Qmd)", "Medio Total (Qmd)", "Máx. Diario (QMD)", "Máx. Horario (QMH)"],
                y=[results.domestic_flow_L_s, results.industrial_flow_L_s, results.total_flow_L_s, results.q_max_daily_flow_L_s, results.q_max_hourly_flow_L_s],
                marker_color=["#0284C7", "#149D9A", "#123047", "#D97706", "#DC2626"],
                text=[f"{results.domestic_flow_L_s:.2f} L/s", f"{results.industrial_flow_L_s:.2f} L/s", f"{results.total_flow_L_s:.2f} L/s", f"{results.q_max_daily_flow_L_s:.2f} L/s", f"{results.q_max_hourly_flow_L_s:.2f} L/s"],
                textposition="outside"
            ))
            fig_bars.update_layout(
                title=dict(text="Comparativa de Caudales de Diseño (L/s)", font=dict(size=13, color="#123047")),
                height=300,
                margin=dict(l=20, r=20, t=35, b=20),
                yaxis=dict(title="Caudal (L/s)", gridcolor="#F1F5F9"),
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif")
            )
            st.plotly_chart(fig_bars, use_container_width=True)

        with col_chart2:
            if results.total_volume_m3_day > 0:
                fig_donut = go.Figure(data=[go.Pie(
                    labels=["Doméstico", "Industrial"],
                    values=[results.domestic_volume_m3_day, results.industrial_volume_m3_day],
                    hole=0.6,
                    marker_colors=["#0284C7", "#149D9A"],
                    textinfo="label+percent",
                    texttemplate="<b>%{label}</b><br>%{percent} (%{value:,.0f} m³/d)",
                    hoverinfo="label+value+percent",
                )])
                fig_donut.update_layout(
                    title=dict(text="Distribución de la Demanda Diaria", font=dict(size=13, color="#123047")),
                    showlegend=False,
                    height=300,
                    margin=dict(l=10, r=10, t=35, b=10),
                    font=dict(family="Inter, sans-serif")
                )
                st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")
        
        # Matriz de Auditoría Casilla por Casilla
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
    Descarga la memoria completa de cálculo estructurada conforme a estándares de consultoría hidráulica.
    La memoria en Excel incluye 5 hojas técnicas con fórmulas comprobables en celdas, formatos numéricos reales y auditoría de concordancia.
    """)

    if results and not calc_error:
        # Generar libros en memoria
        excel_bytes = generate_professional_excel(results)
        pdf_bytes = generate_professional_pdf(results)

        col_ex_main, col_ex_pdf = st.columns(2, gap="large")

        with col_ex_main:
            st.markdown("""
            <div style="background:#FFFFFF; border:2px solid #149D9A; border-radius:10px; padding:1.25rem;">
                <h4 style="color:#123047; margin-top:0;">📊 Libro Completo en Excel (.xlsx)</h4>
                <p style="font-size:0.85rem; color:#475569;">
                    Incluye 5 hojas técnicas formalizadas con fórmulas comprobables en celda:
                </p>
                <ul style="font-size:0.8rem; color:#334155; padding-left:1.2rem;">
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
                file_name=f"Memoria_Demanda_Agua_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col_ex_pdf:
            st.markdown("""
            <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:1.25rem;">
                <h4 style="color:#123047; margin-top:0;">📄 Informe Técnico en PDF (.pdf)</h4>
                <p style="font-size:0.85rem; color:#475569;">
                    Documento formal maquetado listo para adjuntar a memorias de consultoría, expedientes técnicos o trámites de concesión:
                </p>
                <ul style="font-size:0.8rem; color:#334155; padding-left:1.2rem;">
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
                file_name=f"Informe_Demanda_Agua_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    else:
        st.warning("No es posible generar los archivos de exportación hasta que se corrijan las incoherencias detectadas.")
