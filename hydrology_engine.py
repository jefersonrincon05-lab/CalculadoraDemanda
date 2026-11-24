"""
Motor de Cálculo Hidráulico y Sanitario
Calculadora de Demanda Doméstica e Industrial de Agua
Versión 3.0 - Auditoría Técnica, Integración Normativa RAS 0330 / 2017 y Modo Exploratorio
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Tuple, Optional


# Constantes físicas y factores de conversión hidráulica exacta
SECONDS_PER_DAY = 86400.0  # 24 h * 60 min * 60 s
LITERS_PER_M3 = 1000.0     # 1 m3 = 1000 L
FACTOR_M3DAY_TO_LS = LITERS_PER_M3 / SECONDS_PER_DAY  # 1 / 86.4 ≈ 0.011574074074074073
FACTOR_LS_TO_M3DAY = SECONDS_PER_DAY / LITERS_PER_M3  # Exactamente 86.40


def m3_day_to_L_s(volume_m3_day: float) -> float:
    """Convierte un volumen diario en m3/día a caudal continuo distribuido en 24h (L/s)."""
    return (volume_m3_day * LITERS_PER_M3) / SECONDS_PER_DAY


def L_s_to_m3_day(flow_L_s: float) -> float:
    """Convierte un caudal continuo en L/s a volumen acumulado diario en m3/día."""
    return (flow_L_s * SECONDS_PER_DAY) / LITERS_PER_M3


class CalculationMode(str, Enum):
    """Modo de cálculo y auditoría técnica."""
    NORMATIVE_RAS = "RAS_0330"   # Reglamento Técnico del Sector de Agua Potable y Saneamiento Básico (Colombia, Res. 0330/2017)
    EXPLORATORY = "EXPLORATORY"  # Modo exploratorio / libre para investigación y proyectos internacionales


class AltitudeZone(str, Enum):
    """Pisos térmicos y rangos de altitud según Art. 43 Res. 0330 de 2017."""
    COLD = "Frio (> 2000 msnm)"              # Dotación neta máxima RAS: 120 L/hab·día
    TEMPERATE = "Templado (1000 - 2000 msnm)" # Dotación neta máxima RAS: 130 L/hab·día
    WARM = "Calido (< 1000 msnm)"             # Dotación neta máxima RAS: 140 L/hab·día


# Límites oficiales de dotación neta máxima según Art. 43 Res. 0330 de 2017
RAS_MAX_NET_ENDOWMENT: Dict[AltitudeZone, float] = {
    AltitudeZone.COLD: 120.0,
    AltitudeZone.TEMPERATE: 130.0,
    AltitudeZone.WARM: 140.0,
}

# Límite normativo de pérdidas técnicas admisibles según Art. 44 Res. 0330 de 2017
RAS_MAX_TECHNICAL_LOSSES_PCT = 25.0


# Catálogo documentado de benchmarks de consumo industrial con fuentes técnicas formales
DOCUMENTED_INDUSTRIAL_BENCHMARKS = {
    "Personalizada": {
        "unit": "m3/unidad",
        "consumo_tipico": 1.0,
        "horas_op_tipicas": 24.0,
        "fuente": "Definido por el proyectista / Memoria del proceso industrial."
    },
    "Bebidas y Refrescos (L agua / L bebida)": {
        "unit": "L/unidad",
        "consumo_tipico": 2.5,
        "horas_op_tipicas": 16.0,
        "fuente": "PNUMA / ONUDI - Guías de Producción Limpia en Industria de Bebidas; BAT Reference Document."
    },
    "Cervecería Industrial (L agua / L cerveza)": {
        "unit": "L/unidad",
        "consumo_tipico": 4.5,
        "horas_op_tipicas": 24.0,
        "fuente": "Metcalf & Eddy (Wastewater Engineering); European Commission IPPC BREF FDM (2019)."
    },
    "Planta Láctea / Pasteurizadora (L agua / L leche)": {
        "unit": "L/unidad",
        "consumo_tipico": 2.0,
        "horas_op_tipicas": 16.0,
        "fuente": "Banco Mundial / IFC - Environmental, Health, and Safety Guidelines for Dairy Processing."
    },
    "Matadero / Frigorífico Bovino (L agua / res faenada)": {
        "unit": "L/unidad",
        "consumo_tipico": 1200.0,
        "horas_op_tipicas": 8.0,
        "fuente": "FAO / CEPIS-OPS - Manual de Abastecimiento de Agua en Rastros y Mataderos Municipales."
    },
    "Matadero Porcino (L agua / cerdo faenado)": {
        "unit": "L/unidad",
        "consumo_tipico": 450.0,
        "horas_op_tipicas": 8.0,
        "fuente": "FAO / CEPIS-OPS; Guías de Saneamiento Agroindustrial."
    },
    "Planta de Beneficio Avícola (L agua / ave faenada)": {
        "unit": "L/unidad",
        "consumo_tipico": 25.0,
        "horas_op_tipicas": 12.0,
        "fuente": "IFC / World Bank - Poultry Processing Guidelines; Guías Ambientales del Sector Avícola."
    },
    "Industria Textil - Tintorería (L agua / kg tela procesada)": {
        "unit": "L/unidad",
        "consumo_tipico": 110.0,
        "horas_op_tipicas": 16.0,
        "fuente": "European IPPC Bureau (BREF Textiles); CONAGUA - Manual de Agua Potable y Alcantarillado."
    },
    "Fabricación de Papel y Cartón (m³ agua / ton papel)": {
        "unit": "m3/unidad",
        "consumo_tipico": 25.0,
        "horas_op_tipicas": 24.0,
        "fuente": "Best Available Techniques (BAT) Reference Document for the Production of Pulp, Paper and Board (2015)."
    },
    "Central de Concreto Hidráulico (m³ agua / m³ concreto)": {
        "unit": "m3/unidad",
        "consumo_tipico": 0.20,
        "horas_op_tipicas": 10.0,
        "fuente": "American Concrete Institute (ACI 211.1) - Standard Practice for Selecting Proportions."
    },
    "Curtiduría de Pieles (m³ agua / ton piel salada)": {
        "unit": "m3/unidad",
        "consumo_tipico": 35.0,
        "horas_op_tipicas": 12.0,
        "fuente": "UNIDO - United Nations Industrial Development Organization, Tanneries Environmental Benchmark."
    },
    "Ingenio Azucarero (m³ agua / ton caña)": {
        "unit": "m3/unidad",
        "consumo_tipico": 0.85,
        "horas_op_tipicas": 24.0,
        "fuente": "EPA / IFC - Environmental, Health, and Safety Guidelines for Sugar Manufacturing."
    },
    "Lavandería Industrial (L agua / kg ropa lavada)": {
        "unit": "L/unidad",
        "consumo_tipico": 20.0,
        "horas_op_tipicas": 12.0,
        "fuente": "European Textile Services Association (ETSA); CONAGUA - Manual de Eficiencia en Servicios."
    },
    "Industria Farmacéutica (L agua / empleado·día)": {
        "unit": "L/unidad",
        "consumo_tipico": 180.0,
        "horas_op_tipicas": 16.0,
        "fuente": "WHO Technical Report Series; IFC - Pharmaceuticals Manufacturing Guidelines."
    },
    "Complejo Hotelero / Resort (L agua / huésped·día)": {
        "unit": "L/unidad",
        "consumo_tipico": 400.0,
        "horas_op_tipicas": 24.0,
        "fuente": "OMT / CEPIS-OPS - Guías de Consumo y Saneamiento Turístico en América Latina."
    },
    "Hospital de Alta Complejidad (L agua / cama·día)": {
        "unit": "L/unidad",
        "consumo_tipico": 800.0,
        "horas_op_tipicas": 24.0,
        "fuente": "OPS/OMS - Guías de Calidad y Dotación de Agua en Establecimientos de Salud; RAS Título B."
    },
    "Estación de Lavado Automotriz (L agua / vehículo)": {
        "unit": "L/unidad",
        "consumo_tipico": 220.0,
        "horas_op_tipicas": 10.0,
        "fuente": "International Carwash Association (ICA) / Water Recycling Benchmarks."
    },
}


@dataclass
class ValidationReport:
    """Informe estructurado de validación de datos técnicos."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    ras_non_compliance: List[str] = field(default_factory=list)


