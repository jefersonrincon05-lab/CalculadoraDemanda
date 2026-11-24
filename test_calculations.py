"""
Pruebas Unitarias y Validaciones Matemáticas
Calculadora de Demanda Doméstica e Industrial de Agua

Verifica la precisión matemática, conversiones hidráulicas dimensionales
y manejo de casos límite según principios de ingeniería sanitaria.
"""

import math
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


class TestDomesticDemand:
    """Verifica el cálculo de la Demanda Media Diaria Doméstica."""

    def test_standard_case_without_losses(self):
        """
        Población: 10,000 hab
        Dotación: 150 L/hab·día
        Pérdidas: 0%
        V = 10,000 * 150 / 1000 = 1,500 m³/día
        Q = 10,000 * 150 / 86400 = 17.36111... L/s
        """
        inp = DomesticDemandInput(
            population=10000,
            endowment_L_hab_day=150.0,
            technical_losses_pct=0.0
        )
        vol_m3, q_ls, gross_end = WaterDemandEngine.calculate_domestic_demand(inp)

        assert pytest.approx(gross_end, rel=1e-9) == 150.0
        assert pytest.approx(vol_m3, rel=1e-9) == 1500.0
        assert pytest.approx(q_ls, rel=1e-5) == 17.36111
        # Comprobar equivalencia exacta V = Q * 86.4
        assert pytest.approx(vol_m3, rel=1e-9) == q_ls * 86.4

    def test_case_with_technical_losses(self):
        """
        Población: 5,000 hab
        Dotación neta: 120 L/hab·día
        Pérdidas: 20%
        Dotación bruta = 120 / (1 - 0.20) = 150 L/hab·día
        V = 5000 * 150 / 1000 = 750 m³/día
        Q = 750 / 86.4 = 8.68055... L/s
        """
        inp = DomesticDemandInput(
            population=5000,
            endowment_L_hab_day=120.0,
            technical_losses_pct=20.0
        )
        vol_m3, q_ls, gross_end = WaterDemandEngine.calculate_domestic_demand(inp)

        assert pytest.approx(gross_end, rel=1e-9) == 150.0
        assert pytest.approx(vol_m3, rel=1e-9) == 750.0
        assert pytest.approx(q_ls, rel=1e-5) == 8.68056

    def test_validation_negative_population(self):
        inp = DomesticDemandInput(population=-100, endowment_L_hab_day=150.0)
        with pytest.raises(ValueError, match="no puede ser negativa"):
            WaterDemandEngine.calculate_domestic_demand(inp)

    def test_validation_negative_endowment(self):
        inp = DomesticDemandInput(population=1000, endowment_L_hab_day=-50.0)
        with pytest.raises(ValueError, match="no puede ser negativa"):
            WaterDemandEngine.calculate_domestic_demand(inp)

    def test_validation_invalid_losses(self):
        inp = DomesticDemandInput(population=1000, endowment_L_hab_day=150.0, technical_losses_pct=100.0)
        with pytest.raises(ValueError, match="pérdidas técnicas"):
            WaterDemandEngine.calculate_domestic_demand(inp)


