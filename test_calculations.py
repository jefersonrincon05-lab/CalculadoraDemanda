"""
Pruebas Unitarias y Validaciones Matemáticas
Calculadora de Demanda Doméstica e Industrial de Agua
Versión 2.0 - Validación Estricta de Casillas y Datos Incoherentes
"""

import pytest
from hydrology_engine import (
    SECONDS_PER_DAY,
    LITERS_PER_M3,
    FACTOR_LS_TO_M3DAY,
    m3_day_to_L_s,
    L_s_to_m3_day,
    DomesticDemandInput,
    IndustrialRecord,
    WaterDemandEngine,
)


class TestHydraulicConversions:
    """Verifica las conversiones de unidades fundamentales."""

    def test_constants_accuracy(self):
        """1 día = 86400 s, 1 m³ = 1000 L -> Factor = 86.4"""
        assert SECONDS_PER_DAY == 86400.0
        assert LITERS_PER_M3 == 1000.0
        assert pytest.approx(FACTOR_LS_TO_M3DAY, rel=1e-9) == 86.4

    def test_conversion_roundtrip(self):
        """Verifica que la conversión m3/día <-> L/s sea simétrica y exacta."""
        test_values_m3 = [0.0, 1.0, 86.4, 500.0, 10000.0, 12345.67]
        for v in test_values_m3:
            q_ls = m3_day_to_L_s(v)
            v_back = L_s_to_m3_day(q_ls)
            assert pytest.approx(v, rel=1e-9) == v_back

    def test_known_equivalence(self):
        """Un caudal continuo de 1 L/s genera exactamente 86.4 m³/día."""
        assert pytest.approx(L_s_to_m3_day(1.0), rel=1e-9) == 86.4
        assert pytest.approx(m3_day_to_L_s(86.4), rel=1e-9) == 1.0


class TestDomesticDemandStrictValidation:
    """Verifica que los datos incoherentes sean estrictamente rechazados casilla por casilla."""

    def test_standard_valid_case(self):
        inp = DomesticDemandInput(population=10000, endowment_L_hab_day=150.0, technical_losses_pct=20.0)
        report = inp.validate_strict()
        assert report.is_valid is True
        assert len(report.errors) == 0

        gross = inp.get_gross_endowment()
        assert pytest.approx(gross, rel=1e-9) == 187.5
        vol_m3, q_ls, _ = WaterDemandEngine.calculate_domestic_demand(inp)
        assert pytest.approx(vol_m3, rel=1e-9) == 1875.0
        assert pytest.approx(q_ls, rel=1e-5) == 21.701388

    def test_reject_zero_or_negative_population(self):
        """Población <= 0 es incoherente."""
        for bad_pop in [0, -1, -500]:
            inp = DomesticDemandInput(population=bad_pop, endowment_L_hab_day=150.0)
            rep = inp.validate_strict()
            assert rep.is_valid is False
            assert any("Población" in err for err in rep.errors)

    def test_reject_subsurvival_dotacion(self):
        """Dotación < 25 L/hab·día viola el mínimo vital OMS."""
        inp = DomesticDemandInput(population=5000, endowment_L_hab_day=20.0)
        rep = inp.validate_strict()
        assert rep.is_valid is False
        assert any("mínimo vital" in err or "Inadmisible" in err for err in rep.errors)

    def test_reject_excessive_dotacion(self):
        """Dotación > 500 L/hab·día es incoherente para uso residencial."""
        inp = DomesticDemandInput(population=5000, endowment_L_hab_day=550.0)
        rep = inp.validate_strict()
        assert rep.is_valid is False
        assert any("Incoherente" in err for err in rep.errors)

    def test_reject_negative_dotacion(self):
        inp = DomesticDemandInput(population=5000, endowment_L_hab_day=-50.0)
        rep = inp.validate_strict()
        assert rep.is_valid is False

    def test_reject_catastrophic_or_negative_losses(self):
        """Pérdidas < 0% o >= 60% deben ser rechazadas."""
        inp_neg = DomesticDemandInput(population=5000, endowment_L_hab_day=150.0, technical_losses_pct=-5.0)
        assert inp_neg.validate_strict().is_valid is False

        inp_inf = DomesticDemandInput(population=5000, endowment_L_hab_day=150.0, technical_losses_pct=60.0)
        assert inp_inf.validate_strict().is_valid is False

        inp_huge = DomesticDemandInput(population=5000, endowment_L_hab_day=150.0, technical_losses_pct=100.0)
        assert inp_huge.validate_strict().is_valid is False


