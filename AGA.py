import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. Configuración de la interfaz web
st.set_page_config(page_title="Optimizador MILP Genérico", layout="wide", page_icon="📊")
st.title("🧮 Optimizador de Programación Lineal Interactivo (MILP)")
st.write("Configurá libremente la función objetivo y todas las restricciones en la barra lateral.")

# --- BARRA LATERAL: PERSONALIZACIÓN TOTAL DEL PROBLEMA ---
st.sidebar.header("⚙️ 1. Configuración de Variables")

# Nombres personalizados para que el usuario sepa qué está optimizando
nombre_x = st.sidebar.text_input("Nombre de la Variable X", "Producto X")
nombre_y = st.sidebar.text_input("Nombre de la Variable Y", "Producto Y")
nombre_z = st.sidebar.text_input("Nombre de la Variable Z", "Producto Z")

# Coeficientes de la Función Objetivo (Ganancias)
st.sidebar.subheader("💰 2. Coeficientes de Ganancia (Maximizar Z)")
g_x = st.sidebar.number_input(f"Ganancia unitaria de {nombre_x} ($)", value=150.0)
g_y = st.sidebar.number_input(f"Ganancia unitaria de {nombre_y} ($)", value=100.0)
g_z = st.sidebar.number_input(f"Ganancia unitaria de {nombre_z} ($)", value=80.0)

# RESTRICCIÓN 1 INTERACTIVA
st.sidebar.subheader("📋 3. Restricción Nº 1")
r1_x = st.sidebar.number_input(f"Coeficiente X en R1", value=1.0, key="r1x")
r1_y = st.sidebar.number_input(f"Coeficiente Y en R1", value=1.0, key="r1y")
r1_z = st.sidebar.number_input(f"Coeficiente Z en R1", value=1.0, key="r1z")
lim_r1 = st.sidebar.number_input("Límite máximo R1 (≤)", value=15.0, key="r1lim")

# RESTRICCIÓN 2 INTERACTIVA
st.sidebar.subheader("📋 4. Restricción Nº 2")
r2_x = st.sidebar.number_input(f"Coeficiente X en R2", value=20.0, key="r2x")
r2_y = st.sidebar.number_input(f"Coeficiente Y en R2", value=10.0, key="r2y")
r2_z = st.sidebar.number_input(f"Coeficiente Z en R2", value=5.0, key="r2z")
lim_r2 = st.sidebar.number_input("Límite máximo R2 (≤)", value=200.0, key="r2lim")

# RESTRICCIÓN 3 INTERACTIVA
st.sidebar.subheader("📋 5. Restricción Nº 3")
r3_x = st.sidebar.number_input(f"Coeficiente X en R3", value=500.0, key="r3x")
r3_y = st.sidebar.number_input(f"Coeficiente Y en R3", value=300.0, key="r3y")
r3_z = st.sidebar.number_input(f"Coeficiente Z en R3", value=200.0, key="r3z")
lim_r3 = st.sidebar.number_input("Límite máximo R3 (≤)", value=5000.0, key="r3lim")

# Tipo de optimización (Entera o Continua)
st.sidebar.subheader("🔢 6. Tipo de Variables")
modo_resolucion = st.sidebar.selectbox(
    "Resolver el problema en:",
    options=["Números Enteros (Discretos)", "Números Continuos (Decimales)"]
)

if modo_resolucion == "Números Enteros (Discretos)":
    integridad = [1, 1, 1]
else:
    integridad = [0, 0, 0]


# --- CÁLCULO MATEMÁTICO DINÁMICO EN EL BACKEND ---

# Coeficientes objetivos invertidos para maximizar con SciPy milp
c = [-g_x, -g_y, -g_z]

# Matriz A armada dinámicamente con los inputs del usuario en una sola línea plana
A = [[r1_x, r1_y, r1_z], [r2_x, r2_y, r2_z], [r3_x, r3_y, r3_z]]

# Cotas superiores e inferiores asignadas dinámicamente
bu = [lim_r1, lim_r2, lim_r3]
bl = [-np.inf, -np.inf, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([0, 0, 0], [np.inf, np.inf, np.inf])

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
    st.success(f"**¡Optimización Exitosa!** Estado: {res.message}")
    
    col1, col2, col3, col4 = st.columns(4)
    es_entero = (modo_resolucion == "Números Enteros (Discretos)")
    
    with col1:
        val_x = int(round(res.x[0])) if es_entero else round(res.x[0], 2)
        st.metric(label=f"Óptimo de {nombre_x}", value=val_x)
    with col2:
        val_y = int(round(res.x[1])) if es_entero else round(res.x[1], 2)
        st.metric(label=f"Óptimo de {nombre_y}", value=val_y)
    with col3:
        val_z = int(round(res.x[2])) if es_entero else round(res.x[2], 2)
        st.metric(label=f"Óptimo de {nombre_z}", value=val_z)
    with col4:
        st.metric(label="Ganancia Máxima Total (Z)", value=f"${-res.fun:,.2f}")
        
    st.subheader("📊 Monitoreo Dinámico de Restricciones")
    
    # Cálculo del consumo en tiempo real basado en lo que ingresó el usuario
    consumo_r1 = (res.x[0] * r1_x) + (res.x[1] * r1_y) + (res.x[2] * r1_z)
    consumo_r2 = (res.x[0] * r2_x) + (res.x[1] * r2_y) + (res.x[2] * r2_z)
    consumo_r3 = (res.x[0] * r3_x) + (res.x[1] * r3_y) + (res.x[2] * r3_z)
    
    datos_tabla = {
        "Restricción Analizada": ["Restricción Nº 1", "Restricción Nº 2", "Restricción Nº 3"],
        "Fórmula Aplicada": [
            f"{r1_x}x + {r1_y}y + {r1_z}z ≤ {lim_r1}",
            f"{r2_x}x + {r2_y}y + {r2_z}z ≤ {lim_r2}",
            f"{r3_x}x + {r3_y}y + {r3_z}z ≤ {lim_r3}"
        ],
        "Capacidad Utilizada": [round(consumo_r1, 2), round(consumo_r2, 2), round(consumo_r3, 2)],
        "Límite Establecido": [lim_r1, lim_r2, lim_r3],
        "Sobrante (Holgura)": [round(lim_r1 - consumo_r1, 2), round(lim_r2 - consumo_r2, 2), round(lim_r3 - consumo_r3, 2)]
    }
    
    st.table(datos_tabla)
    
    with st.expander("Ver detalles técnicos del vector de salida (res.x)"):
        st.code(f"Matriz de resultados crudos: {res.x}", language="python")

else:
    st.error(f"❌ No se encontró una solución óptima viable con las restricciones actuales. Motivo: {res.message}")
