# 💧 Calculadora de Demanda Doméstica e Industrial de Agua (v3.0)

Plataforma técnica, profesional y auditable de **Ingeniería Sanitaria e Hidráulica**, desarrollada en **Python** y **Streamlit** para dimensionamiento de sistemas de abastecimiento de agua potable, balances hídricos y estimación de caudales de diseño.

Implementa el marco normativo colombiano **RAS (Resolución 0330 de 2017 del Ministerio de Vivienda, Ciudad y Territorio)**, así como un **Modo Exploratorio / Libre** para proyectos internacionales y análisis de sensibilidad técnica.

---

## 📋 Tabla de Contenidos
- [Novedades de la Versión 3.0](#-novedades-de-la-versión-30)
- [Marco Normativo RAS 0330 / 2017 vs. Modo Exploratorio](#-marco-normativo-ras-0330--2017-vs-modo-exploratorio)
- [Fundamentación Matemática y Ecuaciones Hidráulicas](#-fundamentación-matemática-y-ecuaciones-hidráulicas)
- [Diferenciación Rigurosa entre Demanda Media y Caudales Máximos](#-diferenciación-rigurosa-entre-demanda-media-y-caudales-máximos)
- [Reconstrucción Profesional del Libro Excel (5 Hojas)](#-reconstrucción-profesional-del-libro-excel-5-hojas)
- [Informe Técnico en PDF](#-informe-técnico-en-pdf)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Ejecución Local](#-instalación-y-ejecución-local)
- [Pruebas Unitarias Automatizadas (pytest)](#-pruebas-unitarias-automatizadas-pytest)

---

## 🌟 Novedades de la Versión 3.0

1. **Rediseño Completo de la Interfaz:**
   - Paleta sobria de consultoría: Azul petróleo (`#123047`), Turquesa técnico (`#149D9A`), Fondo suave (`#F7F9FC`) y Blanco técnico (`#FFFFFF`).
   - Organización en 4 pestañas especializadas:
     1. *Demanda doméstica*
     2. *Demanda industrial*
     3. *Resultados y auditoría*
     4. *Exportación de informes*
2. **Cumplimiento Normativo RAS (Resolución 0330 de 2017):**
   - Incorporación de pisos térmicos y cotas altimétricas (Art. 43) y límite del 25% en pérdidas técnicas (Art. 44).
   - Distinción explícita de un *Modo Exploratorio* para modelaciones sin sujeción a la norma colombiana.
3. **Reconstrucción Integral del Libro Excel (`openpyxl`):**
   - 5 hojas técnicas formalizadas con fórmulas auditables en celdas, valores numéricos reales, filtros automáticos, paneles congelados, gráficos incrustados y verificación de concordancia `Python vs Excel`.
4. **Eliminación de Formatos TXT y CSV en Pantalla:**
   - Supresión de descargas planas en bloc de notas. Descarga principal en Excel y descarga complementaria en PDF formal.
5. **Inventario Industrial Unificado:**
   - Tabla interactiva editable (`st.data_editor`) vinculada directamente al motor de cálculo en tiempo real.
   - Cálculo del **Caudal en Turno Operativo ($Q_{op}$)** para dimensionamiento de acometidas fabriles en jornadas restringidas (8h, 12h, 16h).

---

## 🏛️ Marco Normativo RAS 0330 / 2017 vs. Modo Exploratorio

| Criterio / Parámetro | Modo Normativo RAS (Res. 0330/2017) | Modo Exploratorio / Libre |
| :--- | :--- | :--- |
| **Dotación Neta Máxima (Art. 43)** | - Clima Frío ($> 2.000\text{ msnm}$): **$120\text{ L/hab}\cdot\text{día}$**<br/>- Clima Templado ($1.000 - 2.000\text{ msnm}$): **$130\text{ L/hab}\cdot\text{día}$**<br/>- Clima Cálido ($< 1.000\text{ msnm}$): **$140\text{ L/hab}\cdot\text{día}$** | Admite dotaciones ampliadas ($25 - 500\text{ L/hab}\cdot\text{día}$) con advertencias técnicas para investigación o normativas internacionales. |
| **Pérdidas Técnicas en Red (Art. 44)** | **Máximo 25.0%** ($P \le 25\%$) conforme a metas de eficiencia física de red. | Permite modelar redes en estado crítico de fugas hasta el $55.0\%$. |
| **Factores de Pico ($k_1, k_2$)** | Art. 47 y 48: Sugeridos automáticamente por tamaño poblacional ($k_1 = 1.20 - 1.30$, $k_2 = 1.40 - 1.60$). | Ajustables manualmente por el proyectista con comprobación de límites físicos ($k \ge 1.00$). |
| **Régimen Industrial** | Distingue industrias con almacenamiento propio (régimen continuo amortiguado) de industrias sin tanque. | Permite seleccionar libremente si $k_1$ y $k_2$ afectan al sector industrial. |

---

## 📐 Fundamentación Matemática y Ecuaciones Hidráulicas

### 1. Factor de Conversión de Caudal Continuo
Considerando $86\,400$ segundos en un día ($24 \times 60 \times 60$) y $1\text{ m}^3 = 1\,000\text{ L}$:

$$\text{Factor} = \frac{86\,400 \text{ s/día}}{1\,000 \text{ L/m}^3} = 86.40$$

$$V \text{ [m}^3/\text{día]} = Q \text{ [L/s]} \times 86.40 \quad \Longleftrightarrow \quad Q \text{ [L/s]} = \frac{V \text{ [m}^3/\text{día]}}{86.40}$$

### 2. Demanda Media Diaria Doméstica ($Q_{md, dom}$)
$$D_{bruta} = \frac{D_{neta}}{1 - \frac{\%P}{100}} \quad [L/\text{hab}\cdot\text{día}]$$

$$V_{dom} = \frac{P \times D_{bruta}}{1\,000} \quad [m^3/\text{día}]$$

$$Q_{md, dom} = \frac{P \times D_{bruta}}{86\,400} = \frac{V_{dom}}{86.40} \quad [L/s]$$

### 3. Demanda Industrial y Caudal en Turno ($Q_{ind}$ y $Q_{op}$)
- **Volumen Diario Consolidado:**
  $$V_{ind} = \sum_{i=1}^{n} (U_i \times c_{e,i}) \quad [m^3/\text{día}]$$
- **Caudal Medio Continuo 24h (para balances hídricos):**
  $$Q_{md, ind} = \frac{V_{ind}}{86.40} \quad [L/s]$$
- **Caudal en Turno Operativo (para dimensionamiento de acometida fabril):**
  $$Q_{op, ind} = \frac{V_{ind} \times 1\,000}{H_{op} \times 3\,600} \quad [L/s]$$

---

## ⚡ Diferenciación Rigurosa entre Demanda Media y Caudales Máximos

| Parámetro | Símbolo | Ecuación | Obras Civiles e Hidráulicas Asignadas |
| :--- | :---: | :---: | :--- |
| **Demanda Media Diaria** | $Q_{md}$ | $Q_{dom} + Q_{ind}$ | Concesión de aguas, balance hídrico de la fuente, balances de masa y estimación de volúmenes anuales. |
| **Caudal Máximo Diario** | $Q_{MD}$ | $(Q_{dom} \cdot k_1) + Q_{ind}$ | Dimensionamiento de **obras de captación, desarenador, línea de aducción, Planta de Tratamiento de Agua Potable (PTAP) y volumen de tanques de almacenamiento**. |
| **Caudal Máximo Horario** | $Q_{MH}$ | $(Q_{dom} \cdot k_1 \cdot k_2) + Q_{ind}$ | Dimensionamiento de **redes de distribución de tuberías, mallas matrices y equipos de bombeo directo a red**. |

---

## 📊 Reconstrucción Profesional del Libro Excel (5 Hojas)

Generado dinámicamente mediante `openpyxl` sin plantillas estáticas:

1. **`01_Resumen`:** Cuadro de mando ejecutivo con caudales en $L/s$ y $m^3/\text{día}$, porcentajes de participación, destinos de diseño y gráfico de barras incrustado.
2. **`02_Datos_Entrada`:** Parámetros de diseño (población, altitud, dotación neta, pérdidas, $k_1$, $k_2$).
3. **`03_Memoria_Calculo`:** Trazabilidad paso a paso con **fórmulas nativas de Excel enlazadas a celdas** (`=B7/(1-B8)`, `=E5*1000/86400`, etc.).
4. **`04_Detalle_Industrial`:** Desglose pormenorizado por industria, horas de operación, caudales de turno ($Q_{op}$), fuentes técnicas documentadas y totales con función `=SUM(...)`.
5. **`05_Verificacion`:** Auditoría de concordancia entre los cálculos de Python y las fórmulas de Excel, verificando que la diferencia absoluta sea $0.000000$ (tolerancia $< 10^{-4}$).

---

## 📁 Estructura del Proyecto

```
HIDROLOGIA JEFERSON/
├── app.py                  # Interfaz profesional en Streamlit v3.0
├── hydrology_engine.py      # Motor de cálculo, auditoría y validación RAS 0330
├── excel_generator.py       # Generador de memorias en Excel (5 hojas openpyxl)
├── pdf_generator.py         # Generador de informes técnicos en PDF (reportlab)
├── test_calculations.py    # Suite de pruebas unitarias automatizadas (pytest)
├── requirements.txt        # Dependencias de Python requeridas
└── README.md               # Documentación técnica completa
```

---

## 💻 Instalación y Ejecución Local

1. **Abrir la terminal en la carpeta del proyecto:**
   ```bash
   cd "c:\Users\exito\Desktop\HIDROLOGIA JEFERSON"
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación Streamlit:**
   ```bash
   streamlit run app.py
   ```

4. Abrir en el navegador: [http://localhost:8501](http://localhost:8501)

---

## 🧪 Pruebas Unitarias Automatizadas (pytest)

Para ejecutar la batería de 14 pruebas de verificación técnica:

```bash
pytest test_calculations.py -v
```
