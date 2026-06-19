import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. Configuración de la interfaz web
st.set_page_config(page_title="Optimizador de Antenas 3D", layout="wide", page_icon="📊")
st.title("📊 Optimizador de Producción de Antenas (MILP)")
st.write("Modificá los parámetros en la barra lateral para ver los resultados reflejados en tiempo real.")

# --- BARRA LATERAL: ENTRADA DE PARÁMETROS MODIFICABLES ---
st.sidebar.header("⚙️ Configuración de Parámetros")

# Valores de Ganancias
st.sidebar.subheader("💰 Ganancias por Tipo de Antena")
g_x = st.sidebar.number_input("Ganancia de Antena Grande ($)", min_value=0.0, value=150.0, step=1.0)
g_y = st.sidebar.number_input("Ganancia de Antena Mediana ($)", min_value=0.0, value=100.0, step=1.0)
g_z = st.sidebar.number_input("Ganancia de Antena Chica ($)", min_value=0.0, value=80.0, step=1.0)

# RESTRICCIÓN 1: Cantidad de Antenas
st.sidebar.subheader("📋 Cantidad de Antenas")
r1_x = st.sidebar.number_input("Antena Grande en Cantidad", value=1.0, step=1.0, key="r1x")
r1_y = st.sidebar.number_input("Antena Mediana en Cantidad", value=1.0, step=1.0, key="r1y")
r1_z = st.sidebar.number_input("Antena Chica en Cantidad", value=1.0, step=1.0, key="r1z")
lim_r1 = st.sidebar.number_input("Límite máximo Cantidad (≤)", min_value=1.0, value=15.0, step=1.0, key="r1lim")

# RESTRICCIÓN 2: Consumo de Watts
st.sidebar.subheader("📋 Consumo de Watts")
r2_x = st.sidebar.number_input("Antena Grande en Watts", value=20.0, step=1.0, key="r2x")
r2_y = st.sidebar.number_input("Antena Mediana en Watts", value=10.0, step=1.0, key="r2y")
r2_z = st.sidebar.number_input("Antena Chica en Watts", value=5.0, step=1.0, key="r2z")
lim_r2 = st.sidebar.number_input("Límite máximo Watts (≤)", min_value=1.0, value=200.0, step=1.0, key="r2lim")

# RESTRICCIÓN 3: Costo por Unidad
st.sidebar.subheader("📋 Costo por Unidad")
r3_x = st.sidebar.number_input("Antena Grande en Costo", value=500.0, step=1.0, key="r3x")
r3_y = st.sidebar.number_input("Antena Mediana en Costo", value=300.0, step=1.0, key="r3y")
r3_z = st.sidebar.number_input("Antena Chica en Costo", value=200.0, step=1.0, key="r3z")
lim_r3 = st.sidebar.number_input("Límite máximo Costo (≤)", min_value=1.0, value=5000.0, step=1.0, key="r3lim")

# Tipo de optimización (Entera o Continua)
st.sidebar.subheader("🔢 Tipo de Variables")
modo_resolucion = st.sidebar.selectbox(
    "Resolver el problema en:",
    options=["Números Enteros (Discretos)", "Números Continuos (Decimales)"]
)

# Determinación del vector de integridad de forma segura
if modo_resolucion == "Números Enteros (Discretos)":
    integridad = [1, 1, 1]
else:
    integridad = [0, 0, 0]


# --- CÁLCULO MATEMÁTICO EN EL BACKEND ---

# Coeficientes objetivos invertidos para maximizar con SciPy milp
c = [-g_x, -g_y, -g_z]

# Matriz A estructurada de forma segura en una sola línea plana
A = [[r1_x, r1_y, r1_z], [r2_x, r2_y, r2_z], [r3_x, r3_y, r3_z]]

# Cotas superiores e inferiores asignadas dinámicamente
bu = [lim_r1, lim_r2, lim_r3]
bl = [-np.inf, -np.inf, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([0.0, 0.0, 0.0], [np.inf, np.inf, np.inf])

# Ejecución del optimizador SciPy MILP
res = milp(
    c=c,
    constraints=constraints,
    bounds=bounds,
    integrality=integridad
)


# --- DISPLAY PRINCIPAL: MOSTRAR RESULTADOS AL USUARIO ---
st.header("🎯 Resultados del Análisis de Optimización")

if res.success:
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
    
    # Cálculo del consumo en tiempo real basado en los coeficientes ingresados
    consumo_r1 = (res.x[0] * r1_x) + (res.x[1] * r1_y) + (res.x[2] * r1_z)
    consumo_r2 = (res.x[0] * r2_x) + (res.x[1] * r2_y) + (res.x[2] * r2_z)
    consumo_r3 = (res.x[0] * r3_x) + (res.x[1] * r3_y) + (res.x[2] * r3_z)
    
    datos_tabla = {
        "Restricción Analizada": ["Cantidad de Antenas", "Consumo de Watts", "Costo por Unidad"],
        "Descripción de la Fórmula": [
            f"{int(r1_x)}(Grande) + {int(r1_y)}(Mediana) + {int(r1_z)}(Chica) ≤ {int(lim_r1)}",
            f"{int(r2_x)}(Grande) + {int(r2_y)}(Mediana) + {int(r2_z)}(Chica) ≤ {int(lim_r2)}",
            f"{int(r3_x)}(Grande) + {int(r3_y)}(Mediana) + {int(r3_z)}(Chica) ≤ {int(lim_r3)}"
        ],
        "Capacidad Utilizada": [round(consumo_r1, 2), round(consumo_r2, 2), round(consumo_r3, 2)],
        "Límite Establecido": [int(lim_r1), int(lim_r2), int(lim_r3)],
        "Sobrante (Holgura)": [round(lim_r1 - consumo_r1, 2), round(lim_r2 - consumo_r2, 2), round(lim_r3 - consumo_r3, 2)]
    }
    
    st.table(datos_tabla)
    
    with st.expander("Ver datos técnicos del vector de salida (res.x)"):
        st.code(f"Matriz de resultados crudos: {res.x}", language="python")

else:
    st.error(f"❌ No se encontró una solución óptima viable con las restricciones actuales. Motivo: {res.message}")

