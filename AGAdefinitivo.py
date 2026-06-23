import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
import io

# Intentamos importar reportlab para el PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    PDF_DISPONIBLE = True
except ImportError:
    PDF_DISPONIBLE = False

# 1. Configuración de la interfaz web
st.set_page_config(page_title="Optimizador de Antenas 3D", layout="wide", page_icon="📊")
st.title("📊 Optimizador y Calculador de Costes de Antenas")
st.write("Ingresá la superficie a cubrir y el presupuesto para calcular automáticamente la combinación óptima de antenas.")

if not PDF_DISPONIBLE:
    st.warning("⚠️ Para descargar presupuestos en PDF, debés instalar reportlab. Corré en tu consola: `pip install reportlab`")

# --- VALORES TÉCNICOS Y COMERCIALES FIJOS (No modificables por el usuario) ---
# Viáticos y Mano de Obra fijos
distancia_km = 25.0
costo_km = 15.0
horas_trabajo = 6.0
costo_hora = 50.0
trabajo_altura = False # Cambiar a True si por defecto se requiere

# Costes de Materiales Extra fijos
precio_cable_metro = 2.5
metros_cable_grande = 25.0
metros_cable_mediano = 15.0
metros_cable_chico = 10.0

# Coeficientes Técnicos Internos
g_x, g_y, g_z = 150.0, 100.0, 80.0       # Ganancia comercial
r1_x, r1_y, r1_z = 1.0, 1.0, 1.0          # Cantidad (unidades)
r2_x, r2_y, r2_z = 20.0, 10.0, 5.0        # Consumo de Watts
r3_x, r3_y, r3_z = 500.0, 300.0, 200.0    # Costo de Hardware Base por antena
soporte_x, soporte_y, soporte_z = 80.0, 50.0, 30.0 # Soportes fijos

# Rendimiento de Cobertura por Antena (m² que cubre cada una)
cober_x = 50.0  # Antena Grande cubre 50 m²
cober_y = 30.0  # Antena Mediana cubre 30 m²
cober_z = 15.0  # Antena Chica cubre 15 m²


# --- BARRA LATERAL: ENTRADA DE PARÁMETROS DEL USUARIO ---
st.sidebar.header("⚙️ Configuración del Proyecto")

# NUEVA SECCIÓN: Superficie requerida por el cliente
st.sidebar.subheader("📐 Área de Cobertura")
superficie_objetivo = st.sidebar.number_input("Superficie a cubrir (m²)", min_value=0.0, value=80.0, step=5.0)

# Límites Máximos Permitidos modificables
st.sidebar.subheader("⚠️ Restricciones del Sistema")
lim_r1 = st.sidebar.number_input("Límite máximo Cantidad Total de Antenas (≤)", min_value=1.0, value=15.0, step=1.0)
lim_r2 = st.sidebar.number_input("Límite máximo Consumo de Watts (≤)", min_value=1.0, value=200.0, step=1.0)
lim_r3 = st.sidebar.number_input("Presupuesto Máximo Base ($) (≤)", min_value=1.0, value=5000.0, step=1.0)

# Tipo de optimización (Entera o Continua)
modo_resolucion = st.sidebar.selectbox(
    "Resolver el problema en:",
    options=["Números Enteros (Discretos)", "Números Continuos (Decimales)"]
)
integridad = [1, 1, 1] if modo_resolucion == "Números Enteros (Discretos)" else [0, 0, 0]


# --- CÁLCULO MATEMÁTICO EN EL BACKEND (MILP) ---
# Vector de costos/ganancias (buscamos maximizar ganancia, por ende minimizamos el negativo)
c = [-g_x, -g_y, -g_z]

# Matriz de restricciones:
# Row 0: Cantidad total de antenas (≤ lim_r1)
# Row 1: Consumo total de Watts (≤ lim_r2)
# Row 2: Presupuesto base máximo (≤ lim_r3)
# Row 3: Cobertura de superficie (≥ superficie_objetivo) -> Se invierte multiplicando por -1 para mantener la estructura de límites superiores (≤)
A = [
    [r1_x, r1_y, r1_z],
    [r2_x, r2_y, r2_z],
    [r3_x, r3_y, r3_z],
    [-cober_x, -cober_y, -cober_z]
]

