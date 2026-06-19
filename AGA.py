import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. Configuración de la interfaz web
st.set_page_config(page_title="Optimizador de Antenas 3D", layout="wide", page_icon="📊")

# Título de la aplicación
st.title("📊 Optimizador de Producción Lineal Interactiva (MILP)")
st.write("Modificá las ganancias y las disponibilidades máximas en la barra lateral para recalcular.")

# --- BARRA LATERAL: INTERFAZ SIMPLIFICADA PARA EL USUARIO ---
st.sidebar.header("⚙️ Configuración de Parámetros")

# Valores de ganancia modificables por el usuario
st.sidebar.subheader("💰 Ganancias por Tipo de Antena")
g_x = st.sidebar.number_input("Ganancia de Antena Grande ($)", min_value=0.0, value=150.0, step=10.0)
g_y = st.sidebar.number_input("Ganancia de Antena Mediana ($)", min_value=0.0, value=100.0, step=10.0)
g_z = st.sidebar.number_input("Ganancia de Antena Chica ($)", min_value=0.0, value=80.0, step=10.0)

# Límites de las Restricciones (El usuario SOLO modifica el tope máximo disponible)
st.sidebar.subheader("⚠️ Disponibilidad Máxima (Límites)")
lim_r1 = st.sidebar.number_input("Límite máximo Cantidad de Antenas (≤)", min_value=1.0, value=15.0, step=1.0)
lim_r2 = st.sidebar.number_input("Límite máximo Consumo de Watts (≤)", min_value=1.0, value=200.0, step=10.0)
lim_r3 = st.sidebar.number_input("Límite máximo Costo por Unidad ($) (≤)", min_value=1.0, value=5000.0, step=100.0)

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


# --- CÁLCULO MATEMÁTICO EN EL BACKEND (VALORES INTERNOS FIJOS) ---
c = [-g_x, -g_y, -g_z]

# Valores técnicos internos protegidos contra modificaciones accidentales
r1_x, r1_y, r1_z = 1.0, 1.0, 1.0       # Cantidad de Antenas (1x + 1y + 1z)
r2_x, r2_y, r2_z = 20.0, 10.0, 5.0     # Consumo de Watts (20x + 10y + 5z)
r3_x, r3_y, r3_z = 500.0, 300.0, 200.0 # Costo por Unidad (500x + 300y + 200z)

# Matriz A estructurada de forma fija
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
            f"1(Grande) + 1(Mediana) + 1(Chica) ≤ {lim_r1}",
            f"20(Grande) + 10(Mediana) + 5(Chica) ≤ {lim_r2}",
            f"500(Grande) + 300(Mediana) + 200(Chica) ≤ {lim_r3}"
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

