"""
Pruebas Unitarias y Auditoría Científica
Calculadora de Demanda Doméstica e Industrial de Agua
Versión 3.0 - Validación Normativa RAS 0330, Modo Exploratorio e Integridad de Excel/PDF
"""

import io
import pytest
import openpyxl
from hydrology_engine import (
    SECONDS_PER_DAY,
    LITERS_PER_M3,
    FACTOR_LS_TO_M3DAY,
    m3_day_to_L_s,
    L_s_to_m3_day,
    CalculationMode,
    AltitudeZone,
    DomesticDemandInput,
    IndustrialRecord,
    WaterDemandEngine,
)
from excel_generator import generate_professional_excel
from pdf_generator import generate_professional_pdf


class TestHydraulicConversions:
    """Verifica las conversiones de unidades fundamentales y dimensionales."""

    def test_constants_accuracy(self):
        """1 día = 86400 s, 1 m³ = 1000 L -> Factor exacto = 86.40"""
        assert SECONDS_PER_DAY == 86400.0
        assert LITERS_PER_M3 == 1000.0
        assert pytest.approx(FACTOR_LS_TO_M3DAY, rel=1e-9) == 86.40

    def test_conversion_roundtrip(self):
        """Verifica que la conversión m3/día <-> L/s sea simétrica y exacta."""
        test_values_m3 = [0.0, 1.0, 86.4, 500.0, 10000.0, 12345.67]
        for v in test_values_m3:
            q_ls = m3_day_to_L_s(v)
            v_back = L_s_to_m3_day(q_ls)
            assert pytest.approx(v, rel=1e-9) == v_back

    def test_known_equivalence(self):
        """Un caudal continuo de 1 L/s genera exactamente 86.40 m³/día."""
        assert pytest.approx(L_s_to_m3_day(1.0), rel=1e-9) == 86.40
        assert pytest.approx(m3_day_to_L_s(86.40), rel=1e-9) == 1.0


class TestDomesticDemandRASCompliance:
    """Verifica el cumplimiento de la Resolución 0330 de 2017 (RAS Colombia)."""

    def test_ras_altitude_caps_cold(self):
        """Clima Frío (> 2000 msnm): Dotación neta máxima = 120 L/hab·día."""
        inp_valid = DomesticDemandInput(
            population=10000,
            endowment_L_hab_day=120.0,
            technical_losses_pct=20.0,
            mode=CalculationMode.NORMATIVE_RAS,
            altitude_zone=AltitudeZone.COLD
        )
        assert inp_valid.validate_strict().is_valid is True

        # Si supera 120 en modo RAS debe rechazarlo
        inp_invalid = DomesticDemandInput(
            population=10000,
            endowment_L_hab_day=125.0,
            technical_losses_pct=20.0,
            mode=CalculationMode.NORMATIVE_RAS,
            altitude_zone=AltitudeZone.COLD
        )
        rep = inp_invalid.validate_strict()
        assert rep.is_valid is False
        assert any("Art. 43" in err for err in rep.errors)

    def test_ras_altitude_caps_temperate_and_warm(self):
        """Clima Templado (máx 130) y Clima Cálido (máx 140)."""
        inp_temp = DomesticDemandInput(10000, 130.0, 20.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.TEMPERATE)
        assert inp_temp.validate_strict().is_valid is True

        inp_warm = DomesticDemandInput(10000, 140.0, 20.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.WARM)
        assert inp_warm.validate_strict().is_valid is True

        inp_warm_bad = DomesticDemandInput(10000, 145.0, 20.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.WARM)
        assert inp_warm_bad.validate_strict().is_valid is False

    def test_ras_max_technical_losses(self):
        """Art. 44 Res. 0330: Pérdidas técnicas máximas admisibles = 25.0%."""
        inp_loss_ok = DomesticDemandInput(10000, 120.0, 25.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.TEMPERATE)
        assert inp_loss_ok.validate_strict().is_valid is True

        inp_loss_bad = DomesticDemandInput(10000, 120.0, 26.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.TEMPERATE)
        rep = inp_loss_bad.validate_strict()
        assert rep.is_valid is False
        assert any("Art. 44" in err for err in rep.errors)


