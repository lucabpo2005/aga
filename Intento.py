import streamlit as st
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
import io

# Intentamos importar reportlab para el PDF. Si no está, la app avisa al usuario.
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

# SECCIÓN 1: Cantidades deseadas (Configuradas con valor inicial en 0.0)
st.sidebar.subheader("📡 Cantidad de Antenas a Instalar")
cant_grande = st.sidebar.number_input("Cantidad de Antenas Grandes", min_value=0.0, value=0.0, step=1.0)
cant_mediana = st.sidebar.number_input("Cantidad de Antenas Medianas", min_value=0.0, value=0.0, step=1.0)
cant_chica = st.sidebar.number_input("Cantidad de Antenas Chicas", min_value=0.0, value=0.0, step=1.0)

# SECCIÓN 2: Costes Operativos, Materiales y Viáticos
st.sidebar.subheader("🚚 Viáticos y Mano de Obra")
distancia_km = st.sidebar.number_input("Distancia al sitio (Km)", min_value=0.0, value=0.0, step=5.0)
costo_km = st.sidebar.number_input("Costo por Km de combustible ($)", min_value=0.0, value=0.0, step=1.0)
horas_trabajo = st.sidebar.number_input("Horas estimadas de trabajo", min_value=0.0, value=0.0, step=1.0)
costo_hora = st.sidebar.number_input("Precio por hora técnica ($)", min_value=0.0, value=0.0, step=5.0)
trabajo_altura = st.sidebar.checkbox("¿Requiere trabajo en altura/riesgo?", value=False)

st.sidebar.subheader("🔌 Costes de Materiales Extra")
precio_cable_metro = st.sidebar.number_input("Precio por metro de cable ($)", min_value=0.0, value=0.0, step=0.5)
# Metros requeridos por tipo de antena y cable específico inicializados en 0.0
metros_cable_grande = st.sidebar.number_input("Metros de cable GRANDE por antena", min_value=0.0, value=0.0, step=1.0)
metros_cable_mediano = st.sidebar.number_input("Metros de cable MEDIANO por antena", min_value=0.0, value=0.0, step=1.0)
metros_cable_chico = st.sidebar.number_input("Metros de cable CHICO por antena", min_value=0.0, value=0.0, step=1.0)

# Límites Máximos Permitidos
st.sidebar.subheader("⚠️ Disponibilidad Máxima (Límites)")
lim_r1 = st.sidebar.number_input("Límite máximo Cantidad Total de Antenas (≤)", min_value=1.0, value=15.0, step=1.0)
lim_r2 = st.sidebar.number_input("Límite máximo Consumo de Watts (≤)", min_value=1.0, value=200.0, step=1.0)
lim_r3 = st.sidebar.number_input("Presupuesto Máximo Base ($) (≤)", min_value=1.0, value=5000.0, step=1.0)

