import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. Configuración de la interfaz web
st.set_page_config(page_title="Optimizador de Producción 3D", layout="wide", page_icon="📊")
st.title("📊 Optimizador de Producción Lineal Interactiva (MILP)")
st.write("Modificá los parámetros en la barra lateral para ver los resultados reflejados en tiempo real.")

# --- BARRA LATERAL: ENTRADA DE PARÁMETROS MODIFICABLES ---
st.sidebar.header("⚙️ Configuración de Parámetros")

# Coeficientes de la Función Objetivo (Ganancias)
st.sidebar.subheader("💰 Coeficientes de la Función Objetivo")
g_x = st.sidebar.number_input("Ganancia de x ($)", min_value=0, value=150, step=10)
g_y = st.sidebar.number_input("Ganancia de y ($)", min_value=0, value=100, step=10)
g_z = st.sidebar.number_input("Ganancia de z ($)", min_value=0, value=80, step=10)

# Límites de las Restricciones (Cotas Superiores)
st.sidebar.subheader("⚠️ Disponibilidad Máxima (Límites)")
lim_r1 = st.sidebar.number_input("Límite Restricción 1 (x + y + z ≤ L1)", min_value=1, value=15, step=1)
lim_r2 = st.sidebar.number_input("Límite Restricción 2 (20x + 10y + 5z ≤ L2)", min_value=1, value=200, step=10)
lim_r3 = st.sidebar.number_input("Límite Restricción 3 (500x + 300y + 200z ≤ L3)", min_value=1, value=5000, step=100)

# Tipo de optimización (Entera o Continua)
st.sidebar.subheader("🔢 Tipo de Variables")
modo_resolucion = st.sidebar.selectbox(
    "Resolver el problema en:",
    options=["Números Enteros (Discretos)", "Números Continuos (Decimales)"]
)

# Estructuración lineal para evitar errores de renderizado
if modo_resolucion == "Números Enteros (Discretos)":
    integridad = [1, 1, 1]
else:
    integridad = [0, 0, 0]


# --- CÁLCULO MATEMÁTICO EN EL BACKEND ---

# Coeficientes objetivos invertidos para maximizar
c = [-g_x, -g_y, -g_z]

# Matriz A escrita de manera horizontal continua para forzar la visibilidad de los números
A = [[1, 1, 1], [20, 10, 5], [500, 300, 200]]

# Cotas superiores e inferiores (-np.inf para restricciones de tipo <=)
bu = [lim_r1, lim_r2, lim_r3]
bl = [-np.inf, -np.inf, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([0, 0, 0], [np.inf, np.inf, np.inf])

# Ejecución del optimizador SciPy
res = milp(
    c=c,
    constraints=constraints,
    bounds=bounds,
    integrality=integridad
)


# --- DISPLAY PRINCIPAL: MOSTRAR RESULTADOS AL USUARIO ---
st.header("🎯 Resultados del Análisis")

if res.success:
    st.success(f"**¡Optimización Exitosa!** Estado: {res.message}")
    
    col1, col2, col3, col4 = st.columns(4)
    es_entero = (modo_resolucion == "Números Enteros (Discretos)")
    
    with col1:
        val_x = int(round(res.x[0])) if es_entero else round(res.x[0], 2)
        st.metric(label="Valor óptimo de x", value=val_x)
    with col2:
        val_y = int(round(res.x[1])) if es_entero else round(res.x[1], 2)
        st.metric(label="Valor óptimo de y", value=val_y)
    with col3:
        val_z = int(round(res.x[2])) if es_entero else round(res.x[2], 2)
        st.metric(label="Valor óptimo de z", value=val_z)
    with col4:
        st.metric(label="Ganancia Máxima Total (F)", value=f"${-res.fun:,.2f}")
        
    st.subheader("📊 Monitoreo de Restricciones y Recursos")
    
    consumo_r1 = (res.x[0] * 1) + (res.x[1] * 1) + (res.x[2] * 1)
    consumo_r2 = (res.x[0] * 20) + (res.x[1] * 10) + (res.x[2] * 5)
    consumo_r3 = (res.x[0] * 500) + (res.x[1] * 300) + (res.x[2] * 200)
    
    datos_tabla = {
        "Ecuación de la Restricción": ["1x + 1y + 1z ≤ Límite 1", "20x + 10y + 5z ≤ Límite 2", "500x + 300y + 200z ≤ Límite 3"],
        "Capacidad Utilizada": [round(consumo_r1, 2), round(consumo_r2, 2), round(consumo_r3, 2)],
        "Límite Máximo Permitido": [lim_r1, lim_r2, lim_r3],
        "Holgura (Sobrante)": [round(lim_r1 - consumo_r1, 2), round(lim_r2 - consumo_r2, 2), round(lim_r3 - consumo_r3, 2)]
    }
    
    st.table(datos_tabla)
    
    with st.expander("Ver datos técnicos del vector de salida (res.x)"):
        st.code(f"Matriz de resultados crudos: {res.x}", language="python")

else:
    st.error(f"❌ No se encontró una solución óptima viable con las restricciones actuales. Motivo: {res.message}")
