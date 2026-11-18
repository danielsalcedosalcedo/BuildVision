"""
========================================================================================
BUILDVISION AI · MEDICIÓN DE AVANCE FÍSICO DE OBRA CON VISIÓN COMPUTACIONAL
Caso ancla del MVP: red de rociadores contra incendio (PCI)
Grupo 15: Diego Avella · Patricia Luna · Daniel Salcedo
Implementación Interactiva Streamlit conforme a Sección 7 (UX/UI Wireframes a, b, c, d)
========================================================================================
"""
import streamlit as st
import pandas as pd
from PIL import Image
import importlib
import io
from datetime import datetime

import sys
from pathlib import Path

# Garantizar que la raíz del proyecto esté en sys.path (crítico para Streamlit Cloud en Linux)
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Importar módulos por separado permite refrescarlos al migrar una sesión activa.
from core import inference as inference_module
from core import model as model_module
from core import progress_calculator as progress_module
from core import quality_control as quality_module
from core import report_generator as report_module
from core import sample_data as sample_data_module
from core.audit import AuditTrail

# --------------------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="BuildVision AI - Avance de Rociadores PCI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Streamlit puede conservar módulos importados entre reruns de una sesión existente.
if st.session_state.get('category_version') != 'pci-v1':
    for module in (
        inference_module,
        model_module,
        progress_module,
        quality_module,
        report_module,
        sample_data_module,
    ):
        importlib.reload(module)

from core.progress_calculator import (
    calculate_zone_progress,
    calculate_level_progress,
    DEFAULT_WEIGHTS,
)
from core.quality_control import analyze_photo_quality
from core.model import draw_detections
from core.inference import (
    CLASS_TO_COMPONENT,
    InferenceUnavailable,
    detections_from_json,
    run_inference,
)
from core.sample_data import PROJECTS_DATA
from core.report_generator import generate_weekly_pdf_report

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
    st.session_state.current_zone = "Columnas eje C-D"

if 'weights' not in st.session_state or set(st.session_state.weights) != set(DEFAULT_WEIGHTS):
    st.session_state.weights = DEFAULT_WEIGHTS.copy()

if 'active_inspection' not in st.session_state:
    st.session_state.active_inspection = None

if 'inspected_zones' not in st.session_state:
    st.session_state.inspected_zones = set()

screen_transition_pending = 'pending_screen' in st.session_state
if screen_transition_pending:
    st.session_state.nav_radio = st.session_state.pending_screen
    st.session_state.current_screen = st.session_state.pending_screen
    del st.session_state.pending_screen

def navigate_to(screen: str) -> None:
    st.session_state.pending_screen = screen
    st.session_state.current_screen = screen
    st.rerun()

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
        }

