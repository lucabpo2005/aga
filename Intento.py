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
st.write("Modificá la cantidad exacta de antenas a instalar y los parámetros comerciales para evaluar el escenario y generar presupuestos.")

if not PDF_DISPONIBLE:
    st.warning("⚠️ Para descargar presupuestos en PDF, debés instalar reportlab. Corré en tu consola: `pip install reportlab`")

# --- BARRA LATERAL: ENTRADA DE PARÁMETROS DEL USUARIO ---
st.sidebar.header("⚙️ Configuración de Parámetros")

# SECCIÓN 1: Cantidades deseadas
st.sidebar.subheader("📡 Cantidad de Antenas a Instalar")
cant_grande = st.sidebar.number_input("Cantidad de Antenas Grandes", min_value=0.0, value=5.0, step=1.0)
cant_mediana = st.sidebar.number_input("Cantidad de Antenas Medianas", min_value=0.0, value=5.0, step=1.0)
cant_chica = st.sidebar.number_input("Cantidad de Antenas Chicas", min_value=0.0, value=3.0, step=1.0)

# SECCIÓN 2: Costes Operativos y Viáticos
st.sidebar.subheader("🚚 Viáticos y Mano de Obra")
distancia_km = st.sidebar.number_input("Distancia al sitio (Km)", min_value=0.0, value=25.0, step=5.0)
costo_km = st.sidebar.number_input("Costo por Km de combustible ($)", min_value=0.0, value=15.0, step=1.0)
horas_trabajo = st.sidebar.number_input("Horas estimadas de trabajo", min_value=1.0, value=6.0, step=1.0)
costo_hora = st.sidebar.number_input("Precio por hora técnica ($)", min_value=0.0, value=50.0, step=5.0)
trabajo_altura = st.sidebar.checkbox("¿Requiere trabajo en altura/riesgo?", value=False)

# SECCIÓN 3: Cables específicos y Metraje por tipo de Antena (NUEVO)
st.sidebar.subheader("🔌 Configuración de Cables por Antena")

st.sidebar.markdown("**Antenas Grandes (Cable Blindado Pesado):**")
precio_cable_g = st.sidebar.number_input("Precio/m Cable Grande ($)", min_value=0.0, value=4.5, step=0.5)
metros_cable_g = st.sidebar.number_input("Metros por Antena Grande", min_value=1.0, value=25.0, step=1.0)

st.sidebar.markdown("**Antenas Medianas (Cable Coaxial RG11):**")
precio_cable_m = st.sidebar.number_input("Precio/m Cable Mediano ($)", min_value=0.0, value=3.0, step=0.5)
metros_cable_m = st.sidebar.number_input("Metros por Antena Mediana", min_value=1.0, value=15.0, step=1.0)

st.sidebar.markdown("**Antenas Chicas (Cable Coaxial RG6):**")
precio_cable_c = st.sidebar.number_input("Precio/m Cable Chico ($)", min_value=0.0, value=1.8, step=0.2)
metros_cable_c = st.sidebar.number_input("Metros por Antena Chica", min_value=1.0, value=10.0, step=1.0)

# Límites Máximos Permitidos
st.sidebar.subheader("⚠️ Disponibilidad Máxima (Límites)")
lim_r1 = st.sidebar.number_input("Límite máximo Cantidad Total de Antenas (≤)", min_value=1.0, value=15.0, step=1.0)
lim_r2 = st.sidebar.number_input("Límite máximo Consumo de Watts (≤)", min_value=1.0, value=200.0, step=1.0)
lim_r3 = st.sidebar.number_input("Presupuesto Máximo Base ($) (≤)", min_value=1.0, value=5000.0, step=1.0)

# Tipo de optimización
st.sidebar.subheader("🔢 Tipo de Variables")
modo_resolucion = st.sidebar.selectbox(
    "Resolver el problema en:",
    options=["Números Enteros (Discretos)", "Números Continuos (Decimales)"]
)

integridad = [1, 1, 1] if modo_resolucion == "Números Enteros (Discretos)" else [0, 0, 0]

# --- VALORES TÉCNICOS INTERNOS FIJOS ---
g_x, g_y, g_z = 150.0, 100.0, 80.0
r1_x, r1_y, r1_z = 1.0, 1.0, 1.0
r2_x, r2_y, r2_z = 20.0, 10.0, 5.0
r3_x, r3_y, r3_z = 500.0, 300.0, 200.0 

# Soportes específicos fijos por tipo de antena
soporte_x, soporte_y, soporte_z = 80.0, 50.0, 30.0

# --- CÁLCULO MATEMÁTICO EN EL BACKEND ---
c = [-g_x, -g_y, -g_z]
A = [[r1_x, r1_y, r1_z], [r2_x, r2_y, r2_z], [r3_x, r3_y, r3_z]]
bu = [lim_r1, lim_r2, lim_r3]
bl = [-np.inf, -np.inf, -np.inf]