class TestPeakFactorsStrictValidation:
    """Verifica la validación física de k1 y k2."""

    def test_reject_k1_less_than_one(self):
        """QMD no puede ser menor a Qmd (k1 < 1.0 es físicamente imposible)."""
        rep = WaterDemandEngine.validate_peak_factors(k1=0.85, k2=1.50)
        assert rep.is_valid is False
        assert any("k₁" in err for err in rep.errors)

    def test_reject_k2_less_than_one(self):
        """QMH no puede ser menor a QMD (k2 < 1.0 es físicamente imposible)."""
        rep = WaterDemandEngine.validate_peak_factors(k1=1.20, k2=0.90)
        assert rep.is_valid is False
        assert any("k₂" in err for err in rep.errors)

    def test_accept_valid_peaks_with_warnings(self):
        rep = WaterDemandEngine.validate_peak_factors(k1=1.65, k2=2.60)
        assert rep.is_valid is True
        assert len(rep.warnings) == 2


class TestIndustrialValidationAndShiftFlow:
    """Verifica validación industrial y cálculo de caudal en turno."""

    def test_industrial_shift_operating_flow(self):
        """
        Una fábrica que consume 100 m³/día pero opera en 1 solo turno de 8 horas:
        - Caudal medio diario 24h = 100 / 86.4 = 1.1574 L/s
        - Caudal durante el turno (8h) = (100 * 1000) / (8 * 3600) = 3.4722 L/s
        El caudal de turno es exactamente 3 veces el caudal medio 24h.
        """
        rec = IndustrialRecord(
            name="Cervecería",
            mode="direct",
            direct_consumption_m3_day=100.0,
            operating_hours_per_day=8.0
        )
        assert rec.validate_strict().is_valid is True
        assert pytest.approx(rec.calculate_flow_L_s(), rel=1e-5) == 1.15741
        assert pytest.approx(rec.calculate_operating_flow_L_s(), rel=1e-5) == 3.47222
        assert pytest.approx(rec.calculate_operating_flow_L_s() / rec.calculate_flow_L_s(), rel=1e-5) == 3.0

    def test_reject_negative_industrial_values(self):
        rec_bad = IndustrialRecord(name="Planta X", mode="direct", direct_consumption_m3_day=-10.0)
        assert rec_bad.validate_strict().is_valid is False

        rec_bad_units = IndustrialRecord(name="Planta Y", mode="specific", units_per_day=-5.0, specific_consumption=2.0)
        assert rec_bad_units.validate_strict().is_valid is False

        rec_bad_hours = IndustrialRecord(name="Planta Z", mode="direct", direct_consumption_m3_day=10.0, operating_hours_per_day=0.0)
        assert rec_bad_hours.validate_strict().is_valid is False

        rec_bad_hours2 = IndustrialRecord(name="Planta W", mode="direct", direct_consumption_m3_day=10.0, operating_hours_per_day=25.0)
        assert rec_bad_hours2.validate_strict().is_valid is False


class TestAuditTableGeneration:
    """Verifica que la auditoría casilla por casilla genere todos los campos requeridos."""

    def test_audit_table_completeness(self):
        dom = DomesticDemandInput(population=25000, endowment_L_hab_day=140.0, technical_losses_pct=18.0)
        ind = [IndustrialRecord(name="Lácteos", mode="direct", direct_consumption_m3_day=200.0)]
        res = WaterDemandEngine.calculate_total_system_demand(dom, ind, k1=1.20, k2=1.50)

        assert len(res.audit_table) >= 7
        fields = [row["Casilla / Parámetro"] for row in res.audit_table]
        assert "Población de Diseño (P)" in fields
        assert "Dotación Neta (Dneta)" in fields
        assert "Pérdidas Técnicas (%P)" in fields
        assert "Dotación Bruta (Dbruta)" in fields
        assert "Coeficiente Variación Diaria (k₁)" in fields
        assert "Coeficiente Variación Horaria (k₂)" in fields