@dataclass
class DomesticDemandInput:
    """Parámetros de entrada para el cálculo de demanda doméstica."""
    population: int                              # Población de diseño (habitantes)
    endowment_L_hab_day: float                   # Dotación neta (L/hab·día)
    technical_losses_pct: float = 0.0            # Pérdidas técnicas estimadas en red (%)
    mode: CalculationMode = CalculationMode.NORMATIVE_RAS
    altitude_zone: AltitudeZone = AltitudeZone.TEMPERATE

    def validate_strict(self) -> ValidationReport:
        """
        Valida casilla por casilla distinguiendo modo normativo (RAS Res. 0330/2017)
        de modo exploratorio/internacional.
        """
        errors = []
        warnings = []
        ras_issues = []

        # 1. Casilla: Población
        if not isinstance(self.population, (int, float)) or self.population != int(self.population):
            errors.append("Casilla 'Población': Debe ser un número entero de habitantes.")
        elif self.population <= 0:
            errors.append("Casilla 'Población': Debe ser mayor a 0 habitantes para proyectar el sistema.")
        elif self.population > 25_000_000:
            warnings.append("Casilla 'Población': Superior a 25 millones de hab. Requiere desagregación por subsistemas.")

        # 2. Casilla: Dotación Neta
        if self.endowment_L_hab_day <= 0:
            errors.append("Casilla 'Dotación Neta': Debe ser estrictamente positiva.")
        elif self.endowment_L_hab_day < 25.0:
            errors.append("Casilla 'Dotación Neta': Inadmisible (< 25 L/hab·día). Inferior al mínimo vital OMS de supervivencia.")
        elif self.endowment_L_hab_day > 600.0:
            errors.append("Casilla 'Dotación Neta': Incoherente (> 600 L/hab·día) para uso exclusivamente doméstico.")

        # Verificación normativa colombiana RAS 0330 (Art. 43)
        if self.mode == CalculationMode.NORMATIVE_RAS:
            ras_limit = RAS_MAX_NET_ENDOWMENT.get(self.altitude_zone, 140.0)
            if self.endowment_L_hab_day > ras_limit:
                ras_issues.append(
                    f"Incumplimiento RAS Art. 43: La dotación neta ({self.endowment_L_hab_day:.1f} L/hab·d) "
                    f"supera el límite normativo de {ras_limit:.0f} L/hab·día para zona de clima '{self.altitude_zone.value}'."
                )
                errors.append(
                    f"Casilla 'Dotación Neta' (Modo RAS): Supera el máximo legal de {ras_limit:.0f} L/hab·día (Art. 43 Res. 0330/2017). "
                    f"Cambie a 'Modo Exploratorio' si desea simular un escenario libre sin sujeción a la norma colombiana."
                )
        else:
            if self.endowment_L_hab_day > 250.0:
                warnings.append(f"Casilla 'Dotación Neta': Elevada ({self.endowment_L_hab_day:.1f} L/hab·día). Superior a dotaciones residenciales típicas.")

        # 3. Casilla: Pérdidas Técnicas
        if self.technical_losses_pct < 0.0:
            errors.append("Casilla 'Pérdidas Técnicas': No pueden ser negativas.")
        elif self.technical_losses_pct >= 60.0:
            errors.append(f"Casilla 'Pérdidas Técnicas': Inadmisible ({self.technical_losses_pct:.1f}%). Valores ≥ 60% generan asíntota matemática y sobredimensionamiento extremo.")

        # Verificación normativa colombiana RAS 0330 (Art. 44)
        if self.mode == CalculationMode.NORMATIVE_RAS:
            if self.technical_losses_pct > RAS_MAX_TECHNICAL_LOSSES_PCT:
                ras_issues.append(
                    f"Incumplimiento RAS Art. 44: Las pérdidas técnicas ({self.technical_losses_pct:.1f}%) "
                    f"superan el límite admisible del {RAS_MAX_TECHNICAL_LOSSES_PCT:.0f}% establecido por la Res. 0330/2017."
                )
                errors.append(
                    f"Casilla 'Pérdidas Técnicas' (Modo RAS): Supera el {RAS_MAX_TECHNICAL_LOSSES_PCT:.0f}% máximo legal (Art. 44 Res. 0330/2017). "
                    f"Ajuste a ≤ 25% o active el 'Modo Exploratorio' para modelar redes en estado crítico de fugas."
                )
        else:
            if self.technical_losses_pct >= 30.0:
                warnings.append(f"Casilla 'Pérdidas Técnicas': Nivel elevado ({self.technical_losses_pct:.1f}%). Requiere plan de sectorización y reducción de fugas.")

        return ValidationReport(
            is_valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
            ras_non_compliance=ras_issues
        )

    def get_gross_endowment(self) -> float:
        """
        Calcula la dotación bruta:
        D_bruta = D_neta / (1 - Pérdidas/100)
        """
        loss_factor = 1.0 - (self.technical_losses_pct / 100.0)
        if loss_factor <= 0:
            raise ValueError("Las pérdidas técnicas deben ser inferiores al 100%.")
        return self.endowment_L_hab_day / loss_factor


