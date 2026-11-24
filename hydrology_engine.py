"""
Motor de Cálculo Hidráulico y Sanitario
Calculadora de Demanda Doméstica e Industrial de Agua

Autor: Especialista en Abastecimiento de Agua e Hidrología
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional


# Constantes físicas y de conversión hidráulica
SECONDS_PER_DAY = 86400.0  # 24 h * 60 min * 60 s
LITERS_PER_M3 = 1000.0     # 1 m3 = 1000 L
FACTOR_M3DAY_TO_LS = LITERS_PER_M3 / SECONDS_PER_DAY  # 1 / 86.4 ≈ 0.011574074074074073
FACTOR_LS_TO_M3DAY = SECONDS_PER_DAY / LITERS_PER_M3  # 86.4


def m3_day_to_L_s(volume_m3_day: float) -> float:
    """Convierte un volumen diario en m3/día a caudal continuo en L/s."""
    return (volume_m3_day * LITERS_PER_M3) / SECONDS_PER_DAY


def L_s_to_m3_day(flow_L_s: float) -> float:
    """Convierte un caudal en L/s a volumen acumulado diario en m3/día."""
    return (flow_L_s * SECONDS_PER_DAY) / LITERS_PER_M3


@dataclass
class DomesticDemandInput:
    """Parámetros de entrada para el cálculo de demanda doméstica."""
    population: int                        # Población de diseño (habitantes)
    endowment_L_hab_day: float             # Dotación neta (L/hab·día)
    technical_losses_pct: float = 0.0      # Pérdidas físicas o técnicas estimadas en red (%)

    def validate(self) -> List[str]:
        """Valida que los datos ingresados sean matemáticamente y técnicamente válidos."""
        errors = []
        if self.population < 0:
            errors.append("La población no puede ser negativa.")
        if self.endowment_L_hab_day < 0:
            errors.append("La dotación de agua no puede ser negativa.")
        if not (0.0 <= self.technical_losses_pct < 100.0):
            errors.append("El porcentaje de pérdidas técnicas debe estar entre 0% y menor a 100%.")
        return errors

    def get_gross_endowment(self) -> float:
        """
        Calcula la dotación bruta considerando las pérdidas en la red.
        Dotación Bruta = Dotación Neta / (1 - Pérdidas/100)
        """
        loss_factor = 1.0 - (self.technical_losses_pct / 100.0)
        if loss_factor <= 0:
            raise ValueError("Las pérdidas técnicas deben ser inferiores al 100%.")
        return self.endowment_L_hab_day / loss_factor


@dataclass
class IndustrialRecord:
    """Registro individual de una industria o proceso industrial."""
    name: str                                  # Nombre o tipo de industria
    mode: str = "direct"                       # 'direct' (m3/día) o 'specific' (por producción)
    direct_consumption_m3_day: float = 0.0     # Consumo directo ingresado (m3/día)
    units_per_day: float = 0.0                 # Unidades producidas al día
    specific_consumption: float = 0.0          # Consumo específico por unidad
    specific_unit: str = "m3/unidad"           # 'm3/unidad' o 'L/unidad'
    operating_hours_per_day: float = 24.0      # Horas de operación diaria (default 24h para régimen uniforme)

    def calculate_volume_m3_day(self) -> float:
        """Calcula el volumen diario en m3/día según el método seleccionado."""
        if self.mode == "direct":
            return max(0.0, float(self.direct_consumption_m3_day))
        else:
            # Modo consumo específico
            qty = max(0.0, float(self.units_per_day))
            rate = max(0.0, float(self.specific_consumption))
            if self.specific_unit == "L/unidad":
                return (qty * rate) / LITERS_PER_M3
            else:
                return qty * rate

    def calculate_flow_L_s(self) -> float:
        """Calcula el caudal equivalente en L/s distribuido en 24 horas (demanda media diaria)."""
        vol_m3 = self.calculate_volume_m3_day()
        return m3_day_to_L_s(vol_m3)


@dataclass
class WaterDemandResults:
    """Resultados consolidados de las demandas de agua calculadas."""
    # Demanda Doméstica
    domestic_population: int
    domestic_endowment_net: float
    domestic_endowment_gross: float
    domestic_losses_pct: float
    domestic_volume_m3_day: float
    domestic_flow_L_s: float

    # Demanda Industrial
    industrial_volume_m3_day: float
    industrial_flow_L_s: float
    industrial_details: List[Dict[str, Any]] = field(default_factory=list)

    # Demanda Total Media Diaria (Qmd total)
    total_volume_m3_day: float = 0.0
    total_flow_L_s: float = 0.0

    # Fracciones porcentuales
    domestic_pct: float = 0.0
    industrial_pct: float = 0.0

    # Coeficientes y Caudales Máximos (para dimensionamiento de obras civiles)
    k1_coefficient: float = 1.20   # Coeficiente de variación diaria (QMD = k1 * Qmd)
    k2_coefficient: float = 1.50   # Coeficiente de variación horaria (QMH = k2 * QMD)
    
    # Caudales Máximos calculados
    q_max_daily_flow_L_s: float = 0.0       # QMD (L/s)
    q_max_daily_volume_m3_day: float = 0.0  # QMD equivalente (m3/día)
    q_max_hourly_flow_L_s: float = 0.0      # QMH (L/s)
    q_max_hourly_volume_m3_day: float = 0.0 # QMH equivalente (m3/día)


class WaterDemandEngine:
    """
    Motor central de ingeniería hidráulica para el cálculo de demanda
    media diaria doméstica, industrial y análisis de caudales máximos.
    """

    @staticmethod
    def calculate_domestic_demand(inp: DomesticDemandInput) -> Tuple[float, float, float]:
        """
        Calcula la demanda media diaria doméstica.
        
        Retorna:
            (volumen_m3_dia, caudal_L_s, dotacion_bruta)
        """
        validation_errors = inp.validate()
        if validation_errors:
            raise ValueError("; ".join(validation_errors))

        gross_endowment = inp.get_gross_endowment()
        
        # Volumen diario en Litros = Población * Dotación Bruta
        volume_liters_day = float(inp.population) * gross_endowment
        # Volumen diario en m3 = Litros / 1000
        volume_m3_day = volume_liters_day / LITERS_PER_M3
        # Caudal medio diario en L/s = Litros / 86400
        flow_L_s = volume_liters_day / SECONDS_PER_DAY

        return volume_m3_day, flow_L_s, gross_endowment

    @staticmethod
    def calculate_industrial_demand(records: List[IndustrialRecord]) -> Tuple[float, float, List[Dict[str, Any]]]:
        """
        Calcula la demanda media diaria industrial a partir de una lista de registros.

        Retorna:
            (total_volumen_m3_dia, total_caudal_L_s, lista_detalles)
        """
        total_vol_m3 = 0.0
        details = []

        for rec in records:
            vol_m3 = rec.calculate_volume_m3_day()
            q_ls = rec.calculate_flow_L_s()
            total_vol_m3 += vol_m3
            
            method_desc = (
                f"Directo: {rec.direct_consumption_m3_day:,.2f} m³/día"
                if rec.mode == "direct"
                else f"Específico: {rec.units_per_day:,.2f} u/día × {rec.specific_consumption:,.4f} {rec.specific_unit}"
            )

            details.append({
                "Nombre": rec.name,
                "Método": "Directo" if rec.mode == "direct" else "Consumo Específico",
                "Descripción": method_desc,
                "Volumen (m³/día)": round(vol_m3, 4),
                "Caudal (L/s)": round(q_ls, 4),
            })

        total_q_ls = m3_day_to_L_s(total_vol_m3)
        return total_vol_m3, total_q_ls, details

    @classmethod
    def calculate_total_system_demand(
        cls,
        domestic_input: DomesticDemandInput,
        industrial_records: List[IndustrialRecord],
        k1: float = 1.20,
        k2: float = 1.50,
        apply_k_to_industrial: bool = False
    ) -> WaterDemandResults:
        """
        Calcula la demanda total del sistema de abastecimiento, integrando
        las demandas domésticas e industriales y diferenciando demanda media
        de caudales máximos (QMD y QMH).
        
        Parámetro apply_k_to_industrial:
            En ingeniería sanitaria, si las industrias operan con regímenes
            estables de 24h o almacenamiento propio, frecuentemente los coeficientes
            de pico (k1, k2) solo se aplican a la demanda doméstica. Este parámetro
            permite seleccionar si los factores k1 y k2 afectan a todo el sistema
            o únicamente a la componente doméstica.
        """
        # Demanda Doméstica
        dom_vol_m3, dom_q_ls, gross_endowment = cls.calculate_domestic_demand(domestic_input)

        # Demanda Industrial
        ind_vol_m3, ind_q_ls, ind_details = cls.calculate_industrial_demand(industrial_records)

        # Demanda Total Media Diaria
        tot_vol_m3 = dom_vol_m3 + ind_vol_m3
        tot_q_ls = dom_q_ls + ind_q_ls

        # Porcentajes de participación
        if tot_vol_m3 > 0:
            dom_pct = (dom_vol_m3 / tot_vol_m3) * 100.0
            ind_pct = (ind_vol_m3 / tot_vol_m3) * 100.0
        else:
            dom_pct = 0.0
            ind_pct = 0.0

        # Caudales Máximos:
        # Demanda Media Diaria Base (Qmd)
        q_md_base_ls = tot_q_ls

        if apply_k_to_industrial:
            # Coeficientes aplicados a la demanda total
            q_md_flow = q_md_base_ls
            q_max_daily_ls = q_md_flow * k1
            q_max_hourly_ls = q_max_daily_ls * k2
        else:
            # Coeficientes aplicados únicamente al componente doméstico (práctica recomendada en saneamiento)
            q_max_daily_ls = (dom_q_ls * k1) + ind_q_ls
            q_max_hourly_ls = (dom_q_ls * k1 * k2) + ind_q_ls

        q_max_daily_m3_day = L_s_to_m3_day(q_max_daily_ls)
        q_max_hourly_m3_day = L_s_to_m3_day(q_max_hourly_ls)

        return WaterDemandResults(
            domestic_population=domestic_input.population,
            domestic_endowment_net=domestic_input.endowment_L_hab_day,
            domestic_endowment_gross=gross_endowment,
            domestic_losses_pct=domestic_input.technical_losses_pct,
            domestic_volume_m3_day=dom_vol_m3,
            domestic_flow_L_s=dom_q_ls,
            industrial_volume_m3_day=ind_vol_m3,
            industrial_flow_L_s=ind_q_ls,
            industrial_details=ind_details,
            total_volume_m3_day=tot_vol_m3,
            total_flow_L_s=tot_q_ls,
            domestic_pct=dom_pct,
            industrial_pct=ind_pct,
            k1_coefficient=k1,
            k2_coefficient=k2,
            q_max_daily_flow_L_s=q_max_daily_ls,
            q_max_daily_volume_m3_day=q_max_daily_m3_day,
            q_max_hourly_flow_L_s=q_max_hourly_ls,
            q_max_hourly_volume_m3_day=q_max_hourly_m3_day
        )
