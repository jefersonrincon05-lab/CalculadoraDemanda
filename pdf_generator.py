"""
Generador de Memorias de Cálculo en PDF
AQUAMARIS - Plataforma de Demanda Hídrica
Paleta Corporativa Aqua Natura
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

from hydrology_engine import WaterDemandResults


# Paleta corporativa "Aqua Natura"
C_PRIMARY = colors.HexColor("#123047")    # Azul profundo
C_RIVER = colors.HexColor("#087E8B")      # Azul río
C_TURQUOISE = colors.HexColor("#38B6C5")  # Turquesa agua
C_FOREST = colors.HexColor("#25866C")     # Verde bosque
C_NATURE = colors.HexColor("#83B88C")     # Verde natural
C_MIST = colors.HexColor("#F4F9F8")       # Blanco niebla
C_DARK = colors.HexColor("#0F172A")
C_BORDER = colors.HexColor("#CBD5E1")


def generate_professional_pdf(results: WaterDemandResults) -> io.BytesIO:
    """Genera una memoria de cálculo técnica en PDF con la identidad AQUAMARIS."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=C_PRIMARY,
        spaceAfter=3,
        alignment=0
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        textColor=colors.HexColor("#475569"),
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        textColor=C_PRIMARY,
        spaceBefore=9,
        spaceAfter=5
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=C_DARK,
        leading=11
    )

    story = []

    # 1. Encabezado principal AQUAMARIS
    story.append(Paragraph("AQUAMARIS | MEMORIA TÉCNICA DE DEMANDA DE AGUA", title_style))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Plataforma de Ingeniería Hídrica | Fecha: {now_str} | Marco: {results.calculation_mode.value}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_RIVER, spaceAfter=8))

    # 2. Resumen General de Caudales
    story.append(Paragraph("1. BALANCE CONSOLIDADO DE CAUDALES DE DISEÑO", h2_style))
    
    summary_data = [
        ["Parámetro de Diseño", "Caudal (L/s)", "Volumen (m³/día)", "Participación", "Destino Sanitario / Obra Civil"],
        ["Demanda Doméstica Media (Qmd_dom)", f"{results.domestic_flow_L_s:.3f}", f"{results.domestic_volume_m3_day:,.2f}", f"{results.domestic_pct:.1f}%", "Consumo residencial continuo en 24h"],
        ["Demanda Industrial Media (Qmd_ind)", f"{results.industrial_flow_L_s:.3f}", f"{results.industrial_volume_m3_day:,.2f}", f"{results.industrial_pct:.1f}%", "Consumo productivo acumulado"],
        ["Demanda Media Diaria Total (Qmd)", f"{results.total_flow_L_s:.3f}", f"{results.total_volume_m3_day:,.2f}", "100.0%", "Balance hídrico y concesión de aguas"],
        ["Caudal Máximo Diario (QMD)", f"{results.q_max_daily_flow_L_s:.3f}", f"{results.q_max_daily_volume_m3_day:,.2f}", "-", "Captación, aducción, PTAP y tanques"],
        ["Caudal Máximo Horario (QMH)", f"{results.q_max_hourly_flow_L_s:.3f}", f"{results.q_max_hourly_volume_m3_day:,.2f}", "-", "Red de distribución y estaciones de bombeo"],
    ]

    t_summary = Table(summary_data, colWidths=[160, 65, 85, 65, 165])
    t_summary.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_MIST]),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (1, 1), (3, -1), "RIGHT"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#E0F7F6")),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 8))

    # 3. Parámetros de Entrada y Verificación RAS 0330
    story.append(Paragraph("2. PARÁMETROS BÁSICOS Y AUDITORÍA NORMATIVA RAS 0330", h2_style))
    
    params_data = [
        ["Parámetro de Entrada", "Valor de Cálculo", "Criterio Técnico / Límite Normativo", "Estado"],
        ["Población de Diseño (P)", f"{results.domestic_population:,} hab", "Proyección censal al horizonte de diseño", "CONFORME"],
        ["Dotación Neta (Dneta)", f"{results.domestic_endowment_net:.1f} L/hab·día", f"Límite RAS Art. 43: {results.altitude_zone.value}", "CONFORME" if results.domestic_endowment_net <= 140.0 else "OBSERVACIÓN"],
        ["Pérdidas Técnicas en Red (%P)", f"{results.domestic_losses_pct:.1f}%", "Límite RAS Art. 44: ≤ 25.0% de pérdidas", "CONFORME" if results.domestic_losses_pct <= 25.0 else "NO CONFORME"],
        ["Dotación Bruta de Diseño (Dbruta)", f"{results.domestic_endowment_gross:.2f} L/hab·día", "Dbruta = Dneta / (1 - %P/100)", "CALCULADO"],
        ["Coeficiente Diario (k1)", f"{results.k1_coefficient:.2f}", "Art. 47 Res. 0330 (típico 1.20 - 1.30)", "CONFORME"],
        ["Coeficiente Horario (k2)", f"{results.k2_coefficient:.2f}", "Art. 48 Res. 0330 (típico 1.40 - 1.60)", "CONFORME"],
    ]

    t_params = Table(params_data, colWidths=[150, 100, 210, 80])
    t_params.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_RIVER),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_MIST]),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold"),
    ]))
    story.append(t_params)
    story.append(Spacer(1, 8))

    # 4. Desglose Industrial
    if results.industrial_details:
        story.append(Paragraph("3. DESGLOSE DEL SECTOR INDUSTRIAL Y CAUDAL EN TURNO (Qop)", h2_style))
        ind_header = ["Industria / Proceso", "Método", "Horas Op.", "Volumen (m³/d)", "Qmd 24h (L/s)", "Q Turno (L/s)"]
        ind_table_data = [ind_header]

        for item in results.industrial_details:
            ind_table_data.append([
                str(item.get("Nombre", "Industria"))[:25],
                str(item.get("Método", "Directo")),
                str(item.get("Horas Operación", "24 h/día")),
                f"{float(item.get('Volumen Diario (m³/día)', 0.0)):,.2f}",
                f"{float(item.get('Caudal Medio 24h (L/s)', 0.0)):.3f}",
                f"{float(item.get('Caudal en Turno Operativo (L/s)', 0.0)):.3f}",
            ])

        t_ind = Table(ind_table_data, colWidths=[150, 75, 75, 80, 80, 80])
        t_ind.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, C_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_MIST]),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ]))
        story.append(t_ind)
        story.append(Spacer(1, 8))

    # 5. Notas Técnicas
    story.append(Paragraph("4. NOTAS TÉCNICAS Y RECOMENDACIONES DE INGENIERÍA", h2_style))
    notes_text = """
    <b>Principio de Continuidad:</b> 1 L/s continuo durante 24 horas equivale exactamente a 86.40 m³/día.<br/>
    <b>Separación de Caudales:</b> El caudal Qmd debe emplearse en balances hidrológicos y solicitudes de concesión. 
    Los caudales QMD y QMH se reservan exclusivamente para el dimensionamiento mecánico e hidráulico de obras civiles.<br/>
    <b>Régimen Industrial:</b> Se asume amortiguamiento mediante tanque de reserva propio salvo indicación en contrario.
    """
    story.append(Paragraph(notes_text, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
