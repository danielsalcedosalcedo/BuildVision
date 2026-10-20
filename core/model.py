"""
BuildVision AI - Motor de Inferencia y Anotación Visual (RF-03, Sección 5)
Detecta 5 clases de la red de rociadores contra incendio:
1. rociador_instalado
2. tapon_de_rociador (salida pendiente)
3. tuberia (tramo)
4. soporte (colgador / antisísmico)
5. valvula_de_control

Implementa semáforo de confianza:
- >= 0.80: Verde (Pre-aprobado para lote)
- 0.40 - 0.79: Ámbar (Revisión obligatoria del ITO)
- < 0.40: Rojo / Descartado (No suma al avance salvo aprobación explícita)
"""
from typing import List, Dict, Any, Tuple
import math
from PIL import Image, ImageDraw, ImageFont

CLASS_METADATA = {
    'rociador_instalado': {
        'display': 'Rociador instalado',
        'short': 'Rociador',
        'color_high': '#10B981',   # Verde esmeralda
        'color_mid': '#F59E0B',    # Ámbar
        'color_low': '#EF4444',    # Rojo
        'component_key': 'rociadores'
    },
    'tapon_de_rociador': {
        'display': 'Tapón salida pendiente',
        'short': 'Tapón ⚠',
        'color_high': '#F59E0B',
        'color_mid': '#D97706',
        'color_low': '#DC2626',
        'component_key': 'tapones'
    },
    'tuberia': {
        'display': 'Tramo de tubería',
        'short': 'Tubería',
        'color_high': '#06B6D4',   # Cian
        'color_mid': '#0284C7',
        'color_low': '#EF4444',
        'component_key': 'tuberia'
    },
    'soporte': {
        'display': 'Soporte / Colgador',
        'short': 'Soporte',
        'color_high': '#3B82F6',   # Azul
        'color_mid': '#2563EB',
        'color_low': '#EF4444',
        'component_key': 'soportes'
    },
    'valvula_de_control': {
        'display': 'Válvula de control',
        'short': 'Válvula',
        'color_high': '#8B5CF6',   # Púrpura
        'color_mid': '#7C3AED',
        'color_low': '#EF4444',
        'component_key': 'valvula'
    }
}

def get_status_info(confidence: float) -> Tuple[str, str, str]:
    """
    Retorna (categoría, color, ícono) según los umbrales de la Sección 5
    """
    if confidence >= 0.80:
        return 'ALTA (Preseleccionada)', '#10B981', '✓'
    elif confidence >= 0.40:
        return 'MEDIA (Revisión requerida)', '#F59E0B', '⚠'
    else:
        return 'BAJA (Descartada/Dudosa)', '#EF4444', '✗'

def draw_detections(
    image: Image.Image,
    detections: List[Dict[str, Any]],
    show_labels: bool = True,
    filter_status: str = 'all'
) -> Image.Image:
    """
    Dibuja bounding boxes estilizadas de alto contraste aptas para terreno (AEC).
    """
    annotated = image.copy().convert('RGBA')
    draw = ImageDraw.Draw(annotated)
    w, h = annotated.size

    # Intentar cargar fuente estándar legible
    try:
        font = ImageFont.truetype("arial.ttf", size=max(12, int(h * 0.018)))
    except Exception:
        font = ImageFont.load_default()

    for det in detections:
        conf = det['confidence']
        category, cat_color, icon = get_status_info(conf)

        if filter_status == 'high' and conf < 0.80:
            continue
        if filter_status == 'review' and (conf >= 0.80 or conf < 0.40):
            continue

        box = det['box']  # [x1, y1, x2, y2] en coordenadas absolutas o normalizadas
        if max(box) <= 1.0:
            x1, y1, x2, y2 = int(box[0]*w), int(box[1]*h), int(box[2]*w), int(box[3]*h)
        else:
            x1, y1, x2, y2 = [int(v) for v in box]

        cls_key = det['class']
        meta = CLASS_METADATA.get(cls_key, {
            'short': cls_key,
            'color_high': cat_color,
            'color_mid': cat_color,
            'color_low': cat_color
        })

        color = cat_color

        # Caja delimitadora con grosor táctil
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        # Relleno sutil semi-transparente
        # Extraer RGB
        hex_val = color.lstrip('#')
        rgb = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
        draw.rectangle([x1, y1, x2, y2], fill=(rgb[0], rgb[1], rgb[2], 25))

        if show_labels:
            label_text = f"{meta['short']} {conf:.2f} {icon}"
            
            # Cálculo de caja para el tag de texto
            text_bbox = draw.textbbox((x1, max(0, y1 - 22)), label_text, font=font)
            tag_x1, tag_y1, tag_x2, tag_y2 = text_bbox
            tag_w = tag_x2 - tag_x1 + 10
            tag_h = tag_y2 - tag_y1 + 6
            
            box_tag_y1 = max(0, y1 - tag_h - 2)
            box_tag_y2 = box_tag_y1 + tag_h
            box_tag_x2 = min(w, x1 + tag_w)

            # Fondo sólido del tag con color distintivo
            draw.rectangle([x1, box_tag_y1, box_tag_x2, box_tag_y2], fill=color)
            draw.text((x1 + 5, box_tag_y1 + 2), label_text, fill=(255, 255, 255, 255), font=font)

    return annotated.convert('RGB')