# Tipo de optimización (Entera o Continua)
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
r3_x, r3_y, r3_z = 500.0, 300.0, 200.0 # Coste base de hardware por tipo de antena

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
        
    # --- PROCESAMIENTO UNIFICADO DE DATOS (Mano de Obra y Totales) ---
    costo_hw_g, costo_hw_m, costo_hw_c = antenas_g * r3_x, antenas_m * r3_y, antenas_c * r3_z
    costo_hw_total = costo_hw_g + costo_hw_m + costo_hw_c
    
    costo_sop_g, costo_sop_m, costo_sop_c = antenas_g * soporte_x, antenas_m * soporte_y, antenas_c * soporte_z
    costo_soportes_total = costo_sop_g + costo_sop_m + costo_sop_c
    
    # Cálculo dinámico de metros y costos individuales por cada tipo de cable asignado
    total_metros_g = antenas_g * metros_cable_grande
    total_metros_m = antenas_m * metros_cable_mediano
    total_metros_c = antenas_c * metros_cable_chico
    
    costo_cable_g = total_metros_g * precio_cable_metro
    costo_cable_m = total_metros_m * precio_cable_metro
    costo_cable_c = total_metros_c * precio_cable_metro
    
    costo_cable_total = costo_cable_g + costo_cable_m + costo_cable_c
    total_metros_combinados = total_metros_g + total_metros_m + total_metros_c
    
    costo_viaticos = distancia_km * costo_km
    mano_obra_base = horas_trabajo * costo_hora
    adicional_altura = (mano_obra_base * 0.35) if trabajo_altura else 0.0
    costo_mano_obra_total = mano_obra_base + adicional_altura
    
    costo_total_proyecto = costo_hw_total + costo_soportes_total + costo_cable_total + costo_viaticos + costo_mano_obra_total
    
    consumo_r1 = (res.x[0] * r1_x) + (res.x[1] * r1_y) + (res.x[2] * r1_z)
    consumo_r2 = (res.x[0] * r2_x) + (res.x[1] * r2_y) + (res.x[2] * r2_z)
    consumo_r3 = (res.x[0] * r3_x) + (res.x[1] * r3_y) + (res.x[2] * r3_z)

    # Métricas resumidas en la interfaz superior
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Equipos e Infraestructura", f"${costo_hw_total + costo_soportes_total:,.2f}")
    with c2:
        st.metric("Total Materiales (Cables)", f"${costo_cable_total:,.2f}")
    with c3:
        st.metric("Total Mano de Obra (+Riesgo)", f"${costo_mano_obra_total:,.2f}")
    with c4:
        st.metric("COSTO TOTAL DEL PROYECTO", f"${costo_total_proyecto:,.2f}", delta="Inversión requerida")

    # --- TABLA ÚNICA DE MONITOREO Y COSTES ---
    st.header("📋 Matriz Unificada: Desglose por Antena, Restricciones y Costes")
    
    tabla_maestra = {
        "Antenas a Eleccion": [
            "Cantidad de Antenas (U)", 
            "Consumo Eléctrico (Watts)", 
            "Costo de Hardware Base ($)", 
            "Costo Estructuras / Soportes ($)", 
            "Costo Material Extra: Cableado ($)",
            "Mano de Obra + Viáticos Operativos ($)",
            "COSTO TOTAL CONSOLIDADO ($)"
        ],
        "Grande": [
            f"{antenas_g} (Límite: {r1_x})", 
            f"{antenas_g * r2_x} W (Coef: {r2_x})", 
            f"${costo_hw_g:,.2f}", 
            f"${costo_sop_g:,.2f}", 
            f"${costo_cable_g:,.2f} (Cable G: {int(total_metros_g)}m)", 
            "-", 
            "-"
        ],
        "Mediana": [
            f"{antenas_m} (Límite: {r1_y})", 
            f"{antenas_m * r2_y} W (Coef: {r2_y})", 
            f"${costo_hw_m:,.2f}", 
            f"${costo_sop_m:,.2f}", 
            f"${costo_cable_m:,.2f} (Cable M: {int(total_metros_m)}m)", 
            "-", 
            "-"
        ],
        "Chica": [
            f"{antenas_c} (Límite: {r1_z})", 
            f"{antenas_c * r2_z} W (Coef: {r2_z})", 
            f"${costo_hw_c:,.2f}", 
            f"${costo_sop_c:,.2f}",  
            f"${costo_cable_c:,.2f} (Cable C: {int(total_metros_c)}m)", 
            "-", 
            "-"
        ],
        "Límite / Parámetro Comercial": [
            f"Máx: {int(lim_r1)} U", 
            f"Máx: {int(lim_r2)} W", 
            f"Presupuesto Base ≤ ${int(lim_r3)}", 
            "Especificaciones fijas", 
            f"Valor de referencia: ${precio_cable_metro}/m", 
            f"{horas_trabajo}hs, {distancia_km}km (+35% Altura si aplica)", 
            "Suma total del proyecto"
        ],
        "Total Utilizado / Subtotal": [
            f"{round(consumo_r1, 2)} U (Holgura: {round(lim_r1 - consumo_r1, 2)})",
            f"{round(consumo_r2, 2)} W (Holgura: {round(lim_r2 - consumo_r2, 2)})",
            f"${costo_hw_total:,.2f}",
            f"${costo_soportes_total:,.2f}",
            f"${costo_cable_total:,.2f}",
            f"${costo_mano_obra_total + costo_viaticos:,.2f}",
            f"${costo_total_proyecto:,.2f}"
        ]
    }
    st.table(tabla_maestra)
    
    # --- MÓDULO EXPORTAR PDF ---
    st.subheader("📄 Generación de Presupuesto Profesional")
    
    if PDF_DISPONIBLE:
        def generar_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=40, bottomMargin=40)
            story = []
            
            styles = getSampleStyleSheet()
