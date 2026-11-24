# 💧 Calculadora de Demanda Doméstica e Industrial de Agua (v2.0)

Una aplicación web técnica y profesional construida con **Python** y **Streamlit** para ingenieros civiles, sanitarios, hidráulicos y planificadores de recursos hídricos. Permite estimar, desagregar y proyectar la **Demanda Media Diaria ($Q_{md}$)** de agua potable para sectores residenciales e industriales, con **auditoría matemática casilla por casilla**, **validación estricta anti-incoherencias** y diferenciación rigurosa con los **Caudales Máximos de Diseño ($Q_{MD}$ y $Q_{MH}$)**.

---

## 📋 Tabla de Contenidos
- [Novedades de la Versión 2.0](#-novedades-de-la-versión-20)
- [Auditoría Casilla por Casilla y Validación Anti-Incoherencias](#-auditoría-casilla-por-casilla-y-validación-anti-incoherencias)
- [Fundamentos Teóricos y Ecuaciones Hidráulicas](#-fundamentos-teóricos-y-ecuaciones-hidráulicas)
- [Diferenciación entre Demanda Media y Consumos Máximos](#-diferenciación-entre-demanda-media-y-consumos-máximos)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Ejecución Local](#-instalación-y-ejecución-local)
- [Pruebas Unitarias y Validación Matemática](#-pruebas-unitarias-y-validación-matemática)
- [Repositorio en GitHub](#-repositorio-en-github)

---

## 🌟 Novedades de la Versión 2.0

1. **Rediseño Completo de la Interfaz:**
   - Estilo SaaS de ingeniería de alto contraste con tarjetas KPI visuales, badges de validación en tiempo real y gráficos interactivos con Plotly.
2. **Auditoría Matemática Casilla por Casilla:**
   - Pestaña dedicada con matriz de trazabilidad paso a paso: cada parámetro de entrada muestra su valor, unidad, rango técnico admisible, ecuación aplicada, estado de consistencia y diagnóstico hidráulico.
3. **Validación Estricta Anti-Incoherencias:**
   - Bloqueo inmediato de cálculos ante datos absurdos o físicamente imposibles.
4. **Caudal en Turno Operativo Industrial ($Q_{op}$):**
   - Incorporación de horas de operación diaria ($H_{op}$) para calcular el caudal real de acometida fabril en turnos restringidos (8h, 12h, 16h).

---

## 🛡️ Auditoría Casilla por Casilla y Validación Anti-Incoherencias

El sistema somete cada celda a un control de calidad hidráulico riguroso:

| Casilla / Parámetro | Rango Admisible | Tratamiento de Incoherencias | Diagnóstico Técnico |
| :--- | :---: | :--- | :--- |
| **Población ($P$)** | $P \ge 1$ (enteros) | ❌ Bloquea valores $\le 0$ o no enteros | Población proyectada para el horizonte de diseño de la red. |
| **Dotación Neta ($D_{neta}$)** | $25.0$ a $500.0\text{ L/hab}\cdot\text{día}$ | ❌ Bloquea valores $< 25$ (mínimo vital OMS) o $> 500$ (anomalía doméstica) | Semáforo de advertencia si está fuera del rango típico (70 - 250 L/hab·día). |
| **Pérdidas de Red ($\%P$)** | $0.0\%$ a $59.9\%$ | ❌ Bloquea valores negativos o $\ge 60\%$ (colapso de red) | Clasificación de eficiencia: Verde (<15%), Azul (15-30%), Amarillo (30-45%), Rojo (>45%). |
| **Factor Diario ($k_1$)** | $1.00 \le k_1 \le 1.60$ | ❌ Bloquea $k_1 < 1.00$ (el día máximo no puede ser menor a la media) | Coeficiente normativo para captaciones, aducciones y PTAP (típico 1.15 - 1.30). |
| **Factor Horario ($k_2$)** | $1.00 \le k_2 \le 2.50$ | ❌ Bloquea $k_2 < 1.00$ (la hora pico no puede consumir menos que el día) | Coeficiente normativo para redes de distribución y bombeo (típico 1.40 - 1.60). |
| **Horas Industriales ($H_{op}$)** | $0.5 \le H_{op} \le 24.0\text{ h/día}$ | ❌ Bloquea horas $\le 0$ o $> 24$ | Permite calcular el caudal de diseño de acometida fabril $Q_{op}$. |

---

## 📐 Fundamentos Teóricos y Ecuaciones Hidráulicas

### 1. Factor de Conversión de Caudal Continuo
Considerando $86\,400$ segundos en un día ($24 \times 60 \times 60$) y $1\text{ m}^3 = 1\,000\text{ L}$:

$$\text{Factor} = \frac{86\,400 \text{ s/día}}{1\,000 \text{ L/m}^3} = 86.40$$

$$V \text{ [m}^3/\text{día]} = Q \text{ [L/s]} \times 86.40 \quad \Longleftrightarrow \quad Q \text{ [L/s]} = \frac{V \text{ [m}^3/\text{día]}}{86.40}$$

### 2. Demanda Media Diaria Doméstica ($Q_{md, dom}$)
$$D_{bruta} = \frac{D_{neta}}{1 - \frac{\%P_{pérdidas}}{100}} \quad [L/\text{hab}\cdot\text{día}]$$

$$V_{dom} = \frac{P \times D_{bruta}}{1\,000} \quad [m^3/\text{día}]$$

$$Q_{md, dom} = \frac{P \times D_{bruta}}{86\,400} = \frac{V_{dom}}{86.40} \quad [L/s]$$

### 3. Demanda Industrial y Caudal en Turno ($Q_{ind}$ y $Q_{op}$)
- **Volumen Diario Consolidado:**
  $$V_{ind} = \sum_{i=1}^{n} (U_i \times c_{e,i}) \quad [m^3/\text{día}]$$
- **Caudal Medio Diario 24h (para balances):**
  $$Q_{md, ind} = \frac{V_{ind}}{86.40} \quad [L/s]$$
- **Caudal de Turno Operativo (para dimensionamiento de acometida fabril):**
  $$Q_{op, ind} = \frac{V_{ind} \times 1\,000}{H_{op} \times 3\,600} \quad [L/s]$$

---

## ⚡ Diferenciación entre Demanda Media y Consumos Máximos

| Parámetro | Símbolo | Ecuación | Aplicación en Obras Civiles e Hidráulicas |
| :--- | :---: | :---: | :--- |
| **Demanda Media Diaria** | $Q_{md}$ | Base de consumo continuo | Balance hidrológico de la cuenca, concesiones ambientales de agua y estimación de volúmenes anuales. |
| **Caudal Máximo Diario** | $Q_{MD}$ | $k_1 \cdot Q_{md}$ | Dimensionamiento de obras de **captación, desarenadores, conducciones principales (aducciones), plantas de tratamiento (PTAP) y tanques de reserva**. |
| **Caudal Máximo Horario** | $Q_{MH}$ | $k_2 \cdot Q_{MD}$ | Dimensionamiento de las **redes de distribución, tuberías matrices y estaciones de bombeo de impulsión directa**. |

---

## 📁 Estructura del Proyecto

```
HIDROLOGIA JEFERSON/
├── app.py                  # Interfaz moderna en Streamlit v2.0
├── hydrology_engine.py      # Motor de cálculo y auditoría casilla por casilla
├── test_calculations.py    # Suite de 15 pruebas unitarias con pytest
├── requirements.txt        # Dependencias de Python requeridas
└── README.md               # Documentación técnica del proyecto
```

---

## 💻 Instalación y Ejecución Local

1. **Abrir la terminal o PowerShell** en la carpeta del proyecto:
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

## 🧪 Pruebas Unitarias y Validación Matemática

Para ejecutar las 15 pruebas unitarias automatizadas:

```bash
pytest test_calculations.py -v
```

---

## 🌐 Repositorio en GitHub

El código fuente está publicado y sincronizado en:
[https://github.com/jefersonrincon05-lab/CalculadoraDemanda](https://github.com/jefersonrincon05-lab/CalculadoraDemanda)
