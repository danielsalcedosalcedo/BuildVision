"""
BuildVision AI - Motor de Inferencia y Anotación Visual (RF-03, Sección 5)
Detector de componentes de la red de rociadores contra incendio.
"""
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont


CLASS_METADATA = {
    'rociador_instalado': {
        'display': 'Rociador instalado',
        'short': 'Rociador',
        'color_high': '#10B981',
        'color_mid': '#F59E0B',
        'color_low': '#EF4444',
        'component_key': 'rociadores',
    },
    'tapon_de_rociador': {
        'display': 'Tapón salida pendiente',
        'short': 'Tapón',
        'color_high': '#F59E0B',
        'color_mid': '#D97706',
        'color_low': '#DC2626',
        'component_key': 'tapones',
    },
    'tuberia': {
        'display': 'Tramo de tubería',
        'short': 'Tubería',
        'color_high': '#06B6D4',
        'color_mid': '#0284C7',
        'color_low': '#EF4444',
        'component_key': 'tuberia',
    },
    'soporte': {
        'display': 'Soporte / Colgador',
        'short': 'Soporte',
        'color_high': '#3B82F6',
        'color_mid': '#2563EB',
        'color_low': '#EF4444',
        'component_key': 'soportes',
    },
    'valvula_de_control': {
        'display': 'Válvula de control',
        'short': 'Válvula',
        'color_high': '#8B5CF6',
        'color_mid': '#7C3AED',
        'color_low': '#EF4444',
        'component_key': 'valvula',
    },
}


def get_status_info(confidence: float) -> Tuple[str, str, str]:
    if confidence >= 0.80:
        return 'ALTA (Preseleccionada)', '#10B981', '✓'
    if confidence >= 0.40:
        return 'MEDIA (Revisión requerida)', '#F59E0B', '⚠'
    return 'BAJA (Descartada/Dudosa)', '#EF4444', '✗'


def draw_detections(
    image: Image.Image,
    detections: List[Dict[str, Any]],
    show_labels: bool = True,
    filter_status: str = 'all',
) -> Image.Image:
    annotated = image.copy().convert('RGBA')
    draw = ImageDraw.Draw(annotated)
    width, height = annotated.size

    try:
        font = ImageFont.truetype("arial.ttf", size=max(12, int(height * 0.018)))
    except OSError:
        font = ImageFont.load_default()

    for detection in detections:
        confidence = detection['confidence']
        _, confidence_color, icon = get_status_info(confidence)
        if filter_status == 'high' and confidence < 0.80:
            continue
        if filter_status == 'review' and not 0.40 <= confidence < 0.80:
            continue

        box = detection['box']
        if max(box) <= 1.0:
            x1, y1, x2, y2 = (
                int(box[0] * width),
                int(box[1] * height),
                int(box[2] * width),
                int(box[3] * height),
            )
        else:
            x1, y1, x2, y2 = (int(value) for value in box)

        metadata = CLASS_METADATA.get(detection['class'], {'short': detection['class']})
        draw.rectangle([x1, y1, x2, y2], outline=confidence_color, width=3)
        rgb = tuple(int(confidence_color[index:index + 2], 16) for index in (1, 3, 5))
        draw.rectangle([x1, y1, x2, y2], fill=(*rgb, 25))

        if show_labels:
            label = f"{metadata['short']} {confidence:.2f} {icon}"
            text_box = draw.textbbox((x1, max(0, y1 - 22)), label, font=font)
            tag_height = text_box[3] - text_box[1] + 6
            tag_width = text_box[2] - text_box[0] + 10
            tag_y = max(0, y1 - tag_height - 2)
            draw.rectangle(
                [x1, tag_y, min(width, x1 + tag_width), tag_y + tag_height],
                fill=confidence_color,
            )
            draw.text((x1 + 5, tag_y + 2), label, fill=(255, 255, 255, 255), font=font)

    return annotated.convert('RGB')


def generate_mock_detections_for_zone(
    zone_id: str,
    image_size: Tuple[int, int] = (1280, 850),
) -> List[Dict[str, Any]]:
    """Genera detecciones sintéticas PCI únicamente para pruebas de interfaz."""
    del image_size
    classes = (
        ['tuberia', 'soporte', 'rociador_instalado', 'tapon_de_rociador', 'valvula_de_control']
        if zone_id == 'Vano C-D'
        else ['tuberia', 'soporte', 'rociador_instalado']
    )
    return [
        {
            'id': f'demo-{index + 1}',
            'class': class_name,
            'confidence': 0.88,
            'box': [0.08 + index * 0.16, 0.2, 0.2 + index * 0.16, 0.72],
        }
        for index, class_name in enumerate(classes)
    ]