bu = [lim_r1, lim_r2, lim_r3, -superficie_objetivo]
bl = [-np.inf, -np.inf, -np.inf, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([0.0, 0.0, 0.0], [np.inf, np.inf, np.inf]) # El algoritmo decide las cantidades partiendo desde 0

res = milp(c=c, constraints=constraints, bounds=bounds, integrality=integridad)


# --- DISPLAY PRINCIPAL ---
st.header("🎯 Resultados del Análisis de Optimización")

if res.success:
    es_entero = (modo_resolucion == "Números Enteros (Discretos)")
    antenas_g = int(round(res.x[0])) if es_entero else round(res.x[0], 2)
    antenas_m = int(round(res.x[1])) if es_entero else round(res.x[1], 2)
    antenas_c = int(round(res.x[2])) if es_entero else round(res.x[2], 2)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Óptimo Antena Grande", value=antenas_g)
    with col2:
        st.metric(label="Óptimo Antena Mediana", value=antenas_m)
    with col3:
        st.metric(label="Óptimo Antena Chica", value=antenas_c)
    with col4:
        st.metric(label="Ganancia Máxima Estimada", value=f"${-res.fun:,.2f}")
        
    # --- PROCESAMIENTO UNIFICADO DE DATOS ---
    costo_hw_g, costo_hw_m, costo_hw_c = antenas_g * r3_x, antenas_m * r3_y, antenas_c * r3_z
    costo_hw_total = costo_hw_g + costo_hw_m + costo_hw_c
    
    costo_sop_g, costo_sop_m, costo_sop_c = antenas_g * soporte_x, antenas_m * soporte_y, antenas_c * soporte_z
    costo_soportes_total = costo_sop_g + costo_sop_m + costo_sop_c
    
    total_metros_g = antenas_g * metros_cable_grande
    total_metros_m = antenas_m * metros_cable_mediano
    total_metros_c = antenas_c * metros_cable_chico
    
    costo_cable_g = total_metros_g * precio_cable_metro
    costo_cable_m = total_metros_m * precio_cable_metro
    costo_cable_c = total_metros_c * precio_cable_metro
    costo_cable_total = costo_cable_g + costo_cable_m + costo_cable_c
    
    # Cálculos fijos de Mano de Obra y Viáticos
    costo_viaticos = distancia_km * costo_km
    mano_obra_base = horas_trabajo * costo_hora
    adicional_altura = (mano_obra_base * 0.35) if trabajo_altura else 0.0
    costo_mano_obra_total = mano_obra_base + adicional_altura
    
    costo_total_proyecto = costo_hw_total + costo_soportes_total + costo_cable_total + costo_viaticos + costo_mano_obra_total
    
    # Consumos reales calculados
    consumo_r1 = (res.x[0] * r1_x) + (res.x[1] * r1_y) + (res.x[2] * r1_z)
    consumo_r2 = (res.x[0] * r2_x) + (res.x[1] * r2_y) + (res.x[2] * r2_z)
    consumo_r3 = (res.x[0] * r3_x) + (res.x[1] * r3_y) + (res.x[2] * r3_z)
    superficie_lograda = (res.x[0] * cober_x) + (res.x[1] * cober_y) + (res.x[2] * cober_z)

    # Métricas resumidas en la interfaz superior
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Equipos e Infraestructura", f"${costo_hw_total + costo_soportes_total:,.2f}")
    with c2:
        st.metric("Total Materiales (Cables)", f"${costo_cable_total:,.2f}")
    with c3:
        st.metric("Total Mano de Obra y Viáticos", f"${costo_mano_obra_total + costo_viaticos:,.2f}")
    with c4:
        st.metric("COSTO TOTAL DEL PROYECTO", f"${costo_total_proyecto:,.2f}", delta=f"{round(superficie_lograda, 1)} m² cubiertos")

    # --- TABLA ÚNICA DE MONITOREO Y COSTES ---
    st.header("📋 Matriz Unificada: Desglose por Antena, Restricciones y Costes")
    
    tabla_maestra = {
        "Métricas y Parámetros": [
            "Cantidad de Antenas Asignadas (U)", 
            "Cobertura de Superficie (m²)",
            "Consumo Eléctrico (Watts)", 
            "Costo de Hardware Base ($)", 
            "Costo Estructuras / Soportes ($)", 
            "Costo Material Extra: Cableado ($)",
            "Mano de Obra + Viáticos Operativos ($)",
            "COSTO TOTAL CONSOLIDADO ($)"
        ],
        "Grande": [
            f"{antenas_g} U", 
            f"{antenas_g * cober_x} m² (Capac: {cober_x}m²)",
            f"{antenas_g * r2_x} W (Coef: {r2_x})", 
            f"${costo_hw_g:,.2f} (${r3_x}/u)", 
            f"${costo_sop_g:,.2f}", 
            f"${costo_cable_g:,.2f} ({int(total_metros_g)}m)", 
            "-", 
            "-"
        ],
        "Mediana": [
            f"{antenas_m} U", 
            f"{antenas_m * cober_y} m² (Capac: {cober_y}m²)",
            f"{antenas_m * r2_y} W (Coef: {r2_y})", 
            f"${costo_hw_m:,.2f} (${r3_y}/u)", 
            f"${costo_sop_m:,.2f}", 
            f"${costo_cable_m:,.2f} ({int(total_metros_m)}m)", 
            "-", 
            "-"
        ],
        "Chica": [
            f"{antenas_c} U", 
            f"{antenas_c * cober_z} m² (Capac: {cober_z}m²)",
            f"{antenas_c * r2_z} W (Coef: {r2_z})", 
            f"${costo_hw_c:,.2f} (${r3_z}/u)", 
            f"${costo_sop_c:,.2f}",  
            f"${costo_cable_c:,.2f} ({int(total_metros_c)}m)", 
            "-", 
            "-"
        ],
        "Límite / Parámetro Estático": [
            f"Máx: {int(lim_r1)} U", 
            f"Mínimo Requerido: {superficie_objetivo} m²",
            f"Máx: {int(lim_r2)} W", 
            f"Presupuesto Base ≤ ${int(lim_r3)}", 
            "Valores corporativos fijos", 
            f"Valor fijo: ${precio_cable_metro}/m", 
            f"Fijo: {horas_trabajo}hs, {distancia_km}km", 
            "Inversión final calculada"
        ],
        "Total Utilizado / Subtotal": [
            f"{round(consumo_r1, 2)} U (Holgura: {round(lim_r1 - consumo_r1, 2)})",
            f"{round(superficie_lograda, 2)} m² (Excedente: {round(superficie_lograda - superficie_objetivo, 2)} m²)",
            f"{round(consumo_r2, 2)} W (Holgura: {round(lim_r2 - consumo_r2, 2)})",
            f"${costo_hw_total:,.2f}",
            f"${costo_soportes_total:,.2f}",
            f"${costo_cable_total:,.2f}",
            f"${costo_mano_obra_total + costo_viaticos:,.2f}",
            f"${costo_total_proyecto:,.2f}"
        ]
    }
    st.table(tabla_maestra)
    
else:
    st.error("❌ No se encontró una solución óptima que cumpla con las restricciones actuales. Intentá aumentar el presupuesto base máximo o reducir los límites de Watts/Antenas.")
    