if st.session_state.get('category_version') != 'pci-v1':
    init_zones = PROJECTS_DATA["Torre Norte"]["levels"]["Nivel 4"]["zones"]
    st.session_state.zones_state = {
        zone_name: {
            'id': zone['id'],
            'name': zone['name'],
            'coverage': zone['coverage'],
            'needs_review': zone['needs_review'],
            'plan': zone['plan'].copy(),
            'validated': zone['validated'].copy(),
        }
        for zone_name, zone in init_zones.items()
    }
    st.session_state.weights = DEFAULT_WEIGHTS.copy()
    st.session_state.current_zone = next(iter(init_zones))
    st.session_state.current_screen = 'a_subir'
    st.session_state.nav_radio = 'a_subir'
    st.session_state.active_inspection = None
    st.session_state.inspected_zones = set()
    st.session_state.category_version = 'pci-v1'
    if 'pending_screen' in st.session_state:
        del st.session_state.pending_screen
    screen_transition_pending = False

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
                Caso ancla: <b>Armadura de refuerzo / Enfierradura</b> | Grupo 15: Diego Avella · Patricia Luna · Daniel Salcedo
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
        index=None if screen_transition_pending else list(nav_options.keys()).index(st.session_state.current_screen),
        key="nav_radio"
    )
    if selected_screen != st.session_state.current_screen:
        st.session_state.current_screen = selected_screen
        st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Contexto de Obra")
    
    st.caption("Proyecto piloto: Torre Norte · Nivel 4")
    st.caption("Las inspecciones se mantienen en memoria durante esta sesión.")

    # Selector de elemento o sector
    available_zones = list(st.session_state.zones_state.keys())
    st.session_state.current_zone = st.selectbox(
        "Elemento / Zona:",
        available_zones,
        index=available_zones.index(st.session_state.current_zone) if st.session_state.current_zone in available_zones else 0
    )

    st.markdown("---")
    with st.expander("⚖️ Ajuste de Pesos de Partida (Sección 5)"):
        st.caption("Pesos iniciales de demostración; deben ajustarse al presupuesto y al criterio del ITO.")
        w_pipe = st.slider("Tubería:", 0.0, 1.0, float(st.session_state.weights['tuberia']), 0.05)
        w_support = st.slider("Soportes y colgadores:", 0.0, 1.0, float(st.session_state.weights['soportes']), 0.05)
        w_sprinkler = st.slider("Rociadores instalados:", 0.0, 1.0, float(st.session_state.weights['rociadores']), 0.05)
        w_valve = st.slider("Válvula de control:", 0.0, 1.0, float(st.session_state.weights['valvula']), 0.05)
        w_test = st.slider("Prueba hidráulica:", 0.0, 1.0, float(st.session_state.weights['prueba_hidraulica']), 0.05)

        sum_w = w_pipe + w_support + w_sprinkler + w_valve + w_test
        if abs(sum_w - 1.0) > 0.01:
            st.error(f"Suma de pesos: {sum_w:.2f} (debe sumar exactamente 1.00)")
        else:
            st.success(f"Suma de pesos: {sum_w:.2f} (100% normalizado)")
            st.session_state.weights.update({
                'tuberia': w_pipe,
                'soportes': w_support,
                'rociadores': w_sprinkler,
                'valvula': w_valve,
                'prueba_hidraulica': w_test,
            })


