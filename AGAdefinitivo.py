import streamlit as st
import numpy as np
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
st.set_page_config(page_title="Calculador de Antenas 3D", layout="wide", page_icon="📊")
st.title("📊 Calculador y Presupuestador de Costes de Antenas")
st.write("Modificá la cantidad exacta de antenas a instalar para evaluar el escenario, la superficie cubierta y generar presupuestos.")

if not PDF_DISPONIBLE:
    st.warning("⚠️ Para descargar presupuestos en PDF, debés instalar reportlab. Corré en tu consola: `pip install reportlab`")

# --- VALORES TÉCNICOS Y COMERCIALES FIJOS ---
distancia_km = 25.0
costo_km = 15.0
horas_trabajo = 6.0
costo_hora = 50.0
trabajo_altura = False 

precio_cable_metro = 2.5
metros_cable_grande = 25.0
metros_cable_mediano = 15.0
metros_cable_chico = 10.0

# REPARADO: Aquí están las variables fijas de ganancia que causaban el NameError
g_x, g_y, g_z = 150.0, 100.0, 80.0       
r1_x, r1_y, r1_z = 1.0, 1.0, 1.0          
r2_x, r2_y, r2_z = 20.0, 10.0, 5.0        
r3_x, r3_y, r3_z = 500.0, 300.0, 200.0    
soporte_x, soporte_y, soporte_z = 80.0, 50.0, 30.0 

cober_x = 50.0  
cober_y = 30.0  
cober_z = 15.0  

# --- BARRA LATERAL: ENTRADA DE PARÁMETROS DEL USUARIO ---
st.sidebar.header("⚙️ Configuración del Proyecto")

st.sidebar.subheader("📡 Cantidad de Antenas a Instalar")
antenas_g = st.sidebar.number_input("Cantidad de Antenas Grandes", min_value=0.0, value=0.0, step=1.0)
antenas_m = st.sidebar.number_input("Cantidad de Antenas Medianas", min_value=0.0, value=0.0, step=1.0)
antenas_c = st.sidebar.number_input("Cantidad de Antenas Chicas", min_value=0.0, value=0.0, step=1.0)

st.sidebar.subheader("⚠️ Restricciones de Monitoreo")
lim_r1 = st.sidebar.number_input("Límite máximo Cantidad Total de Antenas (≤)", min_value=1.0, value=15.0, step=1.0)
lim_r2 = st.sidebar.number_input("Límite máximo Consumo de Watts (≤)", min_value=1.0, value=200.0, step=1.0)
lim_r3 = st.sidebar.number_input("Presupuesto Máximo Base ($) (≤)", min_value=1.0, value=5000.0, step=1.0)

# --- DISPLAY PRINCIPAL ---
st.header("🎯 Resultados del Escenario Seleccionado")

antenas_g_display = int(antenas_g) if antenas_g.is_integer() else antenas_g
antenas_m_display = int(antenas_m) if antenas_m.is_integer() else antenas_m
antenas_c_display = int(antenas_c) if antenas_c.is_integer() else antenas_c

superficie_lograda = (antenas_g * cober_x) + (antenas_m * cober_y) + (antenas_c * cober_z)
ganancia_estimada = (antenas_g * g_x) + (antenas_m * g_y) + (antenas_c * g_z)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Antenas Grandes", value=antenas_g_display)
with col2:
    st.metric(label="Antenas Medianas", value=antenas_m_display)
with col3:
    st.metric(label="Antenas Chicas", value=antenas_c_display)
with col4:
    st.metric(label="Ganancia Comercial Estimada", value=f"${ganancia_estimada:,.2f}")
    
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

costo_viaticos = distancia_km * costo_km
mano_obra_base = horas_trabajo * costo_hora
adicional_altura = (mano_obra_base * 0.35) if trabajo_altura else 0.0
costo_mano_obra_total = mano_obra_base + adicional_altura

costo_total_proyecto = costo_hw_total + costo_soportes_total + costo_cable_total + costo_viaticos + costo_mano_obra_total

consumo_r1 = (antenas_g * r1_x) + (antenas_m * r1_y) + (antenas_c * r1_z)
consumo_r2 = (antenas_g * r2_x) + (antenas_m * r2_y) + (antenas_c * r2_z)
consumo_r3 = (antenas_g * r3_x) + (antenas_m * r3_y) + (antenas_c * r3_z)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Equipos e Infraestructura", f"${costo_hw_total + costo_soportes_total:,.2f}")
with c2:
    st.metric("Total Materiales (Cables)", f"${costo_cable_total:,.2f}")