@dataclass
class IndustrialRecord:
    """Registro individual de una industria o proceso productivo."""
    name: str                                  # Nombre o razón social
    mode: str = "direct"                       # 'direct' (m3/día) o 'specific' (por producción)
    direct_consumption_m3_day: float = 0.0     # Consumo directo (m3/día)
    units_per_day: float = 0.0                 # Unidades producidas al día
    specific_consumption: float = 0.0          # Consumo específico
    specific_unit: str = "m3/unidad"           # 'm3/unidad' o 'L/unidad'
    operating_hours_per_day: float = 24.0      # Horas de operación diaria (Hop)
    has_own_storage: bool = True               # Si tiene tanque de reserva propio (amortigua picos a la red)
    benchmark_source: str = "Estimación directa del proyectista."

    def validate_strict(self) -> ValidationReport:
        errors = []
        warnings = []

        if not self.name or not self.name.strip():
            errors.append("El nombre de la industria no puede estar vacío.")

        if not (0.5 <= self.operating_hours_per_day <= 24.0):
            errors.append(f"Las horas de operación de '{self.name}' deben estar entre 0.5 y 24.0 horas al día.")

        if self.mode == "direct":
            if self.direct_consumption_m3_day < 0.0:
                errors.append(f"El consumo directo en '{self.name}' no puede ser negativo.")
        elif self.mode == "specific":
            if self.units_per_day < 0.0:
                errors.append(f"Las unidades producidas en '{self.name}' no pueden ser negativas.")
            if self.specific_consumption < 0.0:
                errors.append(f"El consumo específico en '{self.name}' no puede ser negativo.")
            if self.units_per_day > 0 and self.specific_consumption == 0:
                warnings.append(f"'{self.name}' tiene unidades producidas pero consumo específico 0.")
        else:
            errors.append(f"Modo '{self.mode}' no reconocido.")

        return ValidationReport(is_valid=(len(errors) == 0), errors=errors, warnings=warnings)

    def calculate_volume_m3_day(self) -> float:
        """Calcula el volumen diario en m3/día."""
        rep = self.validate_strict()
        if not rep.is_valid:
            raise ValueError("; ".join(rep.errors))

        if self.mode == "direct":
            return max(0.0, float(self.direct_consumption_m3_day))
        else:
            qty = max(0.0, float(self.units_per_day))
            rate = max(0.0, float(self.specific_consumption))
            if self.specific_unit == "L/unidad":
                return (qty * rate) / LITERS_PER_M3
            else:
                return qty * rate

    def calculate_flow_L_s(self) -> float:
        """Calcula el caudal medio diario en L/s (base 24 horas, para balance de recurso hídrico)."""
        vol_m3 = self.calculate_volume_m3_day()
        return m3_day_to_L_s(vol_m3)

    def calculate_operating_flow_L_s(self) -> float:
        """
        Calcula el caudal de acometida durante el turno de operación fabril (Hop):
        Q_op = (Volumen_m3 * 1000) / (Hop * 3600) [L/s]
        """
        vol_m3 = self.calculate_volume_m3_day()
        seconds_op = max(0.5, float(self.operating_hours_per_day)) * 3600.0
        return (vol_m3 * LITERS_PER_M3) / seconds_op


