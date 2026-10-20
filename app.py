"""
========================================================================================
BUILDVISION AI · MEDICIÓN DE AVANCE FÍSICO DE OBRA CON VISIÓN COMPUTACIONAL
Caso Ancla del MVP: Red de Rociadores Contra Incendio (Sprinklers)
Grupo 15: Diego Avella · Patricia Luna · Daniel Salcedo
Implementación Interactiva Streamlit conforme a Sección 7 (UX/UI Wireframes a, b, c, d)
========================================================================================
"""
import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import io
import time
from datetime import datetime

import sys
from pathlib import Path

# Garantizar que la raíz del proyecto esté en sys.path (crítico para Streamlit Cloud en Linux)
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Importación de módulos del núcleo
from core.progress_calculator import (
    calculate_zone_progress,
    calculate_level_progress,
    DEFAULT_WEIGHTS,
    COMPONENT_NAMES
)
from core.quality_control import analyze_photo_quality
from core.model import (
    draw_detections,
    generate_mock_detections_for_zone,
    CLASS_METADATA,
    get_status_info
)
from core.sample_data import (
    PROJECTS_DATA,
    create_synthetic_construction_photo
)
from core.audit import AuditTrail
from core.report_generator import generate_weekly_pdf_report

# --------------------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="BuildVision AI - Control de Avance PCI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS (AEC FIELD GRADE - ALTO CONTRASTE, TÁCTIL >= 48px)
# --------------------------------------------------------------------------------------
st.markdown("""
<style>
    /* Tipografía y paleta base AEC */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Barra superior institucional */
    .brand-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border-bottom: 3px solid #0284C7;
        padding: 16px 24px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .brand-title {
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #F8FAFC;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .brand-subtitle {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-top: 4px;
    }

    /* Tarjetas de métrica y estado */
    .aec-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .aec-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    .aec-card-dark {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        color: #F8FAFC;
    }

    /* Badges de semáforo de confianza con texto + icono (Sección 7) */
    .badge-green {
        background-color: #DCFCE7;
        color: #15803D;
        border: 1px solid #86EFAC;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .badge-amber {
        background-color: #FEF3C7;
        color: #B45309;
        border: 1px solid #FCD34D;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .badge-red {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FCA5A5;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    /* Botones de acción táctil ergonómica (>= 48px según wireframes) */
    .stButton > button {
        min-height: 48px;
        font-weight: 700;
        font-size: 0.95rem;
        border-radius: 10px;
        transition: all 0.2s ease;
    }

    /* Indicador de modo sin conexión */
    .offline-indicator {
        background: #F1F5F9;
        border: 1px dashed #64748B;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        color: #475569;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Barra de progreso de obra */
    .progress-bar-container {
        background-color: #E2E8F0;
        border-radius: 10px;
        overflow: hidden;
        height: 20px;
        margin-top: 6px;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 10px;
        text-align: right;
        padding-right: 8px;
        color: white;
        font-size: 11px;
        font-weight: bold;
        line-height: 20px;
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# GESTIÓN DE ESTADO DE SESIÓN (SESSION STATE)
# --------------------------------------------------------------------------------------
if 'audit' not in st.session_state:
    st.session_state.audit = AuditTrail()

if 'current_screen' not in st.session_state:
    st.session_state.current_screen = "a_subir"  # 'a_subir', 'b_revision', 'c_avance', 'd_reporte'

if 'current_project' not in st.session_state:
    st.session_state.current_project = "Torre Norte"

if 'current_level' not in st.session_state:
    st.session_state.current_level = "Nivel 4"

if 'current_zone' not in st.session_state:
    st.session_state.current_zone = "Vano C-D"

if 'offline_mode' not in st.session_state:
    st.session_state.offline_mode = False

if 'offline_queue' not in st.session_state:
    st.session_state.offline_queue = []

if 'weights' not in st.session_state:
    st.session_state.weights = DEFAULT_WEIGHTS.copy()

# Cargar datos base de zonas si no existen
if 'zones_state' not in st.session_state:
    init_zones = PROJECTS_DATA["Torre Norte"]["levels"]["Nivel 4"]["zones"]
    # Copia profunda mutable
    st.session_state.zones_state = {}
    for zk, zv in init_zones.items():
        st.session_state.zones_state[zk] = {
            'id': zv['id'],
            'name': zv['name'],
            'coverage': zv['coverage'],
            'needs_review': zv['needs_review'],
            'plan': zv['plan'].copy(),
            'validated': zv['validated'].copy(),
            'detected_raw': zv['detected_raw'].copy(),
            'photo_meta': zv['photo_meta'].copy()
        }

if 'photo_index' not in st.session_state:
    st.session_state.photo_index = 2  # Como en Wireframe: "Revisión 2 de 8"

if 'total_photos' not in st.session_state:
    st.session_state.total_photos = 8

if 'user_name' not in st.session_state:
    st.session_state.user_name = "Daniel Salcedo (ITO)"

# --------------------------------------------------------------------------------------
# HEADER PRINCIPAL DE LA APLICACIÓN
# --------------------------------------------------------------------------------------
st.markdown("""
<div class="brand-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
        <div>
            <h1 class="brand-title">🏗️ BuildVision AI · Medición de Avance Físico</h1>
            <div class="brand-subtitle">
                Caso Ancla: <b>Red de Rociadores Contra Incendio (PCI · NFPA 13)</b> | Grupo 15: Diego Avella · Patricia Luna · Daniel Salcedo
            </div>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(255,255,255,0.12); padding: 6px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600;">
                👷 ITO Activo: <b>{}</b>
            </span>
        </div>
    </div>
</div>
""".format(st.session_state.user_name), unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# SIDEBAR: NAVEGACIÓN ENTRE LAS 4 PANTALLAS DEL PUNTO 7 UX/UI Y CONTROLES DE OBRA
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📱 Navegación de Terreno")
    st.caption("Flujo de usuario del caso principal (Figura 3 y 5)")

    nav_options = {
        "a_subir": "(a) Subir Fotos & Calidad",
        "b_revision": "(b) Revisión HITL (Foto a Foto)",
        "c_avance": "(c) Panel de Avance & Desviación",
        "d_reporte": "(d) Reporte Semanal & PDF"
    }

    selected_screen = st.radio(
        "Seleccione Pantalla:",
        options=list(nav_options.keys()),
        format_func=lambda x: nav_options[x],
        index=list(nav_options.keys()).index(st.session_state.current_screen),
        key="nav_radio"
    )
    if selected_screen != st.session_state.current_screen:
        st.session_state.current_screen = selected_screen
        st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Contexto de Obra")
    
    # Selector de proyecto
    proj_names = list(PROJECTS_DATA.keys())
    st.session_state.current_project = st.selectbox(
        "Proyecto:",
        proj_names,
        index=proj_names.index(st.session_state.current_project) if st.session_state.current_project in proj_names else 0
    )

    # Selector de nivel
    available_levels = list(PROJECTS_DATA[st.session_state.current_project].get("levels", {}).keys())
    if not available_levels:
        available_levels = ["Nivel 4"]
    st.session_state.current_level = st.selectbox(
        "Nivel / Sector:",
        available_levels,
        index=available_levels.index(st.session_state.current_level) if st.session_state.current_level in available_levels else 0
    )

    # Selector de vano/zona
    available_zones = list(st.session_state.zones_state.keys())
    st.session_state.current_zone = st.selectbox(
        "Vano / Zona:",
        available_zones,
        index=available_zones.index(st.session_state.current_zone) if st.session_state.current_zone in available_zones else 0
    )

    st.markdown("---")
    st.markdown("### 📶 Resiliencia de Conectividad (CP-01)")
    offline_toggle = st.toggle("Simular Modo Sin Señal (Offline)", value=st.session_state.offline_mode)
    if offline_toggle != st.session_state.offline_mode:
        st.session_state.offline_mode = offline_toggle
        st.rerun()

    if st.session_state.offline_mode:
        st.warning(f"📡 Modo Offline Activo. Las capturas se guardan en cola local ({len(st.session_state.offline_queue)} en cola).")
        if st.button("🔄 Sincronizar Cola al Servidor", use_container_width=True):
            if st.session_state.offline_queue:
                st.session_state.offline_queue.clear()
                st.success("✅ Fotos sincronizadas exitosamente.")
            else:
                st.info("No hay fotos pendientes en la cola.")
    else:
        st.success("📶 Conexión activa con el servidor de inferencia YOLO.")

    st.markdown("---")
    with st.expander("⚖️ Ajuste de Pesos de Partida (Sección 5)"):
        st.caption("Ponderaciones validadas por ITO y Jefe PCI:")
        w_tub = st.slider("Tubería (w1):", 0.0, 1.0, float(st.session_state.weights['tuberia']), 0.05)
        w_sop = st.slider("Soportes (w2):", 0.0, 1.0, float(st.session_state.weights['soportes']), 0.05)
        w_roc = st.slider("Rociadores (w3):", 0.0, 1.0, float(st.session_state.weights['rociadores']), 0.05)
        w_val = st.slider("Válvula (w4):", 0.0, 1.0, float(st.session_state.weights['valvula']), 0.05)
        w_pru = st.slider("Prueba Hidráulica (w5):", 0.0, 1.0, float(st.session_state.weights['prueba_hidraulica']), 0.05)
        
        sum_w = w_tub + w_sop + w_roc + w_val + w_pru
        if abs(sum_w - 1.0) > 0.01:
            st.error(f"Suma de pesos: {sum_w:.2f} (debe sumar exactamente 1.00)")
        else:
            st.success(f"Suma de pesos: {sum_w:.2f} (100% normalizado)")
            st.session_state.weights['tuberia'] = w_tub
            st.session_state.weights['soportes'] = w_sop
            st.session_state.weights['rociadores'] = w_roc
            st.session_state.weights['valvula'] = w_val
            st.session_state.weights['prueba_hidraulica'] = w_pru


# ======================================================================================
# PANTALLA 7 (A): SUBIR FOTOS & CONTROL DE CALIDAD (INGESTA RF-01, RF-02)
# ======================================================================================
if st.session_state.current_screen == "a_subir":
    st.markdown("## 📤 Pantalla (a): BuildVision · Subir")
    st.markdown(
        r"Captura o carga de fotografías de obra por zona, con **control automático de calidad** "
        r"(resolución $\ge$ 8 MP y nitidez Laplaciana) y cola de almacenamiento sin conexión."
    )

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.info(f"🏢 **Proyecto:** {st.session_state.current_project}")
    with col_meta2:
        st.info(f"📍 **Nivel:** {st.session_state.current_level}")
    with col_meta3:
        st.info(f"🎯 **Zona:** {st.session_state.current_zone}")

    # Pestañas de modo de carga
    tab_demo, tab_upload, tab_camera = st.tabs([
        "🌟 Cargar Caso de Terreno / CP-05 (Demostración Rápida)",
        "📁 Cargar desde Galería / Archivo (JPG >= 8 MP)",
        "📷 Capturar con Cámara de Terreno"
    ])

    uploaded_img = None
    source_label = ""

    with tab_demo:
        st.markdown("#### Selección de Fotos de Inspección Pre-cargadas")
        st.write("Fotos tomadas en la inspección de la red de rociadores contra incendio:")
        
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.markdown("##### Foto 1: Vano C-D (Caso Dorado CP-05)")
            st.caption("Resolución: 4032 x 3024 (12.2 MP) · Nitidez: 158.4 ✓")
            if st.button("Inspeccionar Vano C-D", use_container_width=True, key="btn_demo_cd"):
                st.session_state.current_zone = "Vano C-D"
                st.session_state.photo_index = 2
                uploaded_img = create_synthetic_construction_photo(zone_label="Vano C-D · Losa Nivel 4")
                source_label = "Vano C-D (Caso Dorado CP-05)"

        with col_d2:
            st.markdown("##### Foto 2: Vano E-F (Alerta Desviación)")
            st.caption("Resolución: 3840 x 2160 (8.3 MP) · Cobertura: Parcial ⚠")
            if st.button("Inspeccionar Vano E-F", use_container_width=True, key="btn_demo_ef"):
                st.session_state.current_zone = "Vano E-F"
                st.session_state.photo_index = 3
                uploaded_img = create_synthetic_construction_photo(zone_label="Vano E-F · Cobertura Parcial")
                source_label = "Vano E-F (Alerta Crítica)"

        with col_d3:
            st.markdown("##### Foto 3: Vano G-H (Foto Movida / Calidad Falla)")
            st.caption("Resolución: 2400 x 1800 (4.3 MP) · Nitidez: 42.1 ✗ (RF-02)")
            if st.button("Inspeccionar Vano G-H", use_container_width=True, key="btn_demo_gh"):
                st.session_state.current_zone = "Vano G-H"
                st.session_state.photo_index = 5
                # Imagen desenfocada
                base = create_synthetic_construction_photo(width=800, height=500, zone_label="Vano G-H · Foto Movida")
                uploaded_img = base.resize((400, 250)).resize((800, 500)) # efecto borroso
                source_label = "Vano G-H (Calidad Observada)"

    with tab_upload:
        file_input = st.file_uploader(
            "Seleccione imagen de obra (JPG, PNG, resolución recomendada >= 8 MP)",
            type=['jpg', 'jpeg', 'png']
        )
        if file_input is not None:
            uploaded_img = Image.open(file_input)
            source_label = file_input.name

    with tab_camera:
        camera_input = st.camera_input("Capturar foto desde cámara del dispositivo")
        if camera_input is not None:
            uploaded_img = Image.open(camera_input)
            source_label = f"Captura_Camara_{datetime.now().strftime('%H%M%S')}.jpg"

    # Si no se ha seleccionado ninguna foto en esta acción, mostramos por defecto la foto de la zona actual
    if uploaded_img is None:
        uploaded_img = create_synthetic_construction_photo(zone_label=f"{st.session_state.current_zone} · Nivel 4")
        source_label = f"Foto_Inspeccion_{st.session_state.current_zone}.jpg"

    # Evaluación en tiempo real del Control de Calidad (RF-02)
    qc_res = analyze_photo_quality(uploaded_img)

    st.markdown("---")
    st.markdown("### 🔍 Control de Calidad de Imagen Previo a Inferencia (RF-02)")

    col_q1, col_q2, col_q3 = st.columns(3)
    with col_q1:
        st.metric("Resolución Detectada", f"{qc_res['width']} x {qc_res['height']} px", f"{qc_res['megapixels']} MP")
    with col_q2:
        nitidez_color = "normal" if qc_res['is_sharp'] else "inverse"
        st.metric("Varianza Laplaciana (Nitidez)", f"{qc_res['sharpness_variance']}", "Umbral: >= 85.0")
    with col_q3:
        if qc_res['passed']:
            st.markdown("""
            <div style="background:#DCFCE7; border:1px solid #86EFAC; padding:12px; border-radius:8px; text-align:center;">
                <b style="color:#15803D;">CALIDAD APROBADA ✓</b><br/>
                <span style="font-size:0.85rem; color:#166534;">Apta para inferencia YOLOv8</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#FEE2E2; border:1px solid #FCA5A5; padding:12px; border-radius:8px; text-align:center;">
                <b style="color:#B91C1C;">AVISO DE NITIDEZ / RESOLUCIÓN ⚠</b><br/>
                <span style="font-size:0.85rem; color:#991B1B;">Riesgo de subestimar rociadores</span>
            </div>
            """, unsafe_allow_html=True)

    if qc_res['warnings']:
        for w in qc_res['warnings']:
            st.warning(f"⚠️ {w}")

    # Preview de la foto a subir
    col_prev, col_act = st.columns([2, 1])
    with col_prev:
        st.image(uploaded_img, caption=f"Vista previa: {source_label} ({qc_res['width']}x{qc_res['height']})", use_container_width=True)
    
    with col_act:
        st.markdown("#### Resumen de Lote")
        st.write(f"• **Fotos en sesión:** 3 fotos cargadas")
        st.write(f"• **Aviso de nitidez:** {'1 foto con advertencia' if not qc_res['passed'] else '0 fotos con advertencia'}")
        
        if st.session_state.offline_mode:
            st.info("💾 **Modo sin conexión:** La foto se almacenará en el almacenamiento local del celular hasta recuperar cobertura.")
            if st.button("📥 Guardar en Cola Offline", use_container_width=True):
                st.session_state.offline_queue.append(source_label)
                st.success(f"Guardada en cola ({len(st.session_state.offline_queue)} en espera).")
        else:
            st.markdown("""
            <div class="offline-indicator">
                <span>🟢</span>
                <span><b>Se guarda aunque no haya señal</b> (cola local activa)</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Analizar Fotos (Ultralytics YOLO)", type="primary", use_container_width=True):
                with st.spinner("Ejecutando inferencia YOLOv8s en contenedor local (<= 5s)..."):
                    time.sleep(1.2) # Simulación de inferencia rápida cumpliendo RNF-01 (<= 5s)
                st.success("✅ Inferencia completada: 5 clases detectadas.")
                st.session_state.current_screen = "b_revision"
                st.rerun()


# ======================================================================================
# PANTALLA 7 (B): REVISIÓN HITL - HUMAN-IN-THE-LOOP (F-05, RF-05, RF-06)
# ======================================================================================
elif st.session_state.current_screen == "b_revision":
    current_z = st.session_state.current_zone
    z_data = st.session_state.zones_state[current_z]
    
    # Header del wireframe 7b: "Revisión 2 de 8"
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
    with col_h1:
        st.markdown(f"## 🔍 Pantalla (b): Revisión HITL · {current_z}")
        st.caption(f"Revisión {st.session_state.photo_index} de {st.session_state.total_photos} fotos de la semana | {st.session_state.current_project}")
    with col_h2:
        cov_badge = "badge-green" if z_data['coverage'] == 'Total' else "badge-amber"
        st.markdown(f"""
        <div style="text-align:right; padding-top:10px;">
            <span class="{cov_badge}">Cobertura: {z_data['coverage']}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_h3:
        if st.session_state.audit.can_undo():
            if st.button("↩️ Deshacer (CP-07)", help="Revierte el último ajuste del ITO", use_container_width=True):
                last = st.session_state.audit.pop_undo()
                if last:
                    # Revertir el valor en el estado
                    comp = last['component']
                    z_data['validated'][comp] = last['old_value']
                    st.success(f"Revertido {comp} a {last['old_value']}.")
                    st.rerun()

    # Detecciones para la zona
    detections = generate_mock_detections_for_zone(current_z)
    base_photo = create_synthetic_construction_photo(zone_label=f"{current_z} · Nivel 4")
    
    # Controles de visualización de bounding boxes
    with st.expander("🛠️ Filtro de Visualización de Cajas Delimitadoras (YOLO)", expanded=False):
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            box_filter = st.selectbox(
                "Filtrar por semáforo de confianza:",
                ["all", "high", "review"],
                format_func=lambda x: "Todas las detecciones" if x == "all" else ("Solo Verdes (>= 0.80)" if x == "high" else "Solo Pendientes de Revisión (0.40 - 0.79)")
            )
        with c_f2:
            show_tags = st.checkbox("Mostrar etiquetas y puntaje de confianza", value=True)

    annotated_img = draw_detections(base_photo, detections, show_labels=show_tags, filter_status=box_filter)

    # Contenedor visual principal de la foto con cajas (Wireframe 7b)
    st.image(
        annotated_img,
        caption=f"Foto de la zona: {z_data['photo_meta']['code']} · {z_data['photo_meta']['resolution']} · Ultralytics YOLOv8s",
        use_container_width=True
    )

    # Conteo por clase con semáforo y estado (como en Wireframe 7b: "Rociadores 15 ✓, Tapones 3 ⚠, Soportes 14 ✓, Tramos 12 ✓")
    st.markdown("### 📊 Conteo Detectado vs Validado por el ITO")
    
    val_counts = z_data['validated']
    plan_units = z_data['plan']
    raw_counts = z_data['detected_raw']

    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.markdown("""
        <div class="aec-card" style="text-align:center; border-top: 4px solid #06B6D4;">
            <div style="font-size:0.8rem; color:#64748B; font-weight:600;">TRAMOS TUBERÍA</div>
            <div style="font-size:1.6rem; font-weight:800; color:#0F172A;">{} <span style="color:#059669; font-size:1.1rem;">✓</span></div>
            <div style="font-size:0.75rem; color:#475569;">Plan: {} tramos</div>
            <span class="badge-green">Confianza: 0.88</span>
        </div>
        """.format(val_counts['tuberia'], plan_units['tuberia']), unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="aec-card" style="text-align:center; border-top: 4px solid #3B82F6;">
            <div style="font-size:0.8rem; color:#64748B; font-weight:600;">SOPORTES</div>
            <div style="font-size:1.6rem; font-weight:800; color:#0F172A;">{} <span style="color:#059669; font-size:1.1rem;">✓</span></div>
            <div style="font-size:0.75rem; color:#475569;">Plan: {} unid.</div>
            <span class="badge-amber">1 dudoso: 0.41 ⚠</span>
        </div>
        """.format(val_counts['soportes'], plan_units['soportes']), unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="aec-card" style="text-align:center; border-top: 4px solid #10B981;">
            <div style="font-size:0.8rem; color:#64748B; font-weight:600;">ROCIADORES</div>
            <div style="font-size:1.6rem; font-weight:800; color:#0F172A;">{} <span style="color:#059669; font-size:1.1rem;">✓</span></div>
            <div style="font-size:0.75rem; color:#475569;">Plan: {} instalados</div>
            <span class="badge-green">Alta confianza: 0.93</span>
        </div>
        """.format(val_counts['rociadores'], plan_units['rociadores']), unsafe_allow_html=True)

    with c4:
        st.markdown("""
        <div class="aec-card" style="text-align:center; border-top: 4px solid #F59E0B;">
            <div style="font-size:0.8rem; color:#64748B; font-weight:600;">TAPONES SALIDA</div>
            <div style="font-size:1.6rem; font-weight:800; color:#B45309;">{} <span style="font-size:1.1rem;">⚠</span></div>
            <div style="font-size:0.75rem; color:#475569;">Salidas pendientes</div>
            <span class="badge-amber">Requiere rociador</span>
        </div>
        """.format(raw_counts.get('tapones', 3)), unsafe_allow_html=True)

    with c5:
        st.markdown("""
        <div class="aec-card" style="text-align:center; border-top: 4px solid #8B5CF6;">
            <div style="font-size:0.8rem; color:#64748B; font-weight:600;">VÁLVULA CONTROL</div>
            <div style="font-size:1.6rem; font-weight:800; color:#0F172A;">{} <span style="color:#059669; font-size:1.1rem;">✓</span></div>
            <div style="font-size:0.75rem; color:#475569;">Plan: {} unidad</div>
            <span class="badge-green">Confianza: 0.95</span>
        </div>
        """.format(val_counts['valvula'], plan_units['valvula']), unsafe_allow_html=True)

    # Cálculo dinámico en vivo de la zona conforme a Sección 5
    live_calc = calculate_zone_progress(val_counts, plan_units, st.session_state.weights)
    
    st.markdown(f"""
    <div style="background:#EFF6FF; border-left: 4px solid #3B82F6; padding:12px 18px; border-radius:6px; margin: 12px 0;">
        <span style="font-size:1rem; color:#1E40AF; font-weight:700;">
            Avance recalculado de {current_z}: <b>{live_calc['progress_pct']:.1f}%</b> (conforme a Caso CP-05)
        </span>
    </div>
    """, unsafe_allow_html=True)

    # BOTONES DE ACCIÓN ERGONÓMICA EN LA PARTE BAJA (WIRE FRAME 7B)
    # "Aprobar verdes" (alcance pulgar), "Corregir revisar ⚠", "Rechazar foto (repetir)"
    st.markdown("### 👆 Decisiones del Inspector Técnico (HITL)")
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        if st.button("✅ Aprobar Verdes (Lote en 1 toque)", type="primary", use_container_width=True):
            st.session_state.audit.log_action(
                user=st.session_state.user_name,
                action="Aprobación en Bloque",
                zone_id=current_z,
                target_component="Todas las clases >= 0.80",
                old_val="Detección YOLO",
                new_val="Aprobado",
                note=f"Aprobación rápida en bloque para {current_z}"
            )
            st.success(f"Detecciones verdes aprobadas para {current_z}.")
            time.sleep(0.5)
            st.session_state.current_screen = "c_avance"
            st.rerun()

    with btn_col2:
        with st.popover("✏️ Corregir / Revisar ⚠", use_container_width=True):
            st.markdown(f"#### Modificación Manual de Conteos ({current_z})")
            st.caption("Modifique las cantidades detectadas si la IA cometió omisión o falso positivo:")
            
            c_tub = st.number_input("Tubería (tramos):", min_value=0, max_value=50, value=int(val_counts['tuberia']))
            c_sop = st.number_input("Soportes confirmados:", min_value=0, max_value=50, value=int(val_counts['soportes']))
            c_roc = st.number_input("Rociadores instalados:", min_value=0, max_value=50, value=int(val_counts['rociadores']))
            c_val = st.number_input("Válvula de control:", min_value=0, max_value=5, value=int(val_counts['valvula']))
            c_pru = st.checkbox("Prueba hidráulica conforme (200 psi NFPA 13)", value=bool(val_counts.get('prueba_hidraulica', 0)))

            correc_note = st.text_input("Motivo de corrección (para auditoría):", "Ajuste manual de rociador en sombra detrás de ducto")

            if st.button("💾 Guardar Corrección y Recalcular", type="primary", use_container_width=True):
                # Registrar auditoría de cada campo cambiado
                for comp, old_v, new_v in [
                    ('tuberia', val_counts['tuberia'], c_tub),
                    ('soportes', val_counts['soportes'], c_sop),
                    ('rociadores', val_counts['rociadores'], c_roc),
                    ('valvula', val_counts['valvula'], c_val),
                    ('prueba_hidraulica', val_counts['prueba_hidraulica'], 1 if c_pru else 0)
                ]:
                    if old_v != new_v:
                        st.session_state.audit.log_action(
                            user=st.session_state.user_name,
                            action="Corrección Manual",
                            zone_id=current_z,
                            target_component=comp,
                            old_val=old_v,
                            new_val=new_v,
                            note=correc_note
                        )
                # Actualizar estado
                val_counts['tuberia'] = c_tub
                val_counts['soportes'] = c_sop
                val_counts['rociadores'] = c_roc
                val_counts['valvula'] = c_val
                val_counts['prueba_hidraulica'] = 1 if c_pru else 0
                st.success("Avance recalculado y trazabilidad guardada en auditoría.")
                st.rerun()

    with btn_col3:
        if st.button("❌ Rechazar Foto (Repetir)", use_container_width=True):
            st.session_state.audit.log_action(
                user=st.session_state.user_name,
                action="Rechazo de Foto",
                zone_id=current_z,
                target_component="Foto completa",
                old_val="Cargada",
                new_val="Rechazada",
                note="Foto borrosa o no representativa"
            )
            st.warning(f"Foto de {current_z} rechazada. Se solicita repetir captura en terreno.")
            time.sleep(0.5)
            st.session_state.current_screen = "a_subir"
            st.rerun()

    # Botón directo para pasar a la siguiente pantalla
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➡️ Ir al Panel de Avance Consolidado", use_container_width=True):
        st.session_state.current_screen = "c_avance"
        st.rerun()


# ======================================================================================
# PANTALLA 7 (C): PANEL DE AVANCE & DESVIACIONES (F-06, RF-07, WIREFRAME 7C)
# ======================================================================================
elif st.session_state.current_screen == "c_avance":
    st.markdown(f"## 📊 Pantalla (c): Avance · {st.session_state.current_level}")
    st.caption(f"{st.session_state.current_project} · Seguimiento comparativo contra el plan semanal")

    # Lista de zonas evaluadas
    zones_list = []
    for zk, zv in st.session_state.zones_state.items():
        zones_list.append({
            'name': zk,
            'plan': zv['plan'],
            'validated': zv['validated'],
            'coverage': zv['coverage'],
            'needs_review': zv['needs_review'],
            'plan_week_pct': 85.0
        })

    level_eval = calculate_level_progress(zones_list, st.session_state.weights)
    level_real = level_eval['level_progress_pct']
    level_plan = 85.0
    level_dev = round(level_real - level_plan, 1)

    # WIREFRAME 7C: "80 % real · plan semana: 85 %"
    col_kpi1, col_kpi2, col_kpi3 = st.columns([2, 1, 1])
    with col_kpi1:
        st.markdown(f"""
        <div class="aec-card" style="border-left: 6px solid #0284C7; padding: 20px;">
            <div style="font-size: 0.9rem; font-weight:700; color:#64748B;">AVANCE FÍSICO GLOBAL · {st.session_state.current_level}</div>
            <div style="font-size: 3.2rem; font-weight: 800; color: #0F172A; line-height: 1.1;">
                {level_real:.1f} %
            </div>
            <div style="font-size: 0.95rem; color: #475569; margin-top: 4px;">
                Real vs Plan Semana: <b>{level_plan:.1f} %</b> (Brecha: <b style="color: {'#DC2626' if level_dev < -5 else '#059669'};">{level_dev:+.1f} pp</b>)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi2:
        st.markdown(f"""
        <div class="aec-card" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.85rem; color:#64748B; font-weight:600;">ESTADO DE REVISIÓN</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #059669; margin: 6px 0;">8 / 8 Fotos ✓</div>
            <span class="badge-green">Sin pendientes críticos</span>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
        <div class="aec-card" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.85rem; color:#64748B; font-weight:600;">TOTAL ELEMENTOS</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #0284C7; margin: 6px 0;">{level_eval['total_plan_units']} unid.</div>
            <span style="font-size: 0.8rem; color:#64748B;">Distribuidas en 5 vanos</span>
        </div>
        """, unsafe_allow_html=True)

    # ALERTA DE WIRE FRAME 7C: "▲ Vano E-F: -12 pp (alerta)" o alertas automáticas
    st.markdown("### ⚠️ Semáforo de Desviaciones y Alertas de Obra")
    critical_alerts = [z for z in level_eval['zones'] if z['alert_status'] in ['CRÍTICA', 'DESVIACIÓN']]
    
    if critical_alerts:
        for ca in critical_alerts:
            color = "#FEE2E2" if ca['alert_status'] == 'CRÍTICA' else "#FEF3C7"
            border = "#EF4444" if ca['alert_status'] == 'CRÍTICA' else "#F59E0B"
            text_color = "#991B1B" if ca['alert_status'] == 'CRÍTICA' else "#92400E"
            st.markdown(f"""
            <div style="background:{color}; border: 1px solid {border}; border-left: 6px solid {border}; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px;">
                <b style="color:{text_color}; font-size:1rem;">▲ {ca['name']}: {ca['deviation_pp']:+.1f} pp ({ca['alert_status']})</b>
                <div style="font-size:0.85rem; color:{text_color}; margin-top:2px;">
                    Avance real: {ca['progress_pct']:.1f}% frente a meta plan de {ca['plan_week_pct']:.1f}%. Cobertura: {ca['coverage']}.
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Todos los vanos se encuentran dentro del umbral de tolerancia planificado (< 5 pp).")

    # WIREFRAME 7C: BARRAS POR VANO (C-D 80%, D-E 92%, E-F 63%, F-G 71%, G-H 40%)
    st.markdown("### 🧱 Desglose de Avance Físico por Vano")
    
    for z in level_eval['zones']:
        with st.container():
            col_z1, col_z2, col_z3 = st.columns([2, 5, 2])
            with col_z1:
                st.markdown(f"**{z['name']}**")
                st.caption(f"Cobertura: {z['coverage']} · Desv: {z['deviation_pp']:+.1f} pp")
            
            with col_z2:
                pct = z['progress_pct']
                bar_color = "#10B981" if pct >= 80 else ("#F59E0B" if pct >= 65 else "#EF4444")
                st.markdown(f"""
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: {min(100, max(5, pct))}%; background-color: {bar_color};">
                        {pct:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_z3:
                if z['needs_review']:
                    if st.button("Ver zona pendiente (2)", key=f"btn_rev_{z['name']}", use_container_width=True):
                        st.session_state.current_zone = z['name']
                        st.session_state.current_screen = "b_revision"
                        st.rerun()
                else:
                    if st.button("Detalle Vano", key=f"btn_det_{z['name']}", use_container_width=True):
                        st.session_state.current_zone = z['name']
                        st.session_state.current_screen = "b_revision"
                        st.rerun()

    # Tabla detallada del Caso Dorado CP-05
    with st.expander("🔬 Ver Matriz de Ponderación Matemática Caso CP-05 (Vano C-D)"):
        st.write(r"Fórmula: $A(z) = \sum w(c) \cdot p(c,z)$")
        cd_data = [z for z in level_eval['zones'] if z['name'] == 'Vano C-D'][0]
        df_cp05 = pd.DataFrame(cd_data['components'])
        df_cp05.columns = ["Clave", "Componente", "Peso (w)", "Validado", "Plan", "Ratio p(c,z)", "Aporte (w·p)"]
        st.dataframe(df_cp05, use_container_width=True)

    # BOTÓN PRINCIPAL WIREFRAME 7C: "Generar reporte"
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📑 Generar Reporte Semanal", type="primary", use_container_width=True):
        st.session_state.current_screen = "d_reporte"
        st.rerun()


# ======================================================================================
# PANTALLA 7 (D): REPORTE SEMANAL & EXPORTACIÓN PDF (F-07, RF-08, WIREFRAME 7D)
# ======================================================================================
elif st.session_state.current_screen == "d_reporte":
    st.markdown("## 📄 Pantalla (d): Reporte Semanal · Sem. 42")
    st.caption("Consolidación ejecutiva para Administrador de Obra, Mandante e ITO")

    # Lista de zonas evaluadas
    zones_list = []
    for zk, zv in st.session_state.zones_state.items():
        zones_list.append({
            'name': zk,
            'plan': zv['plan'],
            'validated': zv['validated'],
            'coverage': zv['coverage'],
            'needs_review': zv['needs_review'],
            'plan_week_pct': 85.0
        })
    level_eval = calculate_level_progress(zones_list, st.session_state.weights)
    audit_entries = st.session_state.audit.get_logs_as_dicts()

    # Generación del PDF con ReportLab
    pdf_bytes = generate_weekly_pdf_report(
        project_name=st.session_state.current_project,
        level_name=st.session_state.current_level,
        week_number=42,
        ito_name=st.session_state.user_name,
        level_data=level_eval,
        audit_logs=audit_entries,
        notes="Inspección conforme a protocolo NFPA 13. Se solicita a subcontratista corregir montaje en Vano E-F."
    )

    # WIREFRAME 7D: TARJETA RESUMEN EJECUTIVO
    st.markdown("""
    <div class="aec-card" style="border: 2px solid #0284C7; padding: 24px; background: #F8FAFC;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #CBD5E1; padding-bottom: 12px; margin-bottom: 16px;">
            <div>
                <h3 style="margin: 0; color: #0F172A;">Reporte Semanal · Sem. 42</h3>
                <span style="color: #64748B; font-size: 0.9rem;">Obra: <b>Torre Norte</b> | Nivel: <b>Nivel 4</b></span>
            </div>
            <span class="badge-green" style="font-size: 0.95rem; padding: 6px 14px;">
                8/8 fotos revisadas ✓ Sin pendientes
            </span>
        </div>
        <ul style="font-size: 1rem; color: #1E293B; line-height: 1.8;">
            <li><b>Resumen de Avance:</b> Avance real ponderado <b>{:.1f}%</b> (Plan semanal: 85.0%)</li>
            <li><b>Tabla de avance por zona:</b> 5 vanos monitoreados (C-D, D-E, E-F, F-G, G-H)</li>
            <li><b>Alertas de desviación:</b> Alerta roja en Vano E-F (-22.0 pp) por ramales atrasados</li>
            <li><b>Evidencia y Trazabilidad:</b> 8 fotos auditadas con bounding boxes y firma de ITO</li>
        </ul>
    </div>
    """.format(level_eval['level_progress_pct']), unsafe_allow_html=True)

    # BOTONES DE ACCIÓN WIREFRAME 7D: "Descargar PDF" y "Compartir"
    col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
    with col_d1:
        st.download_button(
            label="📥 Descargar Reporte Oficial en PDF (RF-08)",
            data=pdf_bytes,
            file_name=f"Reporte_PCI_BuildVision_Sem42_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    with col_d2:
        if st.button("📤 Compartir Reporte", use_container_width=True):
            st.info("📋 Enlace de reporte semanal copiado para envío vía WhatsApp / Correo de Obra.")

    with col_d3:
        if st.button("🔄 Nueva Inspección", use_container_width=True):
            st.session_state.current_screen = "a_subir"
            st.rerun()

    # VISTA PREVIA DETALLADA DEL INFORME
    st.markdown("---")
    st.markdown("### 📋 Vista Previa de Tablas del Reporte")

    t1, t2, t3 = st.tabs(["📊 Matriz de Avance por Vano", "🛡️ Registro de Auditoría HITL", "📷 Galería de Fotos de Respaldo"])
    
    with t1:
        table_rows = []
        for z in level_eval['zones']:
            table_rows.append({
                'Vano': z['name'],
                'Avance Real': f"{z['progress_pct']:.1f}%",
                'Plan Semanal': f"{z['plan_week_pct']:.1f}%",
                'Desviación': f"{z['deviation_pp']:+.1f} pp",
                'Estado Semáforo': z['alert_status'],
                'Cobertura': z['coverage']
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

    with t2:
        if audit_entries:
            df_audit = pd.DataFrame(audit_entries)
            st.dataframe(df_audit, use_container_width=True)
        else:
            st.info("Todas las detecciones fueron aprobadas con semáforo verde sin correcciones manuales.")

    with t3:
        st.markdown("#### Galería de Evidencia Fotográfica con Bounding Boxes")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            img1 = draw_detections(create_synthetic_construction_photo(zone_label="Vano C-D"), generate_mock_detections_for_zone("Vano C-D"))
            st.image(img1, caption="Vano C-D: 15 rociadores, 14 soportes, 12 tramos (80.4% validado)", use_container_width=True)
        with col_g2:
            img2 = draw_detections(create_synthetic_construction_photo(zone_label="Vano E-F"), generate_mock_detections_for_zone("Vano E-F"))
            st.image(img2, caption="Vano E-F: Cobertura parcial, alerta de desviación -22.0 pp", use_container_width=True)

    # Firma de conformidad técnica
    st.markdown("---")
    st.markdown("### ✍️ Validación y Firmas")
    col_sig1, col_sig2 = st.columns(2)
    with col_sig1:
        st.markdown(f"""
        <div style="border: 1px dashed #94A3B8; padding: 16px; border-radius: 8px; text-align: center;">
            <div style="font-family: cursive; font-size: 1.4rem; color: #0284C7;">Daniel Salcedo</div>
            <hr style="margin: 8px 0;">
            <b>Inspector Técnico de Obra (ITO)</b><br/>
            <span style="font-size: 0.8rem; color: #64748B;">Daniel Salcedo Salcedo · Registro CIP 49210</span>
        </div>
        """, unsafe_allow_html=True)
    with col_sig2:
        st.markdown(f"""
        <div style="border: 1px dashed #94A3B8; padding: 16px; border-radius: 8px; text-align: center;">
            <div style="font-family: cursive; font-size: 1.4rem; color: #0284C7;">Patricia Luna & Diego Avella</div>
            <hr style="margin: 8px 0;">
            <b>Jefe de Terreno / Admin de Obra</b><br/>
            <span style="font-size: 0.8rem; color: #64748B;">Recepción y VoBo de Avance Semanal</span>
        </div>
        """, unsafe_allow_html=True)
