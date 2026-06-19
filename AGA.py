import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. Configuración de la interfaz web
st.set_page_config(page_title="Optimizador de Antenas 3D", layout="wide", page_icon="📊")

# --- DISEÑO VISUAL: FONDO BLANCO CON PATRÓN DE MARCA DE AGUA "UNM" ---
st.markdown(
    """
    <style>
    /* Fondo general blanco con marca de agua tipográfica repetida */
    .stApp {
        background-color: #ffffff;
        background-image: radial-gradient(rgba(0, 0, 0, 0.02) 1px, transparent 0),
                          url("data:image/svg+xml;utf8,<svg xmlns='http://w3.org' width='120' height='120' viewBox='0 0 120 120'><text x='50%' y='50%' font-family='Arial, sans-serif' font-size='22' font-weight='bold' fill='rgba(0, 50, 100, 0.04)' text-anchor='middle' dominant-baseline='middle'>UNM</text></svg>");
        background-attachment: fixed;
        color: #1e293b;
    }
    
    /* Asegurar contraste de textos principales sobre blanco */
    h1, h2, h3, p, span, label {
        color: #1e293b !important;
    }
    
    /* Tarjetas de resultados (métricas) con fondo claro para destacar */
    [data-testid="stMetric"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        padding: 15px !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
    }
    [data-testid="stMetricLabel"] {
        color: #475569 !important;
    }
    
    /* Estilo de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
        border-right: 1px solid #cbd5e1 !important;
    }
    [data-testid="stSidebar"] * {
        color: #334155 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Título Original Restaurado
st.title("📊 Optimizador de Producción Lineal Interactiva (MILP)")
st.write("Modificá los parámetros en la barra lateral para ver los resultados reflejados en tiempo real.")

# --- BARRA LATERAL: ENTRADA DE PARÁMETROS MODIFICABLES ---
st.sidebar.header("⚙️ Configuración de Parámetros")

# Coeficientes de la Función Objetivo (Ganancias)
st.sidebar.subheader("💰 Coeficientes de la Función Objetivo")
g_x = st.sidebar.number_input("Ganancia de Antena Grande ($)", min_value=0.0, value=150.0, step=10.0)
g_y = st.sidebar.number_input("Ganancia de Antena Mediana ($)", min_value=0.0, value=100.0, step=10.0)
g_z = st.sidebar.number_input("Ganancia de Antena Chica ($)", min_value=0.0, value=80.0, step=10.0)

# RESTRICCIÓN 1: Cantidad de Antenas
st.sidebar.subheader("📋 Cantidad de Antenas")
r1_x = st.sidebar.number_input("Coeficiente Antena Grande en Cantidad", value=1.0, key="r1x")
r1_y = st.sidebar.number_input("Coeficiente Antena Mediana en Cantidad", value=1.0, key="r1y")
r1_z = st.sidebar.number_input("Coeficiente Antena Chica en Cantidad", value=1.0, key="r1z")
lim_r1 = st.sidebar.number_input("Límite máximo Cantidad (≤)", min_value=1.0, value=15.0, step=1.0, key="r1lim")

# RESTRICCIÓN 2: Consumo de Watts
st.sidebar.subheader("📋 Consumo de Watts")
r2_x = st.sidebar.number_input("Coeficiente Antena Grande en Watts", value=20.0, key="r2x")
r2_y = st.sidebar.number_input("Coeficiente Antena Mediana en Watts", value=10.0, key="r2y")
r2_z = st.sidebar.number_input("Coeficiente Antena Chica en Watts", value=5.0, key="r2z")
lim_r2 = st.sidebar.number_input("Límite máximo Watts (≤)", min_value=1.0, value=200.0, step=10.0, key="r2lim")

# RESTRICCIÓN 3: Costo por Unidad
st.sidebar.subheader("📋 Costo por Unidad")
r3_x = st.sidebar.number_input("Coeficiente Antena Grande en Costo", value=500.0, key="r3x")
r3_y = st.sidebar.number_input("Coeficiente Antena Mediana en Costo", value=300.0, key="r3y")
r3_z = st.sidebar.number_input("Coeficiente Antena Chica en Costo", value=200.0, key="r3z")
lim_r3 = st.sidebar.number_input("Límite máximo Costo (≤)", min_value=1.0, value=5000.0, step=100.0, key="r3lim")

# Tipo de optimización (Entera o Continua)
st.sidebar.subheader("🔢 Tipo de Variables")
modo_resolucion = st.sidebar.selectbox(
    "Resolver el problema en:",
    options=["Números Enteros (Discretos)", "Números Continuos (Decimales)"]
)

if modo_resolucion == "Números Enteros (Discretos)":
    integridad = [1, 1, 1]
else:
    integridad = [0, 0, 0]


# --- CÁLCULO MATEMÁTICO EN EL BACKEND ---
c = [-g_x, -g_y, -g_z]
A = [[r1_x, r1_y, r1_z], [r2_x, r2_y, r2_z], [r3_x, r3_y, r3_z]]
bu = [lim_r1, lim_r2, lim_r3]
bl = [-np.inf, -np.inf, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([0.0, 0.0, 0.0], [np.inf, np.inf, np.inf])

res = milp(
    c=c,
    constraints=constraints,
    bounds=bounds,
    integrality=integridad
)


# --- DISPLAY PRINCIPAL: MOSTRAR RESULTADOS AL USUARIO ---
st.header("🎯 Resultados del Análisis de Optimización")

if res.success:
    st.success(f"**¡Optimización Exitosa!** Estado: {res.message}")
    
    col1, col2, col3, col4 = st.columns(4)
    es_entero = (modo_resolucion == "Números Enteros (Discretos)")
    
    with col1:
        val_x = int(round(res.x[0])) if es_entero else round(res.x[0], 2)
        st.metric(label="Óptimo Antena Grande", value=val_x)
    with col2:
        val_y = int(round(res.x[1])) if es_entero else round(res.x[1], 2)
        st.metric(label="Óptimo Antena Mediana", value=val_y)
    with col3:
        val_z = int(round(res.x[2])) if es_entero else round(res.x[2], 2)
        st.metric(label="Óptimo Antena Chica", value=val_z)
    with col4:
        st.metric(label="Ganancia Máxima Total (Z)", value=f"${-res.fun:,.2f}")
        
    st.subheader("📊 Monitoreo Dinámico de Restricciones")
    
    consumo_r1 = (res.x[0] * r1_x) + (res.x[1] * r1_y) + (res.x[2] * r1_z)
    consumo_r2 = (res.x[0] * r2_x) + (res.x[1] * r2_y) + (res.x[2] * r2_z)
    consumo_r3 = (res.x[0] * r3_x) + (res.x[1] * r3_y) + (res.x[2] * r3_z)
    
    datos_tabla = {
        "Restricción Analizada": ["Cantidad de Antenas", "Consumo de Watts", "Costo por Unidad"],
        "Descripción de la Fórmula": [
            f"{r1_x}(Grande) + {r1_y}(Mediana) + {r1_z}(Chica) ≤ {lim_r1}",
            f"{r2_x}(Grande) + {r2_y}(Mediana) + {r2_z}(Chica) ≤ {lim_r2}",
            f"{r3_x}(Grande) + {r3_y}(Mediana) + {r3_z}(Chica) ≤ {lim_r3}"
        ],
        "Capacidad Utilizada": [round(consumo_r1, 2), round(consumo_r2, 2), round(consumo_r3, 2)],
        "Límite Establecido": [lim_r1, lim_r2, lim_r3],
        "Sobrante (Holgura)": [round(lim_r1 - consumo_r1, 2), round(lim_r2 - consumo_r2, 2), round(lim_r3 - consumo_r3, 2)]
    }
    
    st.table(datos_tabla)
    
    with st.expander("Ver datos técnicos del vector de salida (res.x)"):
        st.code(f"Matriz de resultados crudos: {res.x}", language="python")

else:
    st.error(f"❌ No se encontró una solución óptima viable con las restricciones actuales. Motivo: {res.message}")