@dataclass
class WaterDemandResults:
    """Resultados consolidados de las demandas de agua calculadas."""
    # Modo de cálculo
    calculation_mode: CalculationMode
    altitude_zone: AltitudeZone

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

    # Demanda Total Media Diaria (Qmd)
    total_volume_m3_day: float = 0.0
    total_flow_L_s: float = 0.0

    # Fracciones porcentuales
    domestic_pct: float = 0.0
    industrial_pct: float = 0.0

    # Coeficientes y Caudales Máximos
    k1_coefficient: float = 1.20   # Coeficiente de variación diaria (QMD = k1 * Qmd)
    k2_coefficient: float = 1.50   # Coeficiente de variación horaria (QMH = k2 * QMD)
    apply_k_to_industrial: bool = False

    # Caudales Máximos calculados
    q_max_daily_flow_L_s: float = 0.0       # QMD (L/s)
    q_max_daily_volume_m3_day: float = 0.0  # QMD equivalente (m3/día)
    q_max_hourly_flow_L_s: float = 0.0      # QMH (L/s)
    q_max_hourly_volume_m3_day: float = 0.0 # QMH equivalente (m3/día)

    # Informe de Validación y Auditoría
    validation_report: ValidationReport = field(default_factory=lambda: ValidationReport(is_valid=True))
    audit_table: List[Dict[str, Any]] = field(default_factory=list)