class TestExploratoryModeFlexibility:
    """Verifica que el modo exploratorio permita evaluar valores fuera de RAS sin bloqueo."""

    def test_exploratory_mode_allows_higher_values(self):
        inp_exp = DomesticDemandInput(
            population=10000,
            endowment_L_hab_day=280.0,  # Superior a RAS
            technical_losses_pct=35.0,  # Superior al 25% de RAS
            mode=CalculationMode.EXPLORATORY,
            altitude_zone=AltitudeZone.TEMPERATE
        )
        rep = inp_exp.validate_strict()
        assert rep.is_valid is True
        assert len(rep.warnings) >= 1

    def test_reject_incoherent_physical_values_even_in_exploratory(self):
        """Población <= 0 o pérdidas >= 60% se rechazan siempre por imposibilidad física."""
        inp_bad_pop = DomesticDemandInput(0, 150.0, 20.0, CalculationMode.EXPLORATORY)
        assert inp_bad_pop.validate_strict().is_valid is False

        inp_bad_loss = DomesticDemandInput(5000, 150.0, 65.0, CalculationMode.EXPLORATORY)
        assert inp_bad_loss.validate_strict().is_valid is False


class TestIndustrialDemandAndShiftFlow:
    """Verifica caudales de 24h y caudales en turno operativo (Qop)."""

    def test_industrial_shift_operating_flow(self):
        """
        Consumo: 120 m³/día en turno de 8 horas:
        Qmd (24h) = 120 / 86.40 = 1.38889 L/s
        Qop (8h)  = 120 * 1000 / (8 * 3600) = 4.16667 L/s
        Relación exacta: Qop / Qmd = 24 / 8 = 3.0
        """
        rec = IndustrialRecord(
            name="Planta Quesera",
            mode="direct",
            direct_consumption_m3_day=120.0,
            operating_hours_per_day=8.0
        )
        assert rec.validate_strict().is_valid is True
        assert pytest.approx(rec.calculate_flow_L_s(), rel=1e-5) == 1.38889
        assert pytest.approx(rec.calculate_operating_flow_L_s(), rel=1e-5) == 4.16667
        assert pytest.approx(rec.calculate_operating_flow_L_s() / rec.calculate_flow_L_s(), rel=1e-5) == 3.0

    def test_specific_consumption_modes(self):
        rec = IndustrialRecord(
            name="Refrescos",
            mode="specific",
            units_per_day=10000.0,
            specific_consumption=2.5,
            specific_unit="L/unidad"
        )
        assert pytest.approx(rec.calculate_volume_m3_day(), rel=1e-9) == 25.0
        assert pytest.approx(rec.calculate_flow_L_s(), rel=1e-5) == 25.0 / 86.40


