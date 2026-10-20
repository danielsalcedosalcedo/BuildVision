"""
BuildVision AI - Módulo de Control de Calidad de Fotos (RF-02)
Valida resolución mínima (>= 8 MP / 1280px), nitidez (varianza Laplaciano),
y detecta fotos borrosas antes de consumir inferencia de IA.
"""
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image

def analyze_photo_quality(image: Image.Image) -> Dict[str, Any]:
    """
    Aplica los criterios de la Sección 4 y RF-02:
    - Resolución mínima recomendada: >= 8 Megapíxeles (mínimo 1280 px de ancho)
    - Nitidez: varianza del Laplaciano sobre la imagen en escala de grises
    """
    width, height = image.size
    total_pixels = width * height
    mp = total_pixels / 1_000_000.0

    # Convertir a escala de grises y calcular Laplaciano rápido con numpy
    gray_img = image.convert('L')
    # Para optimizar velocidad, si la imagen es gigante la reducimos para el test de nitidez
    thumb = gray_img.resize((min(width, 1024), int(min(width, 1024) * height / width)))
    arr = np.array(thumb, dtype=np.float32)

    # Kernel Laplaciano 3x3: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
    # Cálculo eficiente de gradiente discreto 2D
    laplacian = (
        np.roll(arr, 1, axis=0) +
        np.roll(arr, -1, axis=0) +
        np.roll(arr, 1, axis=1) +
        np.roll(arr, -1, axis=1) -
        4 * arr
    )
    # Cortar bordes para evitar artefactos circulares
    laplacian_inner = laplacian[2:-2, 2:-2]
    variance = float(np.var(laplacian_inner))

    # Criterios de calidad según documento
    is_sharp = variance >= 85.0
    is_adequate_res = (width >= 1280 or height >= 1280) and mp >= 2.0
    is_gold_res = mp >= 8.0

    warnings = []
    if not is_sharp:
        warnings.append("Aviso de nitidez: Imagen potencialmente movida o desenfocada. Se recomienda repetir la toma con luz adecuada.")
    if not is_adequate_res:
        warnings.append(f"Resolución baja ({width}x{height}, {mp:.1f} MP). Se exige mínimo 1280px para detectar rociadores pequeños.")

    passed = is_sharp and is_adequate_res

    return {
        'passed': passed,
        'width': width,
        'height': height,
        'megapixels': round(mp, 2),
        'sharpness_variance': round(variance, 1),
        'is_sharp': is_sharp,
        'is_adequate_res': is_adequate_res,
        'is_gold_res': is_gold_res,
        'warnings': warnings,
        'status_label': 'Óptima' if (is_sharp and is_gold_res) else ('Aceptable con advertencia' if passed else 'Rechazada por calidad')
    }