with c3:
    st.metric("Total Mano de Obra y Viáticos", f"${costo_mano_obra_total + costo_viaticos:,.2f}")
with c4:
    st.metric("COSTO TOTAL DEL PROYECTO", f"${costo_total_proyecto:,.2f}", delta=f"{round(superficie_lograda, 1)} m² cubiertos")

if consumo_r1 > lim_r1:
    st.error(f"⚠️ Se ha excedido el límite máximo de antenas permitido ({int(lim_r1)} U).")
if consumo_r2 > lim_r2:
    st.warning(f"⚠️ Se ha excedido el límite máximo de consumo eléctrico planificado ({int(lim_r2)} Watts).")
if consumo_r3 > lim_r3:
    st.info(f"⚠️ El costo base de hardware supera el presupuesto límite fijado (${int(lim_r3)}).")

# --- TABLA ÚNICA DE MONITOREO Y COSTES ---
st.header("📋 Matriz Unificada: Desglose por Antena, Restricciones y Costes")

tabla_maestra = {
    "Antenas a Eleccion": [
        "Cantidad de Antenas (U)", 
        "Cobertura de Superficie (m²)",
        "Consumo Eléctrico (Watts)", 
        "Costo de Hardware Base ($)", 
        "Costo Estructuras / Soportes ($)", 
        "Costo Material Extra: Cableado ($)",
        "Mano de Obra + Viáticos Operativos ($)",
        "COSTO TOTAL CONSOLIDADO ($)"
    ],
    "Grande": [
        f"{antenas_g_display} U", 
        f"{antenas_g * cober_x} m² (Capac: {cober_x}m²)",
        f"{antenas_g * r2_x} W (Coef: {r2_x})", 
        f"${costo_hw_g:,.2f} (${r3_x}/u)", 
        f"${costo_sop_g:,.2f}", 
        f"${costo_cable_g:,.2f} ({int(total_metros_g)}m)", 
        "-", 
        "-"
    ],
    "Mediana": [
        f"{antenas_m_display} U", 
        f"{antenas_m * cober_y} m² (Capac: {cober_y}m²)",
        f"{antenas_m * r2_y} W (Coef: {r2_y})", 
        f"${costo_hw_m:,.2f} (${r3_y}/u)", 
        f"${costo_sop_m:,.2f}", 
        f"${costo_cable_m:,.2f} ({int(total_metros_m)}m)", 
        "-", 
        "-"
    ],
    "Chica": [
        f"{antenas_c_display} U", 
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
        "Basado en selección manual",
        f"Máx: {int(lim_r2)} W", 
        f"Presupuesto Base ≤ ${int(lim_r3)}", 
        "Valores corporativos fijos", 
        f"Valor fijo: ${precio_cable_metro}/m", 
        f"Fijo: {horas_trabajo}hs, {distancia_km}km", 
        "Inversión final calculada"
    ],
    "Total Utilizado / Subtotal": [
        f"{round(consumo_r1, 2)} U (Holgura: {round(lim_r1 - consumo_r1, 2)})",
        f"{round(superficie_lograda, 2)} m²",
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
        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#1A365D"), spaceAfter=15)
        subtitle_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, textColor=colors.gray, spaceAfter=20)
        h2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2B6CB0"), spaceBefore=15, spaceAfter=10)
        cell_style = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=7, leading=9)
        cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=7, leading=9, fontName='Helvetica-Bold')

        story.append(Paragraph("PRESUPUESTO TÉCNICO UNIFICADO DE INSTALACIÓN", title_style))
        story.append(Paragraph("Documento consolidado emitido por el Calculador Logístico", subtitle_style))
        story.append(Spacer(1, 5))
        
        story.append(Paragraph("1. Cuadro Consolidado de Equipos, Restricciones y Costos", h2_style))
        
        data_reportlab = [
            [Paragraph(k, cell_bold) for k in tabla_maestra.keys()]
        ]
        
        for i in range(len(tabla_maestra["Antenas a Eleccion"])):
            fila = []
            for col_name in tabla_maestra.keys():
                texto = tabla_maestra[col_name][i]
                estilo = cell_bold if i == 7 or col_name == "Antenas a Eleccion" else cell_style
                fila.append(Paragraph(texto, estilo))
            data_reportlab.append(fila)

        # REPARADO DEFINITIVAMENTE: Anchos fijos de columna asignados y bloque de ReportLab completamente cerrado
        t_maestra = Table(data_reportlab, colWidths=[120, 75, 75, 75, 125, 100])
        t_maestra.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