# ======================================================================================
# PANTALLA 7 (A): SUBIR FOTOS & CONTROL DE CALIDAD (INGESTA RF-01, RF-02)
# ======================================================================================
if st.session_state.current_screen == "a_subir":
    st.markdown("## 📤 Pantalla (a): BuildVision · Subir")
    st.markdown(
        "Carga una fotografía de la instalación PCI, revisa su calidad y valida los componentes detectados. "
        "El avance se calcula por elementos planificados y requiere revisión del ITO."
    )
    st.caption(
        "Las detecciones visuales son candidatas y requieren validación del ITO; la prueba hidráulica se registra manualmente."
    )

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        st.info(f"🏢 **Proyecto:** {st.session_state.current_project}")
    with col_meta2:
        st.info(f"📍 **Nivel:** {st.session_state.current_level}")
    with col_meta3:
        st.info(f"🎯 **Elemento / zona:** {st.session_state.current_zone}")

    tab_upload, tab_camera = st.tabs([
        "📁 Cargar fotografía real",
        "📷 Capturar con cámara"
    ])

    uploaded_img = None
    source_label = ""
    image_bytes = None

    with tab_upload:
        file_input = st.file_uploader(
            "Seleccione una fotografía de obra (JPG, JPEG o PNG)",
            type=['jpg', 'jpeg', 'png'],
            key="inspection_photo_upload"
        )
        if file_input is not None:
            image_bytes = file_input.getvalue()
            source_label = file_input.name
            uploaded_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    with tab_camera:
        camera_input = st.camera_input("Capturar foto desde cámara del dispositivo")
        if camera_input is not None:
            image_bytes = camera_input.getvalue()
            source_label = f"Captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            uploaded_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    st.markdown("---")
    st.markdown("### 🔍 Control de calidad de imagen")
    if uploaded_img is None:
        st.info("Carga o captura una fotografía real para comenzar la inspección.")
    else:
        qc_res = analyze_photo_quality(uploaded_img)
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            st.metric("Resolución", f"{qc_res['width']} × {qc_res['height']} px", f"{qc_res['megapixels']} MP")
        with col_q2:
            st.metric("Nitidez Laplaciana", qc_res['sharpness_variance'], "Referencia: 85")
        with col_q3:
            st.metric("Estado", qc_res['status_label'])
        for warning in qc_res['warnings']:
            st.warning(warning)

        col_prev, col_act = st.columns([2, 1])
        with col_prev:
            st.image(uploaded_img, caption=f"{source_label} · {qc_res['width']} × {qc_res['height']}", use_container_width=True)
        with col_act:
            st.markdown("#### Detección")
            detection_json = st.file_uploader(
                "Opcional: importa detecciones JSON si no hay modelo entrenado",
                type=["json"],
                key="inspection_detections_json"
            )
            st.caption("Se necesitan pesos entrenados para PCI; sin ellos, la app no inventa detecciones y permite revisión manual.")
            if st.button("Analizar y pasar a revisión", type="primary", use_container_width=True):
                detections = []
                ignored = {}
                engine = "Conteo manual (sin modelo entrenado)"
                if detection_json is not None:
                    try:
                        detections, ignored, errors = detections_from_json(detection_json.getvalue())
                    except (ValueError, UnicodeDecodeError) as exc:
                        st.error(f"No se pudo leer el JSON de detecciones: {exc}")
                        st.stop()
                    if errors:
                        st.warning("Algunas detecciones se omitieron: " + "; ".join(errors))
                    engine = "Detecciones importadas desde JSON"
                else:
                    try:
                        with st.spinner("Ejecutando modelo de detección…"):
                            result = run_inference(uploaded_img)
                        detections = result['detections']
                        ignored = result['ignored']
                        engine = result['engine']
                        st.caption(f"{engine} · {result['seconds']} s")
                    except InferenceUnavailable as exc:
                        st.info(f"{exc} Puedes continuar con revisión y conteo manual; no se mostrarán detecciones inventadas.")

                zone_data = st.session_state.zones_state[st.session_state.current_zone]
                initial_counts = zone_data['validated'].copy()
                initial_counts['rociadores'] = 0
                for detection in detections:
                    component = CLASS_TO_COMPONENT.get(detection['class'])
                    if component in initial_counts and detection['confidence'] >= 0.80:
                        initial_counts[component] += 1
                st.session_state.active_inspection = {
                    "image": image_bytes,
                    "name": source_label,
                    "zone": st.session_state.current_zone,
                    "quality": qc_res,
                    "detections": detections,
                    "ignored": ignored,
                    "engine": engine,
                    "counts": initial_counts
                }
                navigate_to("b_revision")