class TestSystemIntegrationAndPeakFactors:
    """Verifica la agregación integral del sistema y opciones de pico."""

    def test_zero_industries_residential_only(self):
        """Sistema exclusivamente residencial (sin componente industrial)."""
        dom = DomesticDemandInput(10000, 120.0, 20.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.TEMPERATE)
        res = WaterDemandEngine.calculate_total_system_demand(dom, [], k1=1.20, k2=1.50)

        assert res.industrial_volume_m3_day == 0.0
        assert res.industrial_flow_L_s == 0.0
        assert pytest.approx(res.total_flow_L_s, rel=1e-9) == res.domestic_flow_L_s
        assert pytest.approx(res.domestic_pct, rel=1e-9) == 100.0
        assert pytest.approx(res.industrial_pct, rel=1e-9) == 0.0

    def test_apply_k_to_industrial_toggle(self):
        """Verifica diferencia al mayorar o no la industria con k1 y k2."""
        dom = DomesticDemandInput(10000, 120.0, 20.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.TEMPERATE)
        ind = [IndustrialRecord("Fabrica", "direct", direct_consumption_m3_day=86.4)] # Exactamente 1.0 L/s

        res_no_k = WaterDemandEngine.calculate_total_system_demand(dom, ind, k1=1.20, k2=1.50, apply_k_to_industrial=False)
        res_with_k = WaterDemandEngine.calculate_total_system_demand(dom, ind, k1=1.20, k2=1.50, apply_k_to_industrial=True)

        # Cuando NO aplica a la industria: QMD = (Qdom * 1.20) + 1.0
        assert pytest.approx(res_no_k.q_max_daily_flow_L_s, rel=1e-5) == (res_no_k.domestic_flow_L_s * 1.20) + 1.0

        # Cuando SÍ aplica a la industria: QMD = (Qdom + 1.0) * 1.20
        assert pytest.approx(res_with_k.q_max_daily_flow_L_s, rel=1e-5) == (res_with_k.domestic_flow_L_s + 1.0) * 1.20
        assert res_with_k.q_max_daily_flow_L_s > res_no_k.q_max_daily_flow_L_s


class TestExcelGeneratorIntegrity:
    """Verifica que el generador de Excel produzca un archivo válido con las 5 hojas requeridas."""

    def test_excel_five_sheets_and_formulas(self):
        dom = DomesticDemandInput(25000, 125.0, 20.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.TEMPERATE)
        ind = [
            IndustrialRecord("Ind 1", "direct", direct_consumption_m3_day=200.0, operating_hours_per_day=16.0),
            IndustrialRecord("Ind 2", "specific", units_per_day=5000.0, specific_consumption=2.0, specific_unit="L/unidad", operating_hours_per_day=8.0),
        ]
        results = WaterDemandEngine.calculate_total_system_demand(dom, ind, k1=1.20, k2=1.50)

        excel_buf = generate_professional_excel(results)
        assert excel_buf is not None
        assert excel_buf.getvalue() != b""

        # Cargar libro con openpyxl para verificar estructura
        wb = openpyxl.load_workbook(excel_buf, data_only=False)
        expected_sheets = [
            "01_Resumen",
            "02_Datos_Entrada",
            "03_Memoria_Calculo",
            "04_Detalle_Industrial",
            "05_Verificacion"
        ]
        assert wb.sheetnames == expected_sheets

        # Verificar fórmulas en hoja 03_Memoria_Calculo
        ws3 = wb["03_Memoria_Calculo"]
        formula_cells = [cell.value for cell in ws3["E"] if isinstance(cell.value, str) and cell.value.startswith("=")]
        assert len(formula_cells) >= 8

        # Verificar hoja 04_Detalle_Industrial
        ws4 = wb["04_Detalle_Industrial"]
        sum_formula_cells = [cell.value for cell in ws4["E"] if isinstance(cell.value, str) and "SUM" in cell.value]
        assert len(sum_formula_cells) >= 1

        # Verificar hoja 05_Verificacion
        ws5 = wb["05_Verificacion"]
        conformance_cells = [cell.value for cell in ws5["G"] if isinstance(cell.value, str) and "IF" in cell.value]
        assert len(conformance_cells) >= 5


class TestPDFGeneratorIntegrity:
    """Verifica la generación correcta del documento PDF profesional."""

    def test_pdf_generation(self):
        dom = DomesticDemandInput(20000, 130.0, 20.0, CalculationMode.NORMATIVE_RAS, AltitudeZone.TEMPERATE)
        ind = [IndustrialRecord("Lácteos", "direct", direct_consumption_m3_day=150.0)]
        results = WaterDemandEngine.calculate_total_system_demand(dom, ind)

        pdf_buf = generate_professional_pdf(results)
        assert pdf_buf is not None
        pdf_bytes = pdf_buf.getvalue()
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")