class WaterDemandEngine:
    """
    Motor central de ingeniería hidráulica para el cálculo de demanda
    media diaria doméstica, industrial y análisis de caudales máximos.
    """

    @staticmethod
    def suggest_ras_peak_factors(population: int) -> Tuple[float, float]:
        """
        Sugiere coeficientes k1 y k2 conforme a las directrices de la
        Resolución 0330 de 2017 (Artículos 47 y 48) según tamaño poblacional.
        """
        # k1 (Variación diaria):
        if population <= 12500:
            suggested_k1 = 1.30
        else:
            suggested_k1 = 1.20

        # k2 (Variación horaria):
        if population <= 12500:
            suggested_k2 = 1.60
        elif population <= 60000:
            suggested_k2 = 1.50
        else:
            suggested_k2 = 1.40

        return suggested_k1, suggested_k2

    @staticmethod
    def validate_peak_factors(k1: float, k2: float, mode: CalculationMode = CalculationMode.NORMATIVE_RAS) -> ValidationReport:
        """Valida rigurosamente la coherencia de los coeficientes k1 y k2."""
        errors = []
        warnings = []
        ras_issues = []

        if k1 < 1.00:
            errors.append(f"Casilla 'Factor k₁': Incoherente ({k1:.2f}). Por definición física, el día máximo no puede tener menor consumo que el día medio (k₁ ≥ 1.00).")
        elif k1 > 1.60:
            warnings.append(f"Casilla 'Factor k₁': Elevado ({k1:.2f}). El rango normativo habitual en RAS 0330 es de 1.20 a 1.30.")

        if k2 < 1.00:
            errors.append(f"Casilla 'Factor k₂': Incoherente ({k2:.2f}). La hora máxima no puede ser inferior al caudal medio diario (k₂ ≥ 1.00).")
        elif k2 > 2.50:
            warnings.append(f"Casilla 'Factor k₂': Muy elevado ({k2:.2f}). El rango habitual en RAS 0330 oscila entre 1.40 y 1.60.")

        return ValidationReport(is_valid=(len(errors) == 0), errors=errors, warnings=warnings, ras_non_compliance=ras_issues)

    @staticmethod
    def calculate_domestic_demand(inp: DomesticDemandInput) -> Tuple[float, float, float]:
        """Calcula demanda doméstica tras validación rigurosa."""
        report = inp.validate_strict()
        if not report.is_valid:
            raise ValueError("; ".join(report.errors))

        gross_endowment = inp.get_gross_endowment()
        volume_liters_day = float(inp.population) * gross_endowment
        volume_m3_day = volume_liters_day / LITERS_PER_M3
        flow_L_s = volume_liters_day / SECONDS_PER_DAY

        return volume_m3_day, flow_L_s, gross_endowment

    @staticmethod
    def calculate_industrial_demand(records: List[IndustrialRecord]) -> Tuple[float, float, List[Dict[str, Any]]]:
        """Calcula demanda industrial en volumen diario, caudal medio y caudal en turno."""
        total_vol_m3 = 0.0
        details = []

        for rec in records:
            rep = rec.validate_strict()
            if not rep.is_valid:
                raise ValueError("; ".join(rep.errors))

            vol_m3 = rec.calculate_volume_m3_day()
            q_ls = rec.calculate_flow_L_s()
            q_op_ls = rec.calculate_operating_flow_L_s()
            total_vol_m3 += vol_m3

            desc = (
                f"Directo: {rec.direct_consumption_m3_day:,.2f} m³/día"
                if rec.mode == "direct"
                else f"Específico: {rec.units_per_day:,.2f} u/d × {rec.specific_consumption:,.4f} {rec.specific_unit}"
            )

            details.append({
                "Nombre": rec.name,
                "Método": "Directo" if rec.mode == "direct" else "Consumo Específico",
                "Descripción": desc,
                "Horas Operación": f"{rec.operating_hours_per_day:.1f} h/día",
                "Tanque Reserva": "Sí (Amortiguado)" if rec.has_own_storage else "No (Toma Directa)",
                "Volumen Diario (m³/día)": round(vol_m3, 4),
                "Caudal Medio 24h (L/s)": round(q_ls, 4),
                "Caudal en Turno Operativo (L/s)": round(q_op_ls, 4),
                "Fuente Benchmark": rec.benchmark_source
            })

        total_q_ls = m3_day_to_L_s(total_vol_m3)
        return total_vol_m3, total_q_ls, details

    @classmethod
    def generate_field_by_field_audit(
        cls,
        domestic_input: DomesticDemandInput,
        industrial_records: List[IndustrialRecord],
        k1: float,
        k2: float,
        results: Optional[WaterDemandResults] = None
    ) -> List[Dict[str, Any]]:
        """
        Genera la matriz de auditoría técnica casilla por casilla para
        trazabilidad matemática y cumplimiento normativo.
        """
        audit_rows = []

        # 1. Modo de Cálculo
        mode_label = "RAS 0330 (Colombia)" if domestic_input.mode == CalculationMode.NORMATIVE_RAS else "Modo Exploratorio"
        audit_rows.append({
            "Casilla / Parámetro": "Marco Normativo de Diseño",
            "Valor Ingresado": mode_label,
            "Unidad": "adimensional",
            "Rango / Criterio Técnico": "Res. 0330/2017 o Libre",
            "Ecuación / Marco de Referencia": "Resolución 0330 de 2017 (MinVivienda Colombia)",
            "Estado": "✅ Conforme",
            "Diagnóstico de Ingeniería": f"Evaluado bajo piso térmico {domestic_input.altitude_zone.value}."
        })

        # 2. Población
        pop_status = "✅ Válido"
        pop_diag = "Población censal proyectada para horizonte de diseño."
        if domestic_input.population <= 0:
            pop_status = "❌ Incoherente"
            pop_diag = "La población debe ser mayor a cero."
        audit_rows.append({
            "Casilla / Parámetro": "Población de Diseño (P)",
            "Valor Ingresado": f"{domestic_input.population:,}",
            "Unidad": "habitantes",
            "Rango / Criterio Técnico": "P ≥ 1 (enteros)",
            "Ecuación / Marco de Referencia": "Proyección censal conforme a Art. 39 Res. 0330",
            "Estado": pop_status,
            "Diagnóstico de Ingeniería": pop_diag
        })

        # 3. Dotación Neta
        dot_status = "✅ Conforme"
        dot_diag = "Dotación conforme con estándares sanitarios."
        if domestic_input.mode == CalculationMode.NORMATIVE_RAS:
            ras_max = RAS_MAX_NET_ENDOWMENT.get(domestic_input.altitude_zone, 140.0)
            if domestic_input.endowment_L_hab_day > ras_max:
                dot_status = "❌ No Conforme RAS"
                dot_diag = f"Supera límite legal de {ras_max:.0f} L/hab·día (Art. 43 Res. 0330/2017)."
            else:
                dot_diag = f"Conforme con límite legal máximo de {ras_max:.0f} L/hab·día (Art. 43)."
        else:
            if domestic_input.endowment_L_hab_day < 25.0:
                dot_status = "❌ Inadmisible"
                dot_diag = "Inferior al mínimo vital OMS."
            elif domestic_input.endowment_L_hab_day > 350.0:
                dot_status = "⚠️ Advertencia"
                dot_diag = "Dotación elevada."

        audit_rows.append({
            "Casilla / Parámetro": "Dotación Neta (Dneta)",
            "Valor Ingresado": f"{domestic_input.endowment_L_hab_day:.2f}",
            "Unidad": "L/hab·día",
            "Rango / Criterio Técnico": f"≤ {RAS_MAX_NET_ENDOWMENT.get(domestic_input.altitude_zone, 140.0):.0f} L/hab·d (RAS Art. 43)" if domestic_input.mode == CalculationMode.NORMATIVE_RAS else "25 a 500 L/hab·d",
            "Ecuación / Marco de Referencia": "Art. 43 Res. 0330 de 2017",
            "Estado": dot_status,
            "Diagnóstico de Ingeniería": dot_diag
        })

        # 4. Pérdidas Técnicas
        loss_status = "✅ Conforme"
        loss_diag = "Pérdidas dentro de parámetros técnicos."
        if domestic_input.mode == CalculationMode.NORMATIVE_RAS:
            if domestic_input.technical_losses_pct > RAS_MAX_TECHNICAL_LOSSES_PCT:
                loss_status = "❌ No Conforme RAS"
                loss_diag = f"Supera el 25.0% máximo admisible según Art. 44 Res. 0330/2017."
            else:
                loss_diag = "Cumple con el límite normativo de pérdidas admisibles (≤ 25%)."
        else:
            if domestic_input.technical_losses_pct > 35.0:
                loss_status = "⚠️ Pérdidas Altas"
                loss_diag = "Pérdidas elevadas en red física."

        audit_rows.append({
            "Casilla / Parámetro": "Pérdidas Técnicas en Red (%P)",
            "Valor Ingresado": f"{domestic_input.technical_losses_pct:.1f}%",
            "Unidad": "%",
            "Rango / Criterio Técnico": "≤ 25.0% (RAS Art. 44) o ≤ 55.0% (Exploratorio)",
            "Ecuación / Marco de Referencia": "Art. 44 Res. 0330 de 2017",
            "Estado": loss_status,
            "Diagnóstico de Ingeniería": loss_diag
        })

        # 5. Dotación Bruta
        try:
            d_gross = domestic_input.get_gross_endowment()
            d_gross_str = f"{d_gross:.2f}"
            gross_st = "✅ Calculado"
            gross_dg = f"Factor de mayoración por pérdidas: {(d_gross / domestic_input.endowment_L_hab_day):.3f}"
        except Exception as e:
            d_gross_str = "Error"
            gross_st = "❌ Bloqueado"
            gross_dg = str(e)

        audit_rows.append({
            "Casilla / Parámetro": "Dotación Bruta de Diseño (Dbruta)",
            "Valor Ingresado": d_gross_str,
            "Unidad": "L/hab·día",
            "Rango / Criterio Técnico": "Dbruta = Dneta / (1 - %P/100)",
            "Ecuación / Marco de Referencia": "Fórmula general de Dotación Bruta Sanitaria",
            "Estado": gross_st,
            "Diagnóstico de Ingeniería": gross_dg
        })

        # 6. Coeficientes k1 y k2
        k1_st = "✅ Conforme" if 1.00 <= k1 <= 1.50 else ("⚠️ Advertencia" if k1 > 1.50 else "❌ Incoherente")
        audit_rows.append({
            "Casilla / Parámetro": "Coeficiente Variación Diaria (k₁)",
            "Valor Ingresado": f"{k1:.2f}",
            "Unidad": "adimensional",
            "Rango / Criterio Técnico": "1.20 a 1.30 (Art. 47 Res. 0330)",
            "Ecuación / Marco de Referencia": "QMD = k₁ · Qmd",
            "Estado": k1_st,
            "Diagnóstico de Ingeniería": "Diseño de obras de captación, aducción y PTAP."
        })

        k2_st = "✅ Conforme" if 1.00 <= k2 <= 2.20 else ("⚠️ Advertencia" if k2 > 2.20 else "❌ Incoherente")
        audit_rows.append({
            "Casilla / Parámetro": "Coeficiente Variación Horaria (k₂)",
            "Valor Ingresado": f"{k2:.2f}",
            "Unidad": "adimensional",
            "Rango / Criterio Técnico": "1.40 a 1.60 (Art. 48 Res. 0330)",
            "Ecuación / Marco de Referencia": "QMH = k₂ · QMD",
            "Estado": k2_st,
            "Diagnóstico de Ingeniería": "Diseño de redes de distribución y equipos de bombeo a red."
        })

        # 7. Balance Industrial
        tot_ind_m3 = sum(r.calculate_volume_m3_day() for r in industrial_records) if industrial_records else 0.0
        audit_rows.append({
            "Casilla / Parámetro": "Consumo Industrial Consolidado",
            "Valor Ingresado": f"{tot_ind_m3:,.2f}",
            "Unidad": "m³/día",
            "Rango / Criterio Técnico": "≥ 0.0 m³/día",
            "Ecuación / Marco de Referencia": "Vind = ∑(Ui · ce,i) o ingreso directo",
            "Estado": "✅ Válido",
            "Diagnóstico de Ingeniería": f"{len(industrial_records)} industrias registradas en el balance."
        })

        return audit_rows

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
        Calcula la demanda total del sistema integrando validaciones estrictas
        y trazabilidad casilla por casilla.
        """
        dom_report = domestic_input.validate_strict()
        peak_report = cls.validate_peak_factors(k1, k2, domestic_input.mode)

        all_errors = list(dom_report.errors) + list(peak_report.errors)
        all_warnings = list(dom_report.warnings) + list(peak_report.warnings)

        for rec in industrial_records:
            ind_rep = rec.validate_strict()
            all_errors.extend(ind_rep.errors)
            all_warnings.extend(ind_rep.warnings)

        combined_report = ValidationReport(
            is_valid=(len(all_errors) == 0),
            errors=all_errors,
            warnings=all_warnings,
            ras_non_compliance=dom_report.ras_non_compliance
        )

        if not combined_report.is_valid:
            raise ValueError("; ".join(all_errors))

        # Cálculos de Demanda
        dom_vol_m3, dom_q_ls, gross_endowment = cls.calculate_domestic_demand(domestic_input)
        ind_vol_m3, ind_q_ls, ind_details = cls.calculate_industrial_demand(industrial_records)

        tot_vol_m3 = dom_vol_m3 + ind_vol_m3
        tot_q_ls = dom_q_ls + ind_q_ls

        if tot_vol_m3 > 0:
            dom_pct = (dom_vol_m3 / tot_vol_m3) * 100.0
            ind_pct = (ind_vol_m3 / tot_vol_m3) * 100.0
        else:
            dom_pct = 0.0
            ind_pct = 0.0

        # Caudales Máximos (QMD y QMH):
        # En ingeniería sanitaria: si la industria tiene almacenamiento propio o régimen uniforme,
        # los factores k1 y k2 aplican únicamente al caudal doméstico.
        if apply_k_to_industrial:
            q_max_daily_ls = tot_q_ls * k1
            q_max_hourly_ls = q_max_daily_ls * k2
        else:
            q_max_daily_ls = (dom_q_ls * k1) + ind_q_ls
            q_max_hourly_ls = (dom_q_ls * k1 * k2) + ind_q_ls

        q_max_daily_m3_day = L_s_to_m3_day(q_max_daily_ls)
        q_max_hourly_m3_day = L_s_to_m3_day(q_max_hourly_ls)

        res = WaterDemandResults(
            calculation_mode=domestic_input.mode,
            altitude_zone=domestic_input.altitude_zone,
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
            apply_k_to_industrial=apply_k_to_industrial,
            q_max_daily_flow_L_s=q_max_daily_ls,
            q_max_daily_volume_m3_day=q_max_daily_m3_day,
            q_max_hourly_flow_L_s=q_max_hourly_ls,
            q_max_hourly_volume_m3_day=q_max_hourly_m3_day,
            validation_report=combined_report
        )

        res.audit_table = cls.generate_field_by_field_audit(domestic_input, industrial_records, k1, k2, res)
        return res