def generate_mock_detections_for_zone(zone_id: str, image_size: Tuple[int, int] = (1280, 850)) -> List[Dict[str, Any]]:
    """
    Genera detecciones coherentes con el caso de uso y el Caso Dorado CP-05
    """
    w, h = image_size
    detections = []

    if zone_id == 'Vano C-D':
        # Caso Dorado CP-05 exacto:
        # 12 tramos de tubería (confianza 0.85 - 0.94)
        for i in range(12):
            x1 = 0.05 + (i % 6) * 0.15
            y1 = 0.18 + (i // 6) * 0.40
            detections.append({
                'id': f"det-tub-{i+1}",
                'class': 'tuberia',
                'confidence': 0.88 if i % 2 == 0 else 0.92,
                'box': [x1, y1, min(0.96, x1 + 0.14), y1 + 0.06]
            })

        # 14 soportes confirmados
        for i in range(14):
            x1 = 0.08 + (i % 7) * 0.13
            y1 = 0.14 + (i // 7) * 0.40
            detections.append({
                'id': f"det-sop-{i+1}",
                'class': 'soporte',
                'confidence': 0.85 if i != 3 else 0.41,  # 1 soporte con baja confianza como en wireframe (0.41)
                'box': [x1, y1, x1 + 0.04, y1 + 0.10]
            })

        # 15 rociadores instalados (13 con alta confianza >= 0.80, 2 con revisión 0.62)
        for i in range(15):
            x1 = 0.09 + (i % 5) * 0.18
            y1 = 0.25 + (i // 5) * 0.22
            conf = 0.93 if i == 0 else (0.88 if i == 1 else (0.62 if i == 2 else 0.89))
            detections.append({
                'id': f"det-roc-{i+1}",
                'class': 'rociador_instalado',
                'confidence': conf,
                'box': [x1, y1, x1 + 0.05, y1 + 0.07]
            })

        # 3 tapones de rociador (salidas con tapón ⚠ como en CP-05 y wireframe 7b)
        for i in range(3):
            x1 = 0.35 + i * 0.20
            y1 = 0.72
            detections.append({
                'id': f"det-tap-{i+1}",
                'class': 'tapon_de_rociador',
                'confidence': 0.68,
                'box': [x1, y1, x1 + 0.045, y1 + 0.06]
            })

        # 1 válvula de control
        detections.append({
            'id': "det-val-1",
            'class': 'valvula_de_control',
            'confidence': 0.95,
            'box': [0.82, 0.22, 0.94, 0.42]
        })

    else:
        # Generación sintética genérica para otros vanos
        for i in range(8):
            x1 = 0.1 + (i * 0.10)
            detections.append({
                'id': f"det-gen-tub-{i}",
                'class': 'tuberia',
                'confidence': 0.91,
                'box': [x1, 0.25, x1 + 0.09, 0.31]
            })
        for i in range(10):
            x1 = 0.1 + (i * 0.08)
            detections.append({
                'id': f"det-gen-roc-{i}",
                'class': 'rociador_instalado',
                'confidence': 0.87 if i % 2 == 0 else 0.65,
                'box': [x1, 0.32, x1 + 0.04, 0.38]
            })
        for i in range(10):
            x1 = 0.11 + (i * 0.08)
            detections.append({
                'id': f"det-gen-sop-{i}",
                'class': 'soporte',
                'confidence': 0.84,
                'box': [x1, 0.20, x1 + 0.03, 0.25]
            })

    return detections
