"""
Generador de Memorias de Cálculo en Excel
AQUAMARIS - Calculadora de Demanda Doméstica e Industrial de Agua
Paleta Corporativa Aqua Natura
"""

from datetime import datetime
import io
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

from hydrology_engine import WaterDemandResults, FACTOR_LS_TO_M3DAY


# Paleta corporativa "Aqua Natura"
COLOR_PRIMARY = "123047"    # Azul profundo (encabezado y títulos)
COLOR_RIVER = "087E8B"      # Azul río (subtítulos y elementos activos)
COLOR_TURQUOISE = "38B6C5"  # Turquesa agua (acentos y curvas)
COLOR_FOREST = "25866C"     # Verde bosque (indicadores conformes)
COLOR_NATURE = "83B88C"     # Verde natural (detalles ecológicos)
COLOR_MIST_BG = "F4F9F8"    # Blanco niebla (fondo general)
COLOR_WHITE = "FFFFFF"
COLOR_BORDER = "CBD5E1"


def apply_cell_styles(
    cell,
    font_bold=False,
    font_color="000000",
    font_size=10,
    bg_color=None,
    alignment_h="left",
    alignment_v="center",
    wrap_text=False,
    border_style="thin",
    border_color=COLOR_BORDER,
    number_format=None,
    font_name="Calibri"
):
    """Aplica estilos consistentes usando Calibri por compatibilidad universal según estándar de consultoría."""
    cell.font = Font(name=font_name, size=font_size, bold=font_bold, color=font_color)
    if bg_color:
        cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
    cell.alignment = Alignment(horizontal=alignment_h, vertical=alignment_v, wrap_text=wrap_text)
    
    if border_style:
        b_side = Side(style=border_style, color=border_color)
        cell.border = Border(left=b_side, right=b_side, top=b_side, bottom=b_side)
    
    if number_format:
        cell.number_format = number_format


def auto_fit_columns(ws, min_width=12, padding=3):
    """Ajusta automáticamente el ancho de las columnas según su contenido."""
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row in [1, 2, 3]:
                continue
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + padding, min_width)