# ======================================================================================
# PANTALLA 7 (B): REVISIÓN HITL - HUMAN-IN-THE-LOOP (F-05, RF-05, RF-06)
# ======================================================================================
elif st.session_state.current_screen == "b_revision":
    active_inspection = st.session_state.active_inspection
    if active_inspection is None:
        st.warning("No hay una fotografía cargada para revisar. Carga una imagen real en la pantalla (a).")
        if st.button("Ir a cargar fotografía", type="primary"):
            navigate_to("a_subir")
        st.stop()

    current_z = active_inspection["zone"]
    st.session_state.current_zone = current_z
    z_data = st.session_state.zones_state[current_z]
    
    # Header del wireframe 7b: "Revisión 2 de 8"
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
    with col_h1:
        st.markdown(f"## 🔍 Pantalla (b): Revisión HITL · {current_z}")
        st.caption(f"{st.session_state.current_project} · {active_inspection['name']}")
    with col_h2:
        quality_label = active_inspection["quality"]["status_label"]
        quality_badge = "badge-green" if active_inspection["quality"]["passed"] else "badge-amber"
        st.markdown(f"""
        <div style="text-align:right; padding-top:10px;">
            <span class="{quality_badge}">Calidad: {quality_label}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_h3:
        if st.session_state.audit.can_undo():
            if st.button("↩️ Deshacer (CP-07)", help="Revierte el último ajuste del ITO", use_container_width=True):
                last = st.session_state.audit.pop_undo()
                if last:
                    comp = last['component']
                    if last['zone_id'] == current_z and comp in z_data['validated']:
                        z_data['validated'][comp] = last['old_value']
                        active_inspection['counts'][comp] = last['old_value']
                        z_data['needs_review'] = True
                        st.success(f"Revertido {comp} a {last['old_value']}.")
                    else:
                        st.warning("La última acción no corresponde a esta zona y no se aplicó.")
                    st.rerun()

    detections = active_inspection["detections"]
    base_photo = Image.open(io.BytesIO(active_inspection["image"])).convert("RGB")
    
    # Controles de visualización de bounding boxes
    with st.expander("🛠️ Filtro de visualización de detecciones", expanded=False):
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
        caption=f"{active_inspection['name']} · {active_inspection['engine']}",
        use_container_width=True
    )
    if active_inspection["ignored"]:
        st.info(f"Clases ajenas al caso PCI omitidas: {active_inspection['ignored']}")
    if not detections:
        st.info("No hay detecciones disponibles. Ingresa los conteos manualmente en «Corregir / Revisar»; la imagen no se analiza de forma simulada.")

    st.markdown("### 📊 Revisión de detecciones y avance")
    st.caption(
        "Cada caja representa un componente visual candidato; confirma los conteos contra el plan antes de aprobar el avance."
    )
    val_counts = active_inspection["counts"]
    plan_units = z_data['plan']
    raw_counts = {key: 0 for key in val_counts}
    review_counts = {key: 0 for key in val_counts}
    high_counts = {key: 0 for key in val_counts}
    for detection in detections:
        component = CLASS_TO_COMPONENT.get(detection['class'])
        if component in raw_counts:
            raw_counts[component] += 1
            if detection['confidence'] >= 0.80:
                high_counts[component] += 1
            elif detection['confidence'] >= 0.40:
                review_counts[component] += 1

    review_items = [
        ('tuberia', 'TUBERÍA', '#06B6D4'),
        ('soportes', 'SOPORTES', '#3B82F6'),
        ('rociadores', 'ROCIADORES', '#10B981'),
        ('valvula', 'VÁLVULA', '#8B5CF6'),
        ('prueba_hidraulica', 'PRUEBA HIDRÁULICA', '#F59E0B'),
    ]
    for column, (key, label, color) in zip(st.columns(len(review_items)), review_items):
        with column:
            if key == 'rociadores':
                status = (
                    f"Candidatas ≥ 0.80: {high_counts[key]} · "
                    f"Revisar: {review_counts[key]}"
                )
            else:
                status = "Validación manual del ITO"
            st.markdown(
                f"""
                <div class="aec-card" style="text-align:center; border-top: 4px solid {color};">
                    <div style="font-size:0.8rem; color:#64748B; font-weight:600;">{label}</div>
                    <div style="font-size:1.6rem; font-weight:800; color:#0F172A;">{val_counts[key]}</div>
                    <div style="font-size:0.75rem; color:#475569;">Plan: {plan_units[key]} elementos</div>
                    <span class="badge-amber">{status}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Cálculo dinámico en vivo de la zona conforme a Sección 5
    live_calc = calculate_zone_progress(val_counts, plan_units, st.session_state.weights)
    
    st.markdown(f"""
    <div style="background:#EFF6FF; border-left: 4px solid #3B82F6; padding:12px 18px; border-radius:6px; margin: 12px 0;">
        <span style="font-size:1rem; color:#1E40AF; font-weight:700;">
            Avance recalculado de {current_z}: <b>{live_calc['progress_pct']:.1f}%</b> según los conteos de esta revisión
        </span>
    </div>
    """, unsafe_allow_html=True)

    # BOTONES DE ACCIÓN ERGONÓMICA EN LA PARTE BAJA (WIRE FRAME 7B)
    # "Aprobar verdes" (alcance pulgar), "Corregir revisar ⚠", "Rechazar foto (repetir)"
    st.markdown("### 👆 Decisiones del Inspector Técnico (HITL)")
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        if st.button(
            "✅ Aprobar rociadores candidatos ≥ 0.80",
            type="primary",
            use_container_width=True,
            disabled=high_counts['rociadores'] == 0
        ):
            component = 'rociadores'
            new_value = val_counts[component]
            old_value = z_data['validated'].get(component, 0)
            if old_value != new_value:
                st.session_state.audit.log_action(
                    user=st.session_state.user_name,
                    action="Aprobación de detección",
                    zone_id=current_z,
                    target_component=component,
                    old_val=old_value,
                    new_val=new_value,
                    note=f"Aprobado por confianza ≥ 0.80 · {active_inspection['name']}"
                )
            z_data['validated'][component] = new_value
            z_data['needs_review'] = False
            st.session_state.inspected_zones.add(current_z)
            st.success(f"Conteos de {current_z} aprobados y avance actualizado.")
            navigate_to("c_avance")

    with btn_col2:
        with st.popover("✏️ Corregir / Revisar ⚠", use_container_width=True):
            st.markdown(f"#### Validación manual de componentes PCI ({current_z})")
            st.caption("Usa las mismas unidades definidas en el plan de esta zona. La prueba hidráulica requiere constatación del ITO.")

            c_pipe = st.number_input("Tramos de tubería instalados:", min_value=0, max_value=500, value=int(val_counts['tuberia']))
            c_support = st.number_input("Soportes y colgadores instalados:", min_value=0, max_value=500, value=int(val_counts['soportes']))
            c_sprinkler = st.number_input("Rociadores instalados:", min_value=0, max_value=500, value=int(val_counts['rociadores']))
            c_valve = st.number_input("Válvulas de control instaladas:", min_value=0, max_value=500, value=int(val_counts['valvula']))
            c_test = st.number_input("Prueba hidráulica aprobada (0 o 1):", min_value=0, max_value=1, value=int(val_counts['prueba_hidraulica']))

            correc_note = st.text_input("Motivo de corrección (para auditoría):", "Validación de instalación PCI en terreno")

            if st.button("💾 Guardar Corrección y Recalcular", type="primary", use_container_width=True):
                # Registrar auditoría de cada campo cambiado
                for comp, old_v, new_v in [
                    ('tuberia', z_data['validated']['tuberia'], c_pipe),
                    ('soportes', z_data['validated']['soportes'], c_support),
                    ('rociadores', z_data['validated']['rociadores'], c_sprinkler),
                    ('valvula', z_data['validated']['valvula'], c_valve),
                    ('prueba_hidraulica', z_data['validated']['prueba_hidraulica'], c_test),
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
                val_counts.update({
                    'tuberia': c_pipe,
                    'soportes': c_support,
                    'rociadores': c_sprinkler,
                    'valvula': c_valve,
                    'prueba_hidraulica': c_test,
                })
                z_data['validated'].update(val_counts)
                z_data['needs_review'] = False
                st.session_state.inspected_zones.add(current_z)
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
            st.session_state.active_inspection = None
            st.warning(f"Foto de {current_z} rechazada. Carga una nueva toma para continuar.")
            navigate_to("a_subir")

    # Botón directo para pasar a la siguiente pantalla
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("➡️ Ir al Panel de Avance Consolidado", use_container_width=True):
        navigate_to("c_avance")


# ======================================================================================
# PANTALLA 7 (C): PANEL DE AVANCE & DESVIACIONES (F-06, RF-07, WIREFRAME 7C)
# ======================================================================================
elif st.session_state.current_screen == "c_avance":
    st.markdown(f"## 📊 Pantalla (c): Avance · {st.session_state.current_level}")
    st.caption(f"{st.session_state.current_project} · Nivel {st.session_state.current_level}")
    st.info("Las zonas aún no inspeccionadas conservan los datos de demostración. Carga y valida fotos reales para actualizar el avance de cada zona.")

    # Lista de zonas evaluadas
    zones_list = []
    plan_week_pct = PROJECTS_DATA["Torre Norte"]["levels"]["Nivel 4"]["plan_week_pct"]
    for zk, zv in st.session_state.zones_state.items():
        zones_list.append({
            'name': zk,
            'plan': zv['plan'],
            'validated': zv['validated'],
            'coverage': zv['coverage'],
            'needs_review': zv['needs_review'],
            'plan_week_pct': plan_week_pct
        })

    level_eval = calculate_level_progress(zones_list, st.session_state.weights)
    level_real = level_eval['level_progress_pct']
    level_plan = plan_week_pct
    level_dev = round(level_real - level_plan, 1)
    reviewed_zones = sum(zone['name'] in st.session_state.inspected_zones for zone in level_eval['zones'])

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
            <div style="font-size: 0.85rem; color:#64748B; font-weight:600;">ZONAS INSPECCIONADAS EN ESTA SESIÓN</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #059669; margin: 6px 0;">{reviewed_zones} / {len(level_eval['zones'])} zonas</div>
            <span class="badge-green">Conteos confirmados</span>
        </div>
        """, unsafe_allow_html=True)

    with col_kpi3:
        st.markdown(f"""
        <div class="aec-card" style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="font-size: 0.85rem; color:#64748B; font-weight:600;">UNIDADES PCI PLANIFICADAS</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #0284C7; margin: 6px 0;">{level_eval['total_plan_units']} unid.</div>
            <span style="font-size: 0.8rem; color:#64748B;">En {len(level_eval['zones'])} zonas</span>
        </div>
        """, unsafe_allow_html=True)

    # Alertas automáticas de desviación por elemento o zona.
    st.markdown("### ⚠️ Semáforo de desviaciones en instalación PCI")
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
        st.success("✅ Todos los elementos están dentro del umbral de tolerancia planificado (< 5 pp).")

    st.markdown("### 🚿 Desglose de avance de rociadores y componentes PCI por zona")
    
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
                inspection = st.session_state.active_inspection
                has_photo_for_zone = inspection is not None and inspection['zone'] == z['name']
                button_label = "Revisar foto" if has_photo_for_zone else "Cargar foto"
                if st.button(button_label, key=f"btn_zone_{z['name']}", use_container_width=True):
                    st.session_state.current_zone = z['name']
                    navigate_to("b_revision" if has_photo_for_zone else "a_subir")

    # Tabla de ponderación de la zona seleccionada
    with st.expander("🔬 Ver matriz de ponderación de la zona"):
        st.write(r"Fórmula: $A(z) = \sum w(c) \cdot p(c,z)$")
        zone_data = next(z for z in level_eval['zones'] if z['name'] == st.session_state.current_zone)
        df_zone = pd.DataFrame(zone_data['components'])
        df_zone.columns = ["Clave", "Componente", "Peso (w)", "Validado", "Plan", "Ratio p(c,z)", "Aporte (w·p)"]
        st.dataframe(df_zone, use_container_width=True)

    # BOTÓN PRINCIPAL WIREFRAME 7C: "Generar reporte"
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📑 Generar Reporte Semanal", type="primary", use_container_width=True):
        navigate_to("d_reporte")


# ======================================================================================
# PANTALLA 7 (D): REPORTE SEMANAL & EXPORTACIÓN PDF (F-07, RF-08, WIREFRAME 7D)
# ======================================================================================
elif st.session_state.current_screen == "d_reporte":
    report_week = datetime.now().isocalendar().week
    st.markdown(f"## 📄 Reporte de avance · Semana {report_week}")
    st.caption("Consolidación ejecutiva para Administrador de Obra, Mandante e ITO")

    # Lista de zonas evaluadas
    zones_list = []
    plan_week_pct = PROJECTS_DATA["Torre Norte"]["levels"]["Nivel 4"]["plan_week_pct"]
    for zk, zv in st.session_state.zones_state.items():
        zones_list.append({
            'name': zk,
            'plan': zv['plan'],
            'validated': zv['validated'],
            'coverage': zv['coverage'],
            'needs_review': zv['needs_review'],
            'plan_week_pct': plan_week_pct
        })
    level_eval = calculate_level_progress(zones_list, st.session_state.weights)
    audit_entries = st.session_state.audit.get_logs_as_dicts()
    inspected_zone_count = len(st.session_state.inspected_zones)
    level_eval['inspected_zones_this_session'] = inspected_zone_count
    level_eval['uses_sample_data'] = inspected_zone_count < len(level_eval['zones'])

    # Generación del PDF con ReportLab
    pdf_bytes = generate_weekly_pdf_report(
        project_name=st.session_state.current_project,
        level_name=st.session_state.current_level,
        week_number=report_week,
        ito_name=st.session_state.user_name,
        level_data=level_eval,
        audit_logs=audit_entries,
        notes=""
    )

    # Resumen construido únicamente con los datos del estado actual.
    st.info("Este reporte incluye datos precargados de demostración para zonas no inspeccionadas. La fotografía activa no se conserva como historial al cerrar la sesión.")
    st.markdown(f"""
    <div class="aec-card" style="border: 2px solid #0284C7; padding: 24px; background: #F8FAFC;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #CBD5E1; padding-bottom: 12px; margin-bottom: 16px;">
            <div>
                <h3 style="margin: 0; color: #0F172A;">Reporte de avance · Semana {report_week}</h3>
                <span style="color: #64748B; font-size: 0.9rem;">Obra: <b>{st.session_state.current_project}</b> | Nivel: <b>{st.session_state.current_level}</b></span>
            </div>
            <span class="badge-green" style="font-size: 0.95rem; padding: 6px 14px;">
                {inspected_zone_count}/{len(level_eval['zones'])} zonas inspeccionadas
            </span>
        </div>
        <ul style="font-size: 1rem; color: #1E293B; line-height: 1.8;">
            <li><b>Avance real ponderado:</b> {level_eval['level_progress_pct']:.1f}% (Plan semanal: {plan_week_pct:.1f}%)</li>
            <li><b>Zonas incluidas:</b> {len(level_eval['zones'])}</li>
            <li><b>Registros de auditoría:</b> {len(audit_entries)} acciones en esta sesión</li>
            <li><b>Firmas:</b> Este PDF no cuenta con firma electrónica.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # BOTONES DE ACCIÓN WIREFRAME 7D: "Descargar PDF" y "Compartir"
    col_d1, col_d2, col_d3 = st.columns([2, 1, 1])
    with col_d1:
        st.download_button(
            label="📥 Descargar reporte PDF",
            data=pdf_bytes,
            file_name=f"Reporte_Enfierradura_BuildVision_Sem{report_week}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    with col_d2:
        if st.button("📤 Compartir Reporte", use_container_width=True):
            st.info("Descarga el PDF y compártelo desde tu dispositivo. No se genera un enlace externo.")

    with col_d3:
        if st.button("🔄 Nueva Inspección", use_container_width=True):
            navigate_to("a_subir")

    # VISTA PREVIA DETALLADA DEL INFORME
    st.markdown("---")
    st.markdown("### 📋 Vista Previa de Tablas del Reporte")

    t1, t2, t3 = st.tabs(["📊 Matriz de Avance por Zona", "🛡️ Registro de Auditoría HITL", "📷 Foto activa"])
    
    with t1:
        table_rows = []
        for z in level_eval['zones']:
            table_rows.append({
                'Elemento / Zona': z['name'],
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
            st.info("Aún no hay acciones de revisión o corrección en esta sesión.")

    with t3:
        st.markdown("#### Fotografía de la inspección activa")
        active_inspection = st.session_state.active_inspection
        if active_inspection is not None:
            current_image = Image.open(io.BytesIO(active_inspection["image"])).convert("RGB")
            annotated = draw_detections(current_image, active_inspection["detections"])
            st.image(annotated, caption=f"{active_inspection['zone']} · {active_inspection['name']}", use_container_width=True)
        else:
            st.info("No hay una fotografía activa para mostrar.")

    # El prototipo no implementa firma electrónica.
    st.markdown("---")
    st.caption(f"Responsable indicado: {st.session_state.user_name}. Pendiente implementar firma electrónica y persistencia de reportes.")