class TestIndustrialDemand:
    """Verifica el cálculo de Demanda Industrial (directa y específica)."""

    def test_direct_consumption(self):
        """Industria con consumo directo de 432 m³/día -> 432 / 86.4 = 5 L/s."""
        rec = IndustrialRecord(name="Planta A", mode="direct", direct_consumption_m3_day=432.0)
        vol_m3 = rec.calculate_volume_m3_day()
        q_ls = rec.calculate_flow_L_s()

        assert pytest.approx(vol_m3, rel=1e-9) == 432.0
        assert pytest.approx(q_ls, rel=1e-9) == 5.0

    def test_specific_consumption_liters(self):
        """
        2,000 unidades/día a 25 L/unidad = 50,000 L/día = 50 m³/día
        Q = 50 / 86.4 = 0.5787 L/s
        """
        rec = IndustrialRecord(
            name="Embotelladora",
            mode="specific",
            units_per_day=2000.0,
            specific_consumption=25.0,
            specific_unit="L/unidad"
        )
        vol_m3 = rec.calculate_volume_m3_day()
        q_ls = rec.calculate_flow_L_s()

        assert pytest.approx(vol_m3, rel=1e-9) == 50.0
        assert pytest.approx(q_ls, rel=1e-5) == 0.57870

    def test_specific_consumption_m3(self):
        """
        40 toneladas/día a 1.5 m³/tonelada = 60 m³/día
        Q = 60 / 86.4 = 0.6944 L/s
        """
        rec = IndustrialRecord(
            name="Papelera",
            mode="specific",
            units_per_day=40.0,
            specific_consumption=1.5,
            specific_unit="m3/unidad"
        )
        vol_m3 = rec.calculate_volume_m3_day()
        q_ls = rec.calculate_flow_L_s()

        assert pytest.approx(vol_m3, rel=1e-9) == 60.0
        assert pytest.approx(q_ls, rel=1e-5) == 0.69444

    def test_multiple_industries_sum(self):
        records = [
            IndustrialRecord(name="Ind 1", mode="direct", direct_consumption_m3_day=100.0),
            IndustrialRecord(name="Ind 2", mode="specific", units_per_day=500.0, specific_consumption=200.0, specific_unit="L/unidad"), # 100 m3
        ]
        tot_vol, tot_q, details = WaterDemandEngine.calculate_industrial_demand(records)

        assert pytest.approx(tot_vol, rel=1e-9) == 200.0
        assert pytest.approx(tot_q, rel=1e-9) == 200.0 / 86.4
        assert len(details) == 2


class TestTotalSystemDemandAndPeaks:
    """Verifica la agregación del sistema y los caudales máximos."""

    def test_total_demand_integration(self):
        """
        Doméstico: 10,000 hab * 150 L/hab·día = 1,500 m³/día (17.3611 L/s)
        Industrial: 500 m³/día (5.7870 L/s)
        Total: 2,000 m³/día (23.1481 L/s)
        % Doméstico = 1500 / 2000 = 75%
        % Industrial = 500 / 2000 = 25%
        """
        dom_inp = DomesticDemandInput(population=10000, endowment_L_hab_day=150.0)
        ind_rec = [IndustrialRecord(name="Metalúrgica", mode="direct", direct_consumption_m3_day=500.0)]

        res = WaterDemandEngine.calculate_total_system_demand(
            domestic_input=dom_inp,
            industrial_records=ind_rec,
            k1=1.20,
            k2=1.50,
            apply_k_to_industrial=False
        )

        assert pytest.approx(res.domestic_volume_m3_day, rel=1e-9) == 1500.0
        assert pytest.approx(res.industrial_volume_m3_day, rel=1e-9) == 500.0
        assert pytest.approx(res.total_volume_m3_day, rel=1e-9) == 2000.0
        assert pytest.approx(res.domestic_pct, rel=1e-9) == 75.0
        assert pytest.approx(res.industrial_pct, rel=1e-9) == 25.0

        # Verificación de Caudales Máximos (k1 y k2 aplicados al doméstico)
        # QMD = (Qmd_dom * k1) + Qmd_ind
        expected_qmd_ls = (res.domestic_flow_L_s * 1.20) + res.industrial_flow_L_s
        assert pytest.approx(res.q_max_daily_flow_L_s, rel=1e-9) == expected_qmd_ls

        # QMH = (Qmd_dom * k1 * k2) + Qmd_ind
        expected_qmh_ls = (res.domestic_flow_L_s * 1.20 * 1.50) + res.industrial_flow_L_s
        assert pytest.approx(res.q_max_hourly_flow_L_s, rel=1e-9) == expected_qmh_ls

    def test_total_demand_zero_cases(self):
        """Comprueba comportamiento con cero en alguna o ambas componentes."""
        dom_inp = DomesticDemandInput(population=0, endowment_L_hab_day=150.0)
        ind_rec = []
        res = WaterDemandEngine.calculate_total_system_demand(dom_inp, ind_rec)

        assert res.total_volume_m3_day == 0.0
        assert res.total_flow_L_s == 0.0
        assert res.domestic_pct == 0.0
        assert res.industrial_pct == 0.0