constraints = LinearConstraint(A, bl, bu)
bounds = Bounds([cant_grande, cant_mediana, cant_chica], [cant_grande, cant_mediana, cant_chica])

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
        
    # --- NUEVO CUADRO FINANCIERO INTEGRAL DE SUMA DE DINERO ---
    st.header("💸 Cuadro de Desglose de Costes Comerciales")
    st.write("Suma totalizada y discriminada de hardware, infraestructura de soporte y operaciones.")

    # Cálculos detallados individuales de Hardware y Soportes
    hw_g = antenas_g * r3_x
    sop_g = antenas_g * soporte_x
    
    hw_m = antenas_m * r3_y
    sop_m = antenas_m * soporte_y
    
    hw_c = antenas_c * r3_z
    sop_c = antenas_c * soporte_z

    # Cálculos detallados de Cables por separado
    metraje_g = antenas_g * metros_cable_g
    costo_cab_g = metraje_g * precio_cable_g

    metraje_m = antenas_m * metros_cable_m
    costo_cab_m = metraje_m * precio_cable_m

    metraje_c = antenas_c * metros_cable_c
    costo_cab_c = metraje_c * precio_cable_c
    
    costo_cable_total = costo_cab_g + costo_cab_m + costo_cab_c

    # Mano de obra, altura y viáticos
    costo_viaticos = distancia_km * costo_km
    mano_obra_base = horas_trabajo * costo_hora
    adicional_altura = (mano_obra_base * 0.35) if trabajo_altura else 0.0
    costo_mano_obra_total = mano_obra_base + adicional_altura

    # Costo final absoluto
    costo_total_proyecto = (hw_g + sop_g + hw_m + sop_m + hw_c + sop_c + 
                            costo_cable_total + costo_viaticos + costo_mano_obra_total)

    # Construcción de la tabla de dinero centralizada
    tabla_financiera = {
        "Categoría de Coste": [
            "Antenas Grandes (Hardware Base)", "Antenas Grandes (Soportes)",
            "Antenas Medianas (Hardware Base)", "Antenas Medianas (Soportes)",
            "Antenas Chicas (Hardware Base)", "Antenas Chicas (Soportes)",
            "Subtotal Infraestructura y Cables", "Logística y Traslados (Viáticos)",
            "Mano de Obra Técnica Especializada", "COSTO TOTAL INTEGRAL"
        ],
        "Detalle Operativo": [
            f"{antenas_g} unidades x ${r3_x:,.2f}", f"{antenas_g} unidades x ${soporte_x:,.2f}",
            f"{antenas_m} unidades x ${r3_y:,.2f}", f"{antenas_m} unidades x ${soporte_y:,.2f}",
            f"{antenas_c} unidades x ${r3_z:,.2f}", f"{antenas_c} unidades x ${soporte_z:,.2f}",
            "Suma total de equipos + cables de conexión", f"{distancia_km} Km recorridos x ${costo_km:,.2f}/Km",
            f"{horas_trabajo} hs laborables (Plus altura del 35%: {'SÍ' if trabajo_altura else 'NO'})",
            "Inversión final requerida para el cliente"
        ],
        "Monto ($)": [
            f"${hw_g:,.2f}", f"${sop_g:,.2f}",
            f"${hw_m:,.2f}", f"${sop_m:,.2f}",
            f"${hw_c:,.2f}", f"${sop_c:,.2f}",
            f"${(hw_g+sop_g+hw_m+sop_m+hw_c+sop_c+costo_cable_total):,.2f}", f"${costo_viaticos:,.2f}",
            f"${costo_mano_obra_total:,.2f}", f"${costo_total_proyecto:,.2f}"
        ]
    }
    st.table(tabla_financiera)

    # --- SECCIÓN INFERIOR EN COLUMNAS: DETALLE DE CABLEADO (NUEVO) ---
    st.subheader("🔌 Desglose Técnico de Cables Utilizados")
    st.write("Filtro detallado de metrajes y costes específicos según el grosor y tipo de antena instalada:")
    
    col_g, col_m, col_c = st.columns(3)
    
    with col_g:
        st.markdown("### 🔴 Cable Blindado Pesado")
        st.caption("Destinado a Antenas Grandes")
        st.metric(label="Metros Requeridos", value=f"{metraje_g:.1f} m")
        st.metric(label="Costo de Cable Grande", value=f"${costo_cab_g:,.2f}", delta=f"${precio_cable_g:.2f} por metro")
        
    with col_m:
        st.markdown("### 🟡 Cable Coaxial RG11")
        st.caption("Destinado a Antenas Medianas")
        st.metric(label="Metros Requeridos", value=f"{metraje_m:.1f} m")
        st.metric(label="Costo de Cable Mediano", value=f"${costo_cab_m:,.2f}", delta=f"${precio_cable_m:.2f} por metro")
        
    with col_c:
        st.markdown("### 🟢 Cable Coaxial RG6")
        st.caption("Destinado a Antenas Chicas")
        st.metric(label="Metros Requeridos", value=f"{metraje_c:.1f} m")
        st.metric(label="Costo de Cable Chico", value=f"${costo_cab_c:,.2f}", delta=f"${precio_cable_c:.2f} por metro")

    # --- MONITOREO DINÁMICO DE RESTRICCIONES ---
    st.subheader("📊 Monitoreo Dinámico de Restricciones Técnicas")
    consumo_r1 = (res.x[0] * r1_x) + (res.x[1] * r1_y) + (res.x[2] * r1_z)
    consumo_r2 = (res.x[0] * r2_x) + (res.x[1] * r2_y) + (res.x[2] * r2_z)
    consumo_r3 = (res.x[0] * r3_x) + (res.x[1] * r3_y) + (res.x[2] * r3_z)
    
    datos_tabla = {
        "Restricción Analizada": ["Cantidad de Antenas", "Consumo de Watts", "Costo Base Hardware"],
        "Descripción de la Fórmula": [
            f"1(Grande) + 1(Mediana) + 1(Chica) ≤ {int(lim_r1)}"