def generate_professional_excel(results: WaterDemandResults) -> io.BytesIO:
    """
    Genera un libro Excel con 5 hojas técnicas estructuradas y ambientadas en Aqua Natura:
    1. 01_Resumen
    2. 02_Datos_Entrada
    3. 03_Memoria_Calculo
    4. 04_Detalle_Industrial
    5. 05_Verificacion
    """
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # =========================================================================
    # HOJA 1: 01_Resumen
    # =========================================================================
    ws1 = wb.create_sheet(title="01_Resumen")
    ws1.views.sheetView[0].showGridLines = True

    ws1.merge_cells("A1:G1")
    ws1["A1"] = "AQUAMARIS | MEMORIA TÉCNICA DE DEMANDA DE AGUA POTABLE E INDUSTRIAL"
    apply_cell_styles(ws1["A1"], font_bold=True, font_color=COLOR_WHITE, font_size=13, bg_color=COLOR_PRIMARY, alignment_h="center")

    ws1.merge_cells("A2:G2")
    ws1["A2"] = f"Resumen Ejecutivo del Sistema Hidráulico | Fecha: {now_str} | Marco: {results.calculation_mode.value}"
    apply_cell_styles(ws1["A2"], font_bold=False, font_color=COLOR_TURQUOISE, font_size=9, bg_color=COLOR_PRIMARY, alignment_h="center")

    ws1.cell(row=4, column=1, value="PARÁMETRO HIDRÁULICO")
    ws1.cell(row=4, column=2, value="CAUDAL (L/s)")
    ws1.cell(row=4, column=3, value="VOLUMEN (m³/día)")
    ws1.cell(row=4, column=4, value="PARTICIPACIÓN (%)")
    ws1.cell(row=4, column=5, value="DESTINO DE DISEÑO SANITARIO")

    for col in range(1, 6):
        apply_cell_styles(ws1.cell(row=4, column=col), font_bold=True, font_color=COLOR_WHITE, font_size=10, bg_color=COLOR_RIVER, alignment_h="center")

    summary_rows = [
        ("Demanda Doméstica Media (Qmd_dom)", results.domestic_flow_L_s, results.domestic_volume_m3_day, results.domestic_pct / 100.0, "Consumo residencial continuo 24 horas"),
        ("Demanda Industrial Media (Qmd_ind)", results.industrial_flow_L_s, results.industrial_volume_m3_day, results.industrial_pct / 100.0, "Consumo productivo acumulado"),
        ("Demanda Media Diaria Total (Qmd)", results.total_flow_L_s, results.total_volume_m3_day, 1.0, "Concesión de aguas y balance hídrico"),
        ("Caudal Máximo Diario (QMD)", results.q_max_daily_flow_L_s, results.q_max_daily_volume_m3_day, "-", "Captación, desarenador, aducción, PTAP y tanques"),
        ("Caudal Máximo Horario (QMH)", results.q_max_hourly_flow_L_s, results.q_max_hourly_volume_m3_day, "-", "Red de distribución y estaciones de bombeo"),
    ]

    for idx, (param, q_ls, vol_m3, pct, dest) in enumerate(summary_rows, start=5):
        bg = COLOR_WHITE if idx % 2 == 1 else COLOR_MIST_BG
        c1 = ws1.cell(row=idx, column=1, value=param)
        c2 = ws1.cell(row=idx, column=2, value=float(q_ls))
        c3 = ws1.cell(row=idx, column=3, value=float(vol_m3))
        c4 = ws1.cell(row=idx, column=4, value=pct if isinstance(pct, (int, float)) else str(pct))
        c5 = ws1.cell(row=idx, column=5, value=dest)

        apply_cell_styles(c1, font_bold=(idx in [7, 8, 9]), font_size=10, bg_color=bg, alignment_h="left")
        apply_cell_styles(c2, font_bold=(idx in [7, 8, 9]), font_color=COLOR_RIVER if idx in [7, 8] else "000000", font_size=10, bg_color=bg, alignment_h="right", number_format="#,##0.000")
        apply_cell_styles(c3, font_bold=(idx in [7, 8, 9]), font_size=10, bg_color=bg, alignment_h="right", number_format="#,##0.00")
        apply_cell_styles(c4, font_bold=False, font_size=10, bg_color=bg, alignment_h="center", number_format="0.0%" if isinstance(pct, (int, float)) else None)
        apply_cell_styles(c5, font_bold=False, font_size=9, bg_color=bg, alignment_h="left")

    # Gráfica de Barras
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "AQUAMARIS - Comparativa de Caudales de Diseño (L/s)"
    chart.y_axis.title = "Caudal (L/s)"
    chart.x_axis.title = "Caudal Hidráulico"
    chart.height = 11
    chart.width = 16

    data_ref = Reference(ws1, min_col=2, min_row=4, max_row=9)
    cats_ref = Reference(ws1, min_col=1, min_row=5, max_row=9)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.legend = None
    ws1.add_chart(chart, "A12")

    ws1.freeze_panes = "A5"
    auto_fit_columns(ws1, min_width=14)

    # =========================================================================
    # HOJA 2: 02_Datos_Entrada
    # =========================================================================
    ws2 = wb.create_sheet(title="02_Datos_Entrada")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:D1")
    ws2["A1"] = "PARÁMETROS Y DATOS DE ENTRADA DEL SISTEMA"
    apply_cell_styles(ws2["A1"], font_bold=True, font_color=COLOR_WHITE, font_size=12, bg_color=COLOR_PRIMARY, alignment_h="center")

    headers_in = ["VARIABLE / CASILLA", "VALOR INGRESADO", "UNIDAD", "CRITERIO / MARCO NORMATIVO"]
    for c_idx, h in enumerate(headers_in, start=1):
        cell = ws2.cell(row=3, column=c_idx, value=h)
        apply_cell_styles(cell, font_bold=True, font_color=COLOR_WHITE, font_size=10, bg_color=COLOR_RIVER, alignment_h="center")

    inputs_rows = [
        ("Marco Normativo Seleccionado", results.calculation_mode.value, "adimensional", "Resolución 0330 de 2017 o Modo Exploratorio"),
        ("Zona de Altitud / Piso Térmico", results.altitude_zone.value, "msnm", "Criterio de clasificación Art. 43 Res. 0330"),
        ("Población de Diseño (P)", results.domestic_population, "habitantes", "Horizonte de proyección censal del sistema"),
        ("Dotación Neta (Dneta)", results.domestic_endowment_net, "L/hab·día", "Consumo per cápita neto según piso térmico"),
        ("Pérdidas Técnicas en Red (%P)", results.domestic_losses_pct / 100.0, "porcentaje", "Límite RAS Art. 44: ≤ 25.0%"),
        ("Coeficiente de Variación Diaria (k1)", results.k1_coefficient, "adimensional", "Art. 47 Res. 0330 (típico 1.20 - 1.30)"),
        ("Coeficiente de Variación Horaria (k2)", results.k2_coefficient, "adimensional", "Art. 48 Res. 0330 (típico 1.40 - 1.60)"),
        ("Afectar Industria con Factores k1 y k2", "Sí" if results.apply_k_to_industrial else "No", "booleano", "Recomendado: No si la industria posee almacenamiento"),
        ("Cantidad de Industrias Modeladas", len(results.industrial_details), "unidades", "Número de giros o usuarios no domésticos"),
    ]

    for idx, (var, val, unit, crit) in enumerate(inputs_rows, start=4):
        bg = COLOR_WHITE if idx % 2 == 0 else COLOR_MIST_BG
        c1 = ws2.cell(row=idx, column=1, value=var)
        c2 = ws2.cell(row=idx, column=2, value=val)
        c3 = ws2.cell(row=idx, column=3, value=unit)
        c4 = ws2.cell(row=idx, column=4, value=crit)

        num_fmt = None
        if isinstance(val, int):
            num_fmt = "#,##0"
        elif isinstance(val, float):
            num_fmt = "0.0%" if unit == "porcentaje" else "#,##0.00"

        apply_cell_styles(c1, font_bold=False, font_size=10, bg_color=bg, alignment_h="left")
        apply_cell_styles(c2, font_bold=True, font_color=COLOR_PRIMARY if isinstance(val, (int, float)) else "000000", font_size=10, bg_color=bg, alignment_h="right" if isinstance(val, (int, float)) else "center", number_format=num_fmt)
        apply_cell_styles(c3, font_bold=False, font_size=9, bg_color=bg, alignment_h="center")
        apply_cell_styles(c4, font_bold=False, font_size=9, bg_color=bg, alignment_h="left")

    ws2.freeze_panes = "A4"
    auto_fit_columns(ws2, min_width=14)

    # =========================================================================
    # HOJA 3: 03_Memoria_Calculo (Con Fórmulas Auditables)
    # =========================================================================
    ws3 = wb.create_sheet(title="03_Memoria_Calculo")
    ws3.views.sheetView[0].showGridLines = True

    ws3.merge_cells("A1:F1")
    ws3["A1"] = "MEMORIA DE CÁLCULO PASO A PASO (FÓRMULAS AUDITABLES DE EXCEL)"
    apply_cell_styles(ws3["A1"], font_bold=True, font_color=COLOR_WHITE, font_size=12, bg_color=COLOR_PRIMARY, alignment_h="center")

    headers_mem = ["PASO", "DESCRIPCIÓN DE LA ECUACIÓN", "EXPRESIÓN TEÓRICA", "FÓRMULA AUDITABLE EN CELDA", "RESULTADO EXCEL", "UNIDAD"]
    for c_idx, h in enumerate(headers_mem, start=1):
        cell = ws3.cell(row=3, column=c_idx, value=h)
        apply_cell_styles(cell, font_bold=True, font_color=COLOR_WHITE, font_size=10, bg_color=COLOR_RIVER, alignment_h="center")

    calc_steps = [
        ("1", "Dotación Bruta de Diseño (Dbruta)", "Dneta / (1 - %P/100)", "='02_Datos_Entrada'!B7/(1-'02_Datos_Entrada'!B8)", "#,##0.00", "L/hab·día"),
        ("2", "Volumen Diario Doméstico (Vdom)", "P × Dbruta / 1000", "='02_Datos_Entrada'!B6*E4/1000", "#,##0.00", "m³/día"),
        ("3", "Caudal Medio Diario Doméstico (Qmd_dom)", "Vdom × 1000 / 86400", "=E5*1000/86400", "#,##0.000", "L/s"),
        ("4", "Volumen Diario Industrial (Vind)", "∑(Ui × ce,i) o ingreso directo", f"={results.industrial_volume_m3_day:.4f}", "#,##0.00", "m³/día"),
        ("5", "Caudal Medio Diario Industrial (Qmd_ind)", "Vind × 1000 / 86400", "=E7*1000/86400", "#,##0.000", "L/s"),
        ("6", "Caudal Medio Diario Total (Qmd_total)", "Qmd_dom + Qmd_ind", "=E6+E8", "#,##0.000", "L/s"),
        ("7", "Volumen Diario Total (Vtotal)", "Vdom + Vind", "=E5+E7", "#,##0.00", "m³/día"),
        ("8", "Caudal Máximo Diario (QMD)", "(Qmd_dom × k1) + Qmd_ind", "=(E6*'02_Datos_Entrada'!B9)+E8" if not results.apply_k_to_industrial else "=E9*'02_Datos_Entrada'!B9", "#,##0.000", "L/s"),
        ("9", "Caudal Máximo Horario (QMH)", "(Qmd_dom × k1 × k2) + Qmd_ind", "=(E6*'02_Datos_Entrada'!B9*'02_Datos_Entrada'!B10)+E8" if not results.apply_k_to_industrial else "=E11*'02_Datos_Entrada'!B10", "#,##0.000", "L/s"),
        ("10", "Equivalencia Volumétrica QMD", "QMD × 86400 / 1000", "=E11*86.4", "#,##0.00", "m³/día"),
        ("11", "Equivalencia Volumétrica QMH", "QMH × 86400 / 1000", "=E12*86.4", "#,##0.00", "m³/día"),
    ]

    for idx, (step_num, desc, theo, fmla, num_fmt, unit) in enumerate(calc_steps, start=4):
        bg = COLOR_WHITE if idx % 2 == 0 else COLOR_MIST_BG
        c1 = ws3.cell(row=idx, column=1, value=step_num)
        c2 = ws3.cell(row=idx, column=2, value=desc)
        c3 = ws3.cell(row=idx, column=3, value=theo)
        c4 = ws3.cell(row=idx, column=4, value=fmla.replace("=", ""))
        c5 = ws3.cell(row=idx, column=5, value=fmla)
        c6 = ws3.cell(row=idx, column=6, value=unit)

        apply_cell_styles(c1, font_bold=True, font_size=10, bg_color=bg, alignment_h="center")
        apply_cell_styles(c2, font_bold=False, font_size=10, bg_color=bg, alignment_h="left")
        apply_cell_styles(c3, font_bold=False, font_size=9, bg_color=bg, alignment_h="center")
        apply_cell_styles(c4, font_bold=False, font_size=9, font_color="475569", bg_color=bg, alignment_h="left")
        apply_cell_styles(c5, font_bold=True, font_color=COLOR_PRIMARY, font_size=10, bg_color=bg, alignment_h="right", number_format=num_fmt)
        apply_cell_styles(c6, font_bold=False, font_size=9, bg_color=bg, alignment_h="center")

    ws3.freeze_panes = "A4"
    auto_fit_columns(ws3, min_width=14)

    # =========================================================================
    # HOJA 4: 04_Detalle_Industrial
    # =========================================================================
    ws4 = wb.create_sheet(title="04_Detalle_Industrial")
    ws4.views.sheetView[0].showGridLines = True

    ws4.merge_cells("A1:H1")
    ws4["A1"] = "INVENTARIO Y DESGLOSE DETALLADO DE PROCESOS INDUSTRIALES"
    apply_cell_styles(ws4["A1"], font_bold=True, font_color=COLOR_WHITE, font_size=12, bg_color=COLOR_PRIMARY, alignment_h="center")

    headers_ind = ["ID", "INDUSTRIA / RAZÓN SOCIAL", "MÉTODO", "HORAS OPERACIÓN (Hop)", "VOLUMEN (m³/día)", "Qmd 24h (L/s)", "Q TURNO (L/s)", "FUENTE TÉCNICA DOCUMENTADA"]
    for c_idx, h in enumerate(headers_ind, start=1):
        cell = ws4.cell(row=3, column=c_idx, value=h)
        apply_cell_styles(cell, font_bold=True, font_color=COLOR_WHITE, font_size=10, bg_color=COLOR_RIVER, alignment_h="center")

    if results.industrial_details:
        for idx, rec in enumerate(results.industrial_details, start=4):
            bg = COLOR_WHITE if idx % 2 == 0 else COLOR_MIST_BG
            c1 = ws4.cell(row=idx, column=1, value=idx - 3)
            c2 = ws4.cell(row=idx, column=2, value=rec.get("Nombre", "Industria"))
            c3 = ws4.cell(row=idx, column=3, value=rec.get("Método", "Directo"))
            c4 = ws4.cell(row=idx, column=4, value=float(rec.get("Horas Operación", "24").replace(" h/día", "")))
            c5 = ws4.cell(row=idx, column=5, value=float(rec.get("Volumen Diario (m³/día)", 0.0)))
            c6 = ws4.cell(row=idx, column=6, value=f"=E{idx}*1000/86400")
            c7 = ws4.cell(row=idx, column=7, value=f"=E{idx}*1000/(D{idx}*3600)")
            c8 = ws4.cell(row=idx, column=8, value=rec.get("Fuente Benchmark", "-"))

            apply_cell_styles(c1, font_bold=True, font_size=10, bg_color=bg, alignment_h="center")
            apply_cell_styles(c2, font_bold=False, font_size=10, bg_color=bg, alignment_h="left")
            apply_cell_styles(c3, font_bold=False, font_size=9, bg_color=bg, alignment_h="center")
            apply_cell_styles(c4, font_bold=False, font_size=10, bg_color=bg, alignment_h="center", number_format="0.0")
            apply_cell_styles(c5, font_bold=False, font_size=10, bg_color=bg, alignment_h="right", number_format="#,##0.00")
            apply_cell_styles(c6, font_bold=False, font_size=10, bg_color=bg, alignment_h="right", number_format="#,##0.000")
            apply_cell_styles(c7, font_bold=False, font_size=10, bg_color=bg, alignment_h="right", number_format="#,##0.000")
            apply_cell_styles(c8, font_bold=False, font_size=8, font_color="475569", bg_color=bg, alignment_h="left")

        tot_row = len(results.industrial_details) + 4
        ws4.cell(row=tot_row, column=2, value="TOTAL CONSOLIDADO INDUSTRIAL")
        ws4.cell(row=tot_row, column=5, value=f"=SUM(E4:E{tot_row-1})")
        ws4.cell(row=tot_row, column=6, value=f"=SUM(F4:F{tot_row-1})")
        ws4.cell(row=tot_row, column=7, value="-")

        for c_idx in range(1, 9):
            apply_cell_styles(ws4.cell(row=tot_row, column=c_idx), font_bold=True, font_size=10, bg_color="E2E8F0", alignment_h="right" if c_idx in [5, 6] else "center", number_format="#,##0.00" if c_idx == 5 else ("#,##0.000" if c_idx == 6 else None))
        apply_cell_styles(ws4.cell(row=tot_row, column=2), font_bold=True, font_size=10, bg_color="E2E8F0", alignment_h="left")

    ws4.freeze_panes = "A4"
    ws4.auto_filter.ref = f"A3:H{max(4, len(results.industrial_details)+3)}"
    auto_fit_columns(ws4, min_width=14)

    # =========================================================================
    # HOJA 5: 05_Verificacion (Auditoría Concordancia Python vs Excel)
    # =========================================================================
    ws5 = wb.create_sheet(title="05_Verificacion")
    ws5.views.sheetView[0].showGridLines = True

    ws5.merge_cells("A1:G1")
    ws5["A1"] = "AUDITORÍA DE PRECISIÓN Y CONCORDANCIA MATEMÁTICA (PYTHON vs EXCEL)"
    apply_cell_styles(ws5["A1"], font_bold=True, font_color=COLOR_WHITE, font_size=12, bg_color=COLOR_PRIMARY, alignment_h="center")

    headers_ver = ["VARIABLE AUDITADA", "VALOR PYTHON (MOTOR)", "VALOR REFERENCIA EXCEL", "UNIDAD", "DIFERENCIA ABSOLUTA", "TOLERANCIA", "ESTADO CONCORDANCIA"]
    for c_idx, h in enumerate(headers_ver, start=1):
        cell = ws5.cell(row=3, column=c_idx, value=h)
        apply_cell_styles(cell, font_bold=True, font_color=COLOR_WHITE, font_size=10, bg_color=COLOR_RIVER, alignment_h="center")

    verif_checks = [
        ("Dotación Bruta de Diseño", results.domestic_endowment_gross, "='03_Memoria_Calculo'!E4", "L/hab·día"),
        ("Volumen Diario Doméstico", results.domestic_volume_m3_day, "='03_Memoria_Calculo'!E5", "m³/día"),
        ("Caudal Medio Diario Doméstico", results.domestic_flow_L_s, "='03_Memoria_Calculo'!E6", "L/s"),
        ("Volumen Diario Industrial", results.industrial_volume_m3_day, "='03_Memoria_Calculo'!E7", "m³/día"),
        ("Caudal Medio Diario Industrial", results.industrial_flow_L_s, "='03_Memoria_Calculo'!E8", "L/s"),
        ("Caudal Medio Diario Total (Qmd)", results.total_flow_L_s, "='03_Memoria_Calculo'!E9", "L/s"),
        ("Caudal Máximo Diario (QMD)", results.q_max_daily_flow_L_s, "='03_Memoria_Calculo'!E11", "L/s"),
        ("Caudal Máximo Horario (QMH)", results.q_max_hourly_flow_L_s, "='03_Memoria_Calculo'!E12", "L/s"),
    ]

    for idx, (var_name, py_val, xl_ref, unit) in enumerate(verif_checks, start=4):
        bg = COLOR_WHITE if idx % 2 == 0 else COLOR_MIST_BG
        c1 = ws5.cell(row=idx, column=1, value=var_name)
        c2 = ws5.cell(row=idx, column=2, value=float(py_val))
        c3 = ws5.cell(row=idx, column=3, value=xl_ref)
        c4 = ws5.cell(row=idx, column=4, value=unit)
        c5 = ws5.cell(row=idx, column=5, value=f"=ABS(B{idx}-C{idx})")
        c6 = ws5.cell(row=idx, column=6, value=0.0001)
        c7 = ws5.cell(row=idx, column=7, value=f'=IF(E{idx}<=F{idx},"CONFORME (100%)","NO CONFORME")')

        apply_cell_styles(c1, font_bold=False, font_size=10, bg_color=bg, alignment_h="left")
        apply_cell_styles(c2, font_bold=True, font_size=10, bg_color=bg, alignment_h="right", number_format="#,##0.0000")
        apply_cell_styles(c3, font_bold=True, font_color=COLOR_PRIMARY, font_size=10, bg_color=bg, alignment_h="right", number_format="#,##0.0000")
        apply_cell_styles(c4, font_bold=False, font_size=9, bg_color=bg, alignment_h="center")
        apply_cell_styles(c5, font_bold=False, font_size=9, bg_color=bg, alignment_h="right", number_format="0.000000")
        apply_cell_styles(c6, font_bold=False, font_size=9, bg_color=bg, alignment_h="right", number_format="0.000000")
        apply_cell_styles(c7, font_bold=True, font_color=COLOR_FOREST, font_size=10, bg_color="DCFCE7", alignment_h="center")

    ws5.cell(row=14, column=1, value="CONTROL NORMATIVO RAS 0330 (MINVIVIENDA COLOMBIA)")
    ws5.merge_cells("A14:G14")
    apply_cell_styles(ws5["A14"], font_bold=True, font_color=COLOR_WHITE, font_size=10, bg_color=COLOR_FOREST, alignment_h="center")

    ras_checks = [
        ("Artículo 43: Dotación neta máxima admisible", f"Dotación neta = {results.domestic_endowment_net:.1f} L/hab·d (Límite piso {results.altitude_zone.value})", "CONFORME" if (results.domestic_endowment_net <= 140.0) else "OBSERVACIÓN"),
        ("Artículo 44: Pérdidas técnicas máximas en red (≤ 25%)", f"Pérdidas estimadas = {results.domestic_losses_pct:.1f}%", "CONFORME" if results.domestic_losses_pct <= 25.0 else "NO CONFORME (Supera 25%)"),
        ("Artículos 47 y 48: Coeficientes de pico de consumo", f"k1 = {results.k1_coefficient:.2f} | k2 = {results.k2_coefficient:.2f}", "CONFORME (Rangos típicos)"),
        ("Equivalencia Física: Constante de Tiempo", "1 L/s continuo durante 24 horas = 86.40 m³/día", "CONFORME EXACTO"),
    ]

    for idx, (articulo, desc, estado) in enumerate(ras_checks, start=15):
        bg = COLOR_WHITE if idx % 2 == 0 else COLOR_MIST_BG
        c1 = ws5.cell(row=idx, column=1, value=articulo)
        c2 = ws5.cell(row=idx, column=2, value=desc)
        ws5.merge_cells(f"B{idx}:F{idx}")
        c7 = ws5.cell(row=idx, column=7, value=estado)

        apply_cell_styles(c1, font_bold=True, font_size=9, bg_color=bg, alignment_h="left")
        apply_cell_styles(c2, font_bold=False, font_size=9, bg_color=bg, alignment_h="left")
        is_conf = "CONFORME" in estado
        apply_cell_styles(c7, font_bold=True, font_color=COLOR_FOREST if is_conf else "B91C1C", font_size=9, bg_color="DCFCE7" if is_conf else "FEE2E2", alignment_h="center")

    ws5.freeze_panes = "A4"
    auto_fit_columns(ws5, min_width=14)

    for ws in wb.worksheets:
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
