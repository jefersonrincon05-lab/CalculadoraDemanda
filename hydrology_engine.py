"""
Motor de Cálculo Hidráulico y Sanitario
Calculadora de Demanda Doméstica e Industrial de Agua

Autor: Especialista en Abastecimiento de Agua e Hidrología
Versión 2.0 - Auditoría Casilla por Casilla y Validaciones Estrictas
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional


# Constantes físicas y de conversión hidráulica
SECONDS_PER_DAY = 86400.0  # 24 h * 60 min * 60 s
LITERS_PER_M3 = 1000.0     # 1 m3 = 1000 L
FACTOR_M3DAY_TO_LS = LITERS_PER_M3 / SECONDS_PER_DAY  # 1 / 86.4 ≈ 0.011574074074074073
FACTOR_LS_TO_M3DAY = SECONDS_PER_DAY / LITERS_PER_M3  # 86.4


def m3_day_to_L_s(volume_m3_day: float) -> float:
    """Convierte un volumen diario en m3/día a caudal continuo en L/s (base 24h)."""
    return (volume_m3_day * LITERS_PER_M3) / SECONDS_PER_DAY


def L_s_to_m3_day(flow_L_s: float) -> float:
    """Convierte un caudal en L/s a volumen acumulado diario en m3/día."""
    return (flow_L_s * SECONDS_PER_DAY) / LITERS_PER_M3


@dataclass
class ValidationReport:
    """Informe estructurado de validación de datos."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class DomesticDemandInput:
    """Parámetros de entrada para el cálculo de demanda doméstica."""
    population: int                        # Población de diseño (habitantes)
    endowment_L_hab_day: float             # Dotación neta (L/hab·día)
    technical_losses_pct: float = 0.0      # Pérdidas físicas o técnicas estimadas en red (%)

    def validate_strict(self) -> ValidationReport:
        """
        Valida casilla por casilla que los datos sean coherentes técnica
        y matemáticamente. Rechaza datos imposibles o absurdos.
        """
        errors = []
        warnings = []

        # 1. Casilla: Población
        if not isinstance(self.population, (int, float)) or self.population != int(self.population):
            errors.append("Casilla 'Población': Debe ser un número entero de habitantes.")
        elif self.population <= 0:
            errors.append("Casilla 'Población': Debe ser mayor a 0 habitantes para proyectar el abastecimiento.")
        elif self.population > 25_000_000:
            warnings.append("Casilla 'Población': Población superior a 25 millones de habitantes. Requiere modelación sectorizada por macromallas.")

        # 2. Casilla: Dotación Neta
        if self.endowment_L_hab_day <= 0:
            errors.append("Casilla 'Dotación Neta': Debe ser un valor estrictamente positivo.")
        elif self.endowment_L_hab_day < 25.0:
            errors.append("Casilla 'Dotación Neta': Inadmisible (< 25 L/hab·día). Es inferior al umbral mínimo vital de subsistencia humana establecido por la OMS (Organización Mundial de la Salud).")
        elif self.endowment_L_hab_day > 500.0:
            errors.append("Casilla 'Dotación Neta': Incoherente (> 500 L/hab·día). Una dotación estrictamente doméstica no alcanza este orden de magnitud sin consumos industriales encubiertos.")
        elif self.endowment_L_hab_day < 70.0:
            warnings.append("Casilla 'Dotación Neta': Nivel bajo (< 70 L/hab·día). Característico de zonas rurales o abastecimiento por piletas públicas.")
        elif self.endowment_L_hab_day > 250.0:
            warnings.append("Casilla 'Dotación Neta': Elevada (> 250 L/hab·día). Típica de climas muy cálidos o zonas de estrato alto con riego de jardines y piscinas.")

        # 3. Casilla: Pérdidas Técnicas
        if self.technical_losses_pct < 0.0:
            errors.append("Casilla 'Pérdidas Técnicas': No pueden ser negativas.")
        elif self.technical_losses_pct >= 60.0:
            errors.append(f"Casilla 'Pérdidas Técnicas': Inadmisible ({self.technical_losses_pct:.1f}%). Pérdidas iguales o superiores al 60% representan un colapso inaceptable de la red y generan asíntotas de sobredimensionamiento.")
        elif self.technical_losses_pct >= 40.0:
            warnings.append(f"Casilla 'Pérdidas Técnicas': Nivel crítico ({self.technical_losses_pct:.1f}%). Requiere un plan de choque de micromedición y control de fugas.")

        return ValidationReport(
            is_valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings
        )

    def validate(self) -> List[str]:
        """Compatibilidad con versión anterior."""
        report = self.validate_strict()
        return report.errors

    def get_gross_endowment(self) -> float:
        """
        Calcula la dotación bruta considerando las pérdidas en la red.
        Dotación Bruta = Dotación Neta / (1 - Pérdidas/100)
        """
        report = self.validate_strict()
        if not report.is_valid:
            raise ValueError("; ".join(report.errors))

        loss_factor = 1.0 - (self.technical_losses_pct / 100.0)
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
    operating_hours_per_day: float = 24.0      # Horas de operación diaria del proceso

    def validate_strict(self) -> ValidationReport:
        """Valida que los datos industriales sean coherentes y positivos."""
        errors = []
        warnings = []

        if not self.name or not self.name.strip():
            errors.append("El nombre o razón social de la industria no puede estar vacío.")

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
                warnings.append(f"'{self.name}' tiene unidades producidas pero consumo específico 0 (demanda nula).")
        else:
            errors.append(f"Modo '{self.mode}' no reconocido. Use 'direct' o 'specific'.")

        return ValidationReport(
            is_valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings
        )

    def calculate_volume_m3_day(self) -> float:
        """Calcula el volumen diario en m3/día según el método seleccionado."""
        report = self.validate_strict()
        if not report.is_valid:
            raise ValueError("; ".join(report.errors))

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
        """Calcula el caudal medio diario en L/s distribuido en 24 horas (base balance hídrico)."""
        vol_m3 = self.calculate_volume_m3_day()
        return m3_day_to_L_s(vol_m3)

    def calculate_operating_flow_L_s(self) -> float:
        """
        Calcula el caudal de bombeo/toma durante el horario de operación fabril (Hop).
        Q_op = (Volumen_m3 * 1000) / (Hop * 3600) [L/s]
        Indispensable para dimensionar la acometida y tubería de entrada a la fábrica.
        """
        vol_m3 = self.calculate_volume_m3_day()
        seconds_op = max(0.5, float(self.operating_hours_per_day)) * 3600.0
        return (vol_m3 * LITERS_PER_M3) / seconds_op


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
    def validate_peak_factors(k1: float, k2: float) -> ValidationReport:
        """Valida rigurosamente la coherencia de los coeficientes k1 y k2."""
        errors = []
        warnings = []

        if k1 < 1.00:
            errors.append(f"Casilla 'Factor k₁': Incoherente ({k1:.2f}). Por definición física y estadística, el Caudal Máximo Diario no puede ser menor que el caudal medio diario (k₁ ≥ 1.00).")
        elif k1 > 1.60:
            warnings.append(f"Casilla 'Factor k₁': Elevado ({k1:.2f}). Valores típicos normativos oscilan entre 1.15 y 1.30.")

        if k2 < 1.00:
            errors.append(f"Casilla 'Factor k₂': Incoherente ({k2:.2f}). La hora de mayor consumo no puede tener un caudal menor que el promedio del día (k₂ ≥ 1.00).")
        elif k2 > 2.50:
            warnings.append(f"Casilla 'Factor k₂': Muy elevado ({k2:.2f}). Valores típicos normativos oscilan entre 1.40 y 1.60.")

        return ValidationReport(is_valid=(len(errors) == 0), errors=errors, warnings=warnings)

    @staticmethod
    def calculate_domestic_demand(inp: DomesticDemandInput) -> Tuple[float, float, float]:
        """
        Calcula la demanda media diaria doméstica tras validación estricta.
        Retorna: (volumen_m3_dia, caudal_L_s, dotacion_bruta)
        """
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
        """Calcula la demanda media diaria industrial y caudales de turno."""
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

            method_desc = (
                f"Directo: {rec.direct_consumption_m3_day:,.2f} m³/día"
                if rec.mode == "direct"
                else f"Específico: {rec.units_per_day:,.2f} u/día × {rec.specific_consumption:,.4f} {rec.specific_unit}"
            )

            details.append({
                "Nombre": rec.name,
                "Método": "Directo" if rec.mode == "direct" else "Consumo Específico",
                "Descripción": method_desc,
                "Horas Operación": f"{rec.operating_hours_per_day:.1f} h/día",
                "Volumen Diario (m³/día)": round(vol_m3, 4),
                "Caudal Medio 24h (L/s)": round(q_ls, 4),
                "Caudal en Turno Operativo (L/s)": round(q_op_ls, 4),
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
        Genera una auditoría matemática y técnica casilla por casilla.
        Permite a los ingenieros y revisores auditar cada parámetro.
        """
        audit_rows = []

        # 1. Población
        pop_status = "✅ Válido"
        pop_diag = "Población dentro de rango operativo para proyectos de abastecimiento."
        if domestic_input.population <= 0:
            pop_status = "❌ Incoherente"
            pop_diag = "La población no puede ser cero ni negativa."
        elif domestic_input.population > 25_000_000:
            pop_status = "⚠️ Advertencia"
            pop_diag = "Población excepcionalmente grande."

        audit_rows.append({
            "Casilla / Parámetro": "Población de Diseño (P)",
            "Valor Ingresado": f"{domestic_input.population:,}",
            "Unidad": "habitantes",
            "Rango Técnico Admisible": "P ≥ 1 (enteros)",
            "Ecuación / Principio": "Población censal + proyección por método geométrico/exponencial",
            "Estado": pop_status,
            "Diagnóstico de Ingeniería": pop_diag
        })

        # 2. Dotación Neta
        dot_status = "✅ Válido"
        dot_diag = "Dotación conforme a estándares sanitarios usuales."
        if domestic_input.endowment_L_hab_day < 25.0:
            dot_status = "❌ Inadmisible"
            dot_diag = "Inferior al mínimo vital OMS (20-25 L/hab·día)."
        elif domestic_input.endowment_L_hab_day > 500.0:
            dot_status = "❌ Incoherente"
            dot_diag = "Superior al umbral doméstico máximo razonable (500 L/hab·día)."
        elif domestic_input.endowment_L_hab_day < 70.0 or domestic_input.endowment_L_hab_day > 250.0:
            dot_status = "⚠️ Advertencia"
            dot_diag = "Fuera de la franja típica (70 - 250 L/hab·día)."

        audit_rows.append({
            "Casilla / Parámetro": "Dotación Neta (Dneta)",
            "Valor Ingresado": f"{domestic_input.endowment_L_hab_day:.2f}",
            "Unidad": "L/hab·día",
            "Rango Técnico Admisible": "25.0 a 500.0 L/hab·día",
            "Ecuación / Principio": "Asignación per cápita según piso térmico y hábitos de consumo",
            "Estado": dot_status,
            "Diagnóstico de Ingeniería": dot_diag
        })

        # 3. Pérdidas Técnicas
        loss_status = "✅ Válido"
        loss_diag = "Porcentaje de pérdidas dentro del estándar de red."
        if domestic_input.technical_losses_pct < 0.0 or domestic_input.technical_losses_pct >= 60.0:
            loss_status = "❌ Inadmisible"
            loss_diag = "Pérdidas negativas o iguales/superiores al 60% colapsan la ecuación dotacional."
        elif domestic_input.technical_losses_pct >= 40.0:
            loss_status = "⚠️ Crítico"
            loss_diag = "Pérdidas elevadas. Requiere detección activa de fugas."

        audit_rows.append({
            "Casilla / Parámetro": "Pérdidas Técnicas (%P)",
            "Valor Ingresado": f"{domestic_input.technical_losses_pct:.1f}%",
            "Unidad": "%",
            "Rango Técnico Admisible": "0.0% a 59.9%",
            "Ecuación / Principio": "Dbruta = Dneta / (1 - %P/100)",
            "Estado": loss_status,
            "Diagnóstico de Ingeniería": loss_diag
        })

        # 4. Dotación Bruta Resultante
        try:
            gross = domestic_input.get_gross_endowment()
            gross_str = f"{gross:.2f}"
            gross_status = "✅ Calculado"
            gross_diag = f"Factor de mayoración por fugas: {(gross / domestic_input.endowment_L_hab_day):.3f}"
        except Exception as e:
            gross_str = "Error"
            gross_status = "❌ Bloqueado"
            gross_diag = str(e)

        audit_rows.append({
            "Casilla / Parámetro": "Dotación Bruta (Dbruta)",
            "Valor Ingresado": gross_str,
            "Unidad": "L/hab·día",
            "Rango Técnico Admisible": "Dbruta ≥ Dneta",
            "Ecuación / Principio": "Dbruta = Dneta / (1 - %P/100)",
            "Estado": gross_status,
            "Diagnóstico de Ingeniería": gross_diag
        })

        # 5. Factor k1
        k1_status = "✅ Válido"
        k1_diag = "Coeficiente diario consistente con patrones de consumo."
        if k1 < 1.00:
            k1_status = "❌ Incoherente"
            k1_diag = "k1 no puede ser inferior a 1.00 (el día máximo no puede ser menor a la media)."
        elif k1 > 1.60:
            k1_status = "⚠️ Advertencia"
            k1_diag = "k1 superior al rango normativo habitual (1.15 - 1.30)."

        audit_rows.append({
            "Casilla / Parámetro": "Coeficiente Variación Diaria (k₁)",
            "Valor Ingresado": f"{k1:.2f}",
            "Unidad": "adimensional",
            "Rango Técnico Admisible": "1.00 ≤ k₁ ≤ 1.60",
            "Ecuación / Principio": "QMD = k₁ · Qmd",
            "Estado": k1_status,
            "Diagnóstico de Ingeniería": k1_diag
        })

        # 6. Factor k2
        k2_status = "✅ Válido"
        k2_diag = "Coeficiente horario consistente."
        if k2 < 1.00:
            k2_status = "❌ Incoherente"
            k2_diag = "k2 no puede ser menor a 1.00 (la hora máxima no puede ser menor al día máximo)."
        elif k2 > 2.50:
            k2_status = "⚠️ Advertencia"
            k2_diag = "k2 superior a 2.50 (típico solo en poblaciones minúsculas)."

        audit_rows.append({
            "Casilla / Parámetro": "Coeficiente Variación Horaria (k₂)",
            "Valor Ingresado": f"{k2:.2f}",
            "Unidad": "adimensional",
            "Rango Técnico Admisible": "1.00 ≤ k₂ ≤ 2.50",
            "Ecuación / Principio": "QMH = k₂ · QMD",
            "Estado": k2_status,
            "Diagnóstico de Ingeniería": k2_diag
        })

        # 7. Balance Industrial
        tot_ind_m3 = sum(r.calculate_volume_m3_day() for r in industrial_records) if industrial_records else 0.0
        audit_rows.append({
            "Casilla / Parámetro": "Consumo Industrial Consolidado",
            "Valor Ingresado": f"{tot_ind_m3:,.2f}",
            "Unidad": "m³/día",
            "Rango Técnico Admisible": "≥ 0.0 m³/día",
            "Ecuación / Principio": "Vind = ∑(Ui · ce,i) o ingreso directo",
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
        # 1. Validar entradas
        dom_report = domestic_input.validate_strict()
        peak_report = cls.validate_peak_factors(k1, k2)

        all_errors = list(dom_report.errors) + list(peak_report.errors)
        all_warnings = list(dom_report.warnings) + list(peak_report.warnings)

        for rec in industrial_records:
            ind_rep = rec.validate_strict()
            all_errors.extend(ind_rep.errors)
            all_warnings.extend(ind_rep.warnings)

        combined_report = ValidationReport(
            is_valid=(len(all_errors) == 0),
            errors=all_errors,
            warnings=all_warnings
        )

        if not combined_report.is_valid:
            # Generar tabla de auditoría con los errores identificados
            audit = cls.generate_field_by_field_audit(domestic_input, industrial_records, k1, k2, None)
            raise ValueError("; ".join(all_errors))

        # 2. Cálculos hidráulicos
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

        # Caudales Máximos
        if apply_k_to_industrial:
            q_max_daily_ls = tot_q_ls * k1
            q_max_hourly_ls = q_max_daily_ls * k2
        else:
            q_max_daily_ls = (dom_q_ls * k1) + ind_q_ls
            q_max_hourly_ls = (dom_q_ls * k1 * k2) + ind_q_ls

        q_max_daily_m3_day = L_s_to_m3_day(q_max_daily_ls)
        q_max_hourly_m3_day = L_s_to_m3_day(q_max_hourly_ls)

        res = WaterDemandResults(
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
