import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. Configuración de la interfaz web
st.set_page_config(page_title="Optimizador de Antenas 3D", layout="wide", page_icon="📊")
st.title("📊 Optimizador de Producción de Antenas (MILP)")
st.write("Modificá la cantidad de antenas deseadas, el límite máximo y el presupuesto en la barra lateral para recalcular.")

# --- BARRA LATERAL: ENTRADA DE PARÁMETROS PERMITIDOS PARA EL USUARIO ---
st.sidebar.header("⚙️ Configuración de Parámetros")

# NUEVA SECCIÓN: Cupos mínimos de antenas que desea utilizar el usuario
st.sidebar.subheader("📡 Cantidad de Antenas Requeridas (Mínimos)")
min_grande = st.sidebar.number_input("Mínimo de Antenas Grandes", min_value=0.0, value=0.0, step=1.0)
min_mediana = st.sidebar.number_input("Mínimo de Antenas Medianas", min_value=0.0, value=0.0, step=1.0)
min_chica = st.sidebar.number_input("Mínimo de Antenas Chicas", min_value=0.0, value=0.0, step=1.0)

# Límites Permitidos (Cantidad máxima total y presupuesto)
st.sidebar.subheader("⚠️ Disponibilidad Máxima (Límites)")
lim_r1 = st.sidebar.number_input("Límite máximo Cantidad Total de Antenas (≤)", min_value=1.0, value=15.0, step=1.0)
lim_r3 = st.sidebar.number_input("Presupuesto Máximo para Gastar ($) (≤)", min_value=1.0, value=5000.0, step=1.0)

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


# --- VALORES TÉCNICOS INTERNOS FIJOS Y PROTEGIDOS ---
g_x, g_y, g_z = 150.0, 100.0, 80.0
r1_x, r1_y, r1_z = 1.0, 1.0, 1.0
r2_x, r2_y, r2_z = 20.0, 10.0, 5.0
lim_r2 = 200.0
r3_x, r3_y, r3_z = 500.0, 300.0, 200.0


# --- CÁLCULO MATEMÁTICO EN EL BACKEND ---

# Coeficientes objetivos invertidos para maximizar con SciPy milp
c = [-g_x, -g_y, -g_z]

# Matriz A estructurada de forma fija y segura
A = [[r1_x, r1_y, r1_z], [r2_x, r2_y, r2_z], [r3_x, r3_y, r3_z]]

# Cotas superiores e inferiores de las restricciones principales
bu = [lim_r1, lim_r2, lim_r3]
bl = [-np.inf, -np.inf, -np.inf]

constraints = LinearConstraint(A, bl, bu)

# MODIFICACIÓN CRÍTICA: Se inyectan las cantidades deseadas como límites inferiores de las variables [0.0, 0.0, 0.0]
bounds = Bounds([min_grande, min_mediana, min_chica], [np.inf, np.inf, np.inf])

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
    
    # Cálculo del consumo en tiempo real basado en el vector óptimo res.x
    consumo_r1 = (res.x[0] * r1_x) + (res.x[1] * r1_y) + (res.x[2] * r1_z)
    consumo_r2 = (res.x[0] * r2_x) + (res.x[1] * r2_y) + (res.x[2] * r2_z)
    consumo_r3 = (res.x[0] * r3_x) + (res.x[1] * r3_y) + (res.x[2] * r3_z)
    
    datos_tabla = {
        "Restricción Analizada": ["Cantidad de Antenas", "Consumo de Watts", "Costo por Unidad"],
        "Descripción de la Fórmula": [
            f"1(Grande) + 1(Mediana) + 1(Chica) ≤ {int(lim_r1)}",
            f"20(Grande) + 10(Mediana) + 5(Chica) ≤ {int(lim_r2)}",
            f"500(Grande) + 300(Mediana) + 200(Chica) ≤ {int(lim_r3)}"
        ],
        "Capacidad Utilizada": [round(consumo_r1, 2), round(consumo_r2, 2), round(consumo_r3, 2)],
        "Límite Establecido": [int(lim_r1), int(lim_r2), int(lim_r3)],
        "Sobrante (Holgura)": [round(lim_r1 - consumo_r1, 2), round(lim_r2 - consumo_r2, 2), round(lim_r3 - consumo_r3, 2)]
    }
    
    st.table(datos_tabla)
    
    with st.expander("Ver datos técnicos del vector de salida (res.x)"):
        st.code(f"Matriz de resultados crudos: {res.x}", language="python")

else:
    st.error(f"❌ No se encontró una solución óptima viable. Es posible que las cantidades mínimas ingresadas superen el presupuesto o el límite de antenas disponible. Motivo: {res.message}")
