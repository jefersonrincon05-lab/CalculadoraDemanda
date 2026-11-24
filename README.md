# 💧 Calculadora de Demanda Doméstica e Industrial de Agua

Una aplicación web técnica y profesional construida con **Python** y **Streamlit** para ingenieros civiles, sanitarios, hidráulicos y planificadores de recursos hídricos. Permite estimar, desagregar y proyectar la **Demanda Media Diaria ($Q_{md}$)** de agua potable para sectores residenciales e industriales, estableciendo una diferenciación rigurosa con los **Caudales Máximos de Diseño ($Q_{MD}$ y $Q_{MH}$)**.

---

## 📋 Tabla de Contenidos
- [Características Principales](#-características-principales)
- [Fundamentos Teóricos y Ecuaciones Hidráulicas](#-fundamentos-teóricos-y-ecuaciones-hidráulicas)
- [Diferenciación entre Demanda Media y Consumos Máximos](#-diferenciación-entre-demanda-media-y-consumos-máximos)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Ejecución Local](#-instalación-y-ejecución-local)
- [Pruebas Unitarias y Validación Matemática](#-pruebas-unitarias-y-validación-matemática)
- [Guía de Publicación en GitHub](#-guía-de-publicación-en-github)

---

## 🚀 Características Principales

1. **Módulo de Demanda Doméstica:**
   - Ingreso de población de diseño ($P$, hab) y dotación neta de agua ($L/\text{hab}\cdot\text{día}$).
   - Incorporación de pérdidas técnicas o físicas en red (% de agua no contabilizada) para determinar la **Dotación Bruta**.
   - Cálculo automático del caudal medio doméstico ($L/s$) y volumen diario ($m^3/\text{día}$).

2. **Módulo de Demanda Industrial Flexible:**
   - **Método Directo:** Ingreso de consumo volumétrico diario en $m^3/\text{día}$.
   - **Método Específico por Producción:** Cálculo a partir de unidades producidas al día y el índice de consumo específico de agua ($m^3/\text{unidad}$ o $L/\text{unidad}$).
   - **Gestor Multiproceso:** Soporte para agregar, listar y eliminar múltiples industrias con tipologías precargadas (lácteas, cerveceras, cárnicas, textiles, papeleras, concreteras, etc.).

3. **Cálculo Integrado en Doble Unidad:**
   - Resultados sincronizados simultáneamente en **Litros por segundo ($L/s$)** y **Metros cúbicos por día ($m^3/\text{día}$)**.
   - Balances porcentuales de distribución de la demanda total.

4. **Visualizaciones Gráficas Interactivas con Plotly:**
   - Diagrama de anillo (Donut Chart) con la participación porcentual de consumo.
   - Gráfico de barras comparativo entre caudales medios y caudales de diseño de pico.

5. **Exportación de Resultados Profesionales:**
   - Descarga de resumen en formato **CSV**.
   - Descarga de libro de cálculo en **Excel (.xlsx)** con hojas separadas para el resumen ejecutivo y el inventario industrial.
   - Generación de **Memoria Técnica de Cálculo** en texto plano.

---

## 📐 Fundamentos Teóricos y Ecuaciones Hidráulicas

### 1. Factor de Conversión de Caudal Continuo
Considerando que un día tiene $86\,400$ segundos ($24 \times 60 \times 60$) y que $1 \text{ m}^3 = 1\,000 \text{ L}$:

$$\text{Factor de Conversión} = \frac{86\,400 \text{ s/día}}{1\,000 \text{ L/m}^3} = 86.40$$

$$\text{Volumen } [m^3/\text{día}] = \text{Caudal } [L/s] \times 86.40$$

$$\text{Caudal } [L/s] = \frac{\text{Volumen } [m^3/\text{día}]}{86.40}$$

### 2. Demanda Media Diaria Doméstica ($Q_{md, dom}$)
Calculada a partir de la población servida y la dotación bruta:

$$D_{bruta} = \frac{D_{neta}}{1 - \frac{\%P_{pérdidas}}{100}} \quad [L/\text{hab}\cdot\text{día}]$$

$$V_{dom} = \frac{P \times D_{bruta}}{1\,000} \quad [m^3/\text{día}]$$

$$Q_{md, dom} = \frac{P \times D_{bruta}}{86\,400} \quad [L/s]$$

### 3. Demanda Media Diaria Industrial ($Q_{ind}$)
- **Por consumo directo:**
  $$Q_{ind} = \frac{V_{ind}}{86.40} \quad [L/s]$$
- **Por consumo específico por producto:**
  $$V_{ind} = \sum_{i=1}^{n} \left( U_i \times c_{e,i} \right) \quad [m^3/\text{día}]$$
  *(Donde $U_i$ son las unidades producidas/día y $c_{e,i}$ es el consumo de agua por unidad)*.

### 4. Demanda Total del Sistema ($Q_{md, total}$)
$$V_{total} = V_{dom} + V_{ind} \quad [m^3/\text{día}]$$
$$Q_{md, total} = Q_{md, dom} + Q_{md, ind} \quad [L/s]$$

---

## ⚡ Diferenciación entre Demanda Media y Consumos Máximos

En ingeniería sanitaria no se deben confundir la **Demanda Media Diaria** con los **Caudales de Diseño Máximos**:

| Parámetro | Símbolo | Ecuación | Aplicación en Obras Civiles e Hidráulicas |
| :--- | :---: | :---: | :--- |
| **Demanda Media Diaria** | $Q_{md}$ | Base de consumo continuo | Balance hidrológico de la cuenca, concesiones ambientales de agua, balances de masa y estimación de volúmenes anuales. |
| **Caudal Máximo Diario** | $Q_{MD}$ | $k_1 \cdot Q_{md}$ | Dimensionamiento de obras de captación, desarenadores, conducciones principales (aducciones), plantas de tratamiento de agua potable (PTAP) y volumen de tanques de reserva. |
| **Caudal Máximo Horario** | $Q_{MH}$ | $k_2 \cdot Q_{MD}$ | Dimensionamiento de las redes de distribución, tuberías matrices y estaciones de bombeo de impulsión directa a la red. |

> **Nota técnica sobre industrias:** Las industrias que operan con régimen continuo de 24 horas o que disponen de almacenamiento y regulación interna no imponen picos a la red municipal al mismo ritmo que las residencias. Por ello, la herramienta permite elegir si los coeficientes $k_1$ y $k_2$ afectan a la demanda total o únicamente a la componente doméstica.

---

## 📁 Estructura del Proyecto

```
HIDROLOGIA JEFERSON/
├── app.py                  # Aplicación web interactiva en Streamlit
├── hydrology_engine.py      # Motor de cálculo hidráulico desacoplado
├── test_calculations.py    # Suite de pruebas unitarias matemáticas (pytest)
├── requirements.txt        # Dependencias de Python requeridas
└── README.md               # Documentación técnica del proyecto
```

---

## 💻 Requisitos Previos

- Python 3.10 o superior (compatible y probado con Python 3.13).
- Gestor de paquetes `pip`.

---

## 🔧 Instalación y Ejecución Local

1. **Abrir la terminal o PowerShell** en la carpeta del proyecto:
   ```bash
   cd "c:\Users\exito\Desktop\HIDROLOGIA JEFERSON"
   ```

2. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación Streamlit:**
   ```bash
   streamlit run app.py
   ```

4. La aplicación se abrirá automáticamente en tu navegador web en la dirección:
   ```
   http://localhost:8501
   ```

---

## 🧪 Pruebas Unitarias y Validación Matemática

Para verificar la consistencia matemática, las conversiones de unidades y las validaciones de límites de los algoritmos:

```bash
pytest test_calculations.py -v
```

Las 14 pruebas unitarias comprueban:
- Exactitud de la constante de tiempo y volumen ($86.40$).
- Simetría bidireccional entre $L/s$ y $m^3/\text{día}$.
- Casos típicos con y sin pérdidas en red.
- Estimaciones directas y por consumo específico en litros y metros cúbicos.
- Comportamiento de agregación de sistemas y aplicación de coeficientes de pico ($k_1, k_2$).
- Validación y rechazo de valores negativos o porcentajes mayores al 100%.

---

## 🌐 Guía de Publicación en GitHub

Para subir el proyecto a un nuevo repositorio en GitHub:

1. **Inicializar el repositorio Git local:**
   ```bash
   git init
   ```

2. **Crear archivo `.gitignore`** (para no subir archivos temporales de Python):
   ```bash
   echo "__pycache__/" >> .gitignore
   echo ".pytest_cache/" >> .gitignore
   ```

3. **Agregar los archivos y realizar el primer commit:**
   ```bash
   git add .
   git commit -m "feat: Calculadora de Demanda Domestica e Industrial de Agua con Streamlit"
   ```

4. **Vincular el repositorio remoto de GitHub y subir:**
   ```bash
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/calculadora-demanda-agua.git
   git push -u origin main
   ```

5. *(Opcional)* Desplegar gratuitamente en **Streamlit Community Cloud** vinculando tu repositorio de GitHub para tener la aplicación en línea y accesible desde cualquier dispositivo.
