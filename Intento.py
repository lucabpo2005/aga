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

# SECCIÓN 1: Cantidades deseadas
st.sidebar.subheader("📡 Cantidad de Antenas a Instalar")
cant_grande = st.sidebar.number_input("Cantidad de Antenas Grandes", min_value=0.0, value=5.0, step=1.0)
cant_mediana = st.sidebar.number_input("Cantidad de Antenas Medianas", min_value=0.0, value=5.0, step=1.0)
cant_chica = st.sidebar.number_input("Cantidad de Antenas Chicas", min_value=0.0, value=3.0, step=1.0)

# SECCIÓN 2: Costes Operativos, Materiales y Viáticos (NUEVO)
st.sidebar.subheader("🚚 Viáticos y Mano de Obra")
distancia_km = st.sidebar.number_input("Distancia al sitio (Km)", min_value=0.0, value=25.0, step=5.0)
costo_km = st.sidebar.number_input("Costo por Km de combustible ($)", min_value=0.0, value=15.0, step=1.0)
horas_trabajo = st.sidebar.number_input("Horas estimadas de trabajo", min_value=1.0, value=6.0, step=1.0)
costo_hora = st.sidebar.number_input("Precio por hora técnica ($)", min_value=0.0, value=50.0, step=5.0)
trabajo_altura = st.sidebar.checkbox("¿Requiere trabajo en altura/riesgo?", value=False)

st.sidebar.subheader("🔌 Costes de Materiales Extra")
precio_cable_metro = st.sidebar.number_input("Precio por metro de cable ($)", min_value=0.0, value=2.5, step=0.5)
metros_por_antena = st.sidebar.number_input("Metros de cable por antena (Promedio)", min_value=1.0, value=15.0, step=1.0)

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

# Soportes específicos fijos por tipo de antena (NUEVO)
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
        
    # --- DETALLE DE COSTES AMPLIADO (NUEVO) ---
    st.header("💸 Desglose Total de Costes de la Operación")
    
    # 1. Costes de Hardware Base
    costo_hw_total = (antenas_g * r3_x) + (antenas_m * r3_y) + (antenas_c * r3_z)
    
    # 2. Costes de Estructuras / Soportes
    costo_soportes_total = (antenas_g * soporte_x) + (antenas_m * soporte_y) + (antenas_c * soporte_z)
    
    # 3. Costes de Cableado
    total_antenas = antenas_g + antenas_m + antenas_c
    total_metros_cable = total_antenas * metros_por_antena
    costo_cable_total = total_metros_cable * precio_cable_metro
    
    # 4. Mano de obra y Viáticos
    costo_viaticos = distancia_km * costo_km
    mano_obra_base = horas_trabajo * costo_hora
    adicional_altura = (mano_obra_base * 0.35) if trabajo_altura else 0.0  # +35% por riesgo de altura
    costo_mano_obra_total = mano_obra_base + adicional_altura
    
    # Coste final absoluto
    costo_total_proyecto = costo_hw_total + costo_soportes_total + costo_cable_total + costo_viaticos + costo_mano_obra_total
    
    # Mostrar métricas del desglose financiero comercial
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Equipos e Infraestructura", f"${costo_hw_total + costo_soportes_total:,.2f}")
    with c2:
        st.metric("Total Materiales (Cables)", f"${costo_cable_total:,.2f}")
    with c3:
        st.metric("Total Mano de Obra (+Riesgo)", f"${costo_mano_obra_total:,.2f}")
    with c4:
        st.metric("COSTO TOTAL FINAL DEL PROYECTO", f"${costo_total_proyecto:,.2f}", delta="Inversión requerida")
    
    # --- MONITOREO DINÁMICO DE RESTRICCIONES ---
    st.subheader("📊 Monitoreo Dinámico de Restricciones Técnicas (Base)")
    consumo_r1 = (res.x[0] * r1_x) + (res.x[1] * r1_y) + (res.x[2] * r1_z)
    consumo_r2 = (res.x[0] * r2_x) + (res.x[1] * r2_y) + (res.x[2] * r2_z)
    consumo_r3 = (res.x[0] * r3_x) + (res.x[1] * r3_y) + (res.x[2] * r3_z)
    
    datos_tabla = {
        "Restricción Analizada": ["Cantidad de Antenas", "Consumo de Watts", "Costo Base Hardware"],
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
    
    # --- MÓDULO EXPORTAR PDF (NUEVO) ---
    st.subheader("📄 Generación de Presupuesto Profesional")
    
    if PDF_DISPONIBLE:
        # Función para construir el documento PDF en memoria
        def generar_pdf():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
            subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.gray, spaceAfter=25)
            h2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor("#2B6CB0"), spaceBefore=15, spaceAfter=10)
            text_style = styles['Normal']
            
            # Encabezado
            story.append(Paragraph("PRESUPUESTO TÉCNICO DE INSTALACIÓN", title_style))
            story.append(Paragraph("Documento emitido por el Optimizador Logístico Automático", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Sección 1: Cantidades
            story.append(Paragraph("1. Resumen de Equipamiento a Instalar", h2_style))
            data_equipos = [
                ["Descripción del Elemento", "Cantidad Unidades"],
                ["Antena Grande (Estructural)", str(antenas_g)],
                ["Antena Mediana (Estructural)", str(antenas_m)],
                ["Antena Chica (Estructural)", str(antenas_c)]
            ]
            t_equipos = Table(data_equipos, colWidths=[300, 150])
            t_equipos.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC"))
            ]))
            story.append(t_equipos)
            story.append(Spacer(1, 15))
            
            # Sección 2: Desglose Económico
            story.append(Paragraph("2. Desglose de Costes y Conceptos Comerciales", h2_style))
            data_costos = [
                ["Concepto Técnico / Material", "Cálculo Realizado", "Subtotal ($)"],
                ["Hardware Base Antenas", f"Equipos principales", f"${costo_hw_total:,.2f}"],
            ]
