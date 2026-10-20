"""
BuildVision AI - Datos de Prueba y Casos de Obra (CP-05, CP-09, CP-10)
Estructura de proyectos, niveles, zonas, planes de unidades y fotos.
"""
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont

PROJECTS_DATA = {
    "Torre Norte": {
        "id": "PRJ-TN",
        "name": "Torre Norte - Parque Empresarial",
        "levels": {
            "Nivel 4": {
                "id": "NIV-04",
                "name": "Nivel 4 (Piso Tipo Oficinas)",
                "plan_week_pct": 85.0,
                "zones": {
                    "Vano C-D": {
                        "id": "ZON-CD",
                        "name": "Vano C-D",
                        "coverage": "Total",
                        "needs_review": False,
                        "plan": {
                            "tuberia": 12,
                            "soportes": 18,
                            "rociadores": 24,
                            "valvula": 1,
                            "prueba_hidraulica": 1
                        },
                        "validated": {
                            "tuberia": 12,
                            "soportes": 14,
                            "rociadores": 15,
                            "valvula": 1,
                            "prueba_hidraulica": 0
                        },
                        "detected_raw": {
                            "tuberia": 12,
                            "soportes": 14,
                            "rociadores": 15,
                            "tapones": 3,
                            "valvula": 1,
                            "prueba_hidraulica": 0
                        },
                        "photo_meta": {
                            "code": "IMG_N4_CD_02.jpg",
                            "resolution": "4032 x 3024 (12.2 MP)",
                            "sharpness": "158.4 (Nítida)",
                            "date": "2026-10-18 10:42",
                            "author": "Daniel Salcedo (ITO)",
                            "quality_passed": True
                        }
                    },
                    "Vano D-E": {
                        "id": "ZON-DE",
                        "name": "Vano D-E",
                        "coverage": "Total",
                        "needs_review": False,
                        "plan": {
                            "tuberia": 12,
                            "soportes": 18,
                            "rociadores": 24,
                            "valvula": 1,
                            "prueba_hidraulica": 1
                        },
                        "validated": {
                            "tuberia": 12,
                            "soportes": 18,
                            "rociadores": 22,
                            "valvula": 1,
                            "prueba_hidraulica": 0
                        },
                        "detected_raw": {
                            "tuberia": 12,
                            "soportes": 18,
                            "rociadores": 22,
                            "tapones": 2,
                            "valvula": 1,
                            "prueba_hidraulica": 0
                        },
                        "photo_meta": {
                            "code": "IMG_N4_DE_01.jpg",
                            "resolution": "4000 x 3000 (12.0 MP)",
                            "sharpness": "142.1 (Nítida)",
                            "date": "2026-10-18 11:05",
                            "author": "Daniel Salcedo (ITO)",
                            "quality_passed": True
                        }
                    },
                    "Vano E-F": {
                        "id": "ZON-EF",
                        "name": "Vano E-F",
                        "coverage": "Parcial",
                        "needs_review": False,
                        "plan": {
                            "tuberia": 12,
                            "soportes": 18,
                            "rociadores": 24,
                            "valvula": 1,
                            "prueba_hidraulica": 1
                        },
                        "validated": {
                            "tuberia": 9,
                            "soportes": 11,
                            "rociadores": 12,
                            "valvula": 0,
                            "prueba_hidraulica": 0
                        },
                        "detected_raw": {
                            "tuberia": 9,
                            "soportes": 11,
                            "rociadores": 12,
                            "tapones": 5,
                            "valvula": 0,
                            "prueba_hidraulica": 0
                        },
                        "photo_meta": {
                            "code": "IMG_N4_EF_01.jpg",
                            "resolution": "3840 x 2160 (8.3 MP)",
                            "sharpness": "128.7 (Nítida)",
                            "date": "2026-10-18 11:30",
                            "author": "Daniel Salcedo (ITO)",
                            "quality_passed": True
                        }
                    },
                    "Vano F-G": {
                        "id": "ZON-FG",
                        "name": "Vano F-G",
                        "coverage": "Total",
                        "needs_review": False,
                        "plan": {
                            "tuberia": 12,
                            "soportes": 18,
                            "rociadores": 24,
                            "valvula": 1,
                            "prueba_hidraulica": 1
                        },
                        "validated": {
                            "tuberia": 10,
                            "soportes": 13,
                            "rociadores": 16,
                            "valvula": 0,
                            "prueba_hidraulica": 0
                        },
                        "detected_raw": {
                            "tuberia": 10,
                            "soportes": 13,
                            "rociadores": 16,
                            "tapones": 4,
                            "valvula": 0,
                            "prueba_hidraulica": 0
                        },
                        "photo_meta": {
                            "code": "IMG_N4_FG_01.jpg",
                            "resolution": "4032 x 3024 (12.2 MP)",
                            "sharpness": "135.0 (Nítida)",
                            "date": "2026-10-18 11:55",
                            "author": "Daniel Salcedo (ITO)",
                            "quality_passed": True
                        }
                    },
                    "Vano G-H": {
                        "id": "ZON-GH",
                        "name": "Vano G-H",
                        "coverage": "Parcial",
                        "needs_review": True,
                        "plan": {
                            "tuberia": 12,
                            "soportes": 18,
                            "rociadores": 24,
                            "valvula": 1,
                            "prueba_hidraulica": 1
                        },
                        "validated": {
                            "tuberia": 6,
                            "soportes": 7,
                            "rociadores": 8,
                            "valvula": 0,
                            "prueba_hidraulica": 0
                        },
                        "detected_raw": {
                            "tuberia": 6,
                            "soportes": 7,
                            "rociadores": 8,
                            "tapones": 8,
                            "valvula": 0,
                            "prueba_hidraulica": 0
                        },
                        "photo_meta": {
                            "code": "IMG_N4_GH_01.jpg",
                            "resolution": "2400 x 1800 (4.3 MP)",
                            "sharpness": "72.4 (Aviso de Nitidez)",
                            "date": "2026-10-18 12:20",
                            "author": "Daniel Salcedo (ITO)",
                            "quality_passed": False
                        }
                    }
                }
            },
            "Nivel 1": {
                "id": "NIV-01",
                "name": "Nivel 1 (Lobby y Accesos)",
                "plan_week_pct": 100.0,
                "zones": {}
            }
        }
    },
    "Hospital Regional": {
        "id": "PRJ-HR",
        "name": "Hospital Regional - Sector Poniente",
        "levels": {}
    }
}

def create_synthetic_construction_photo(
    width: int = 1280,
    height: int = 800,
    zone_label: str = "Vano C-D - Nivel 4"
) -> Image.Image:
    """
    Genera una imagen técnica de obra realista que simula el cielo de hormigón a la vista,
    la tubería roja ranurada contra incendio (NFPA 13), colgadores y rociadores.
    """
    img = Image.new('RGB', (width, height), color=(68, 72, 78))
    draw = ImageDraw.Draw(img)

    # Fondo textura hormigón / losa nervada
    for y in range(0, height, 120):
        draw.line([(0, y), (width, y)], fill=(55, 59, 64), width=3)
    for x in range(0, width, 180):
        draw.line([(x, 0), (x, height)], fill=(55, 59, 64), width=2)

    # Ductos de ventilación HVAC de fondo (gris metalizado)
    draw.rectangle([0, int(height*0.55), width, int(height*0.75)], fill=(120, 125, 132), outline=(95, 100, 106), width=3)
    for sx in range(40, width, 90):
        draw.line([(sx, int(height*0.55)), (sx, int(height*0.75))], fill=(95, 100, 106), width=2)

    # Tubería principal contra incendio (Rojo Bermellón NFPA)
    pipe_y1 = int(height * 0.32)
    pipe_y2 = int(height * 0.40)
    draw.rectangle([0, pipe_y1, width, pipe_y2], fill=(195, 35, 30), outline=(145, 20, 18), width=3)
    # Bridas y uniones ranuradas Victaulic
    for bx in range(120, width, 160):
        draw.rectangle([bx - 6, pipe_y1 - 4, bx + 6, pipe_y2 + 4], fill=(155, 25, 22), outline=(100, 15, 12), width=2)

    # Soportes colgadores tipo pera fijados a la losa
    for sx in range(100, width - 80, 150):
        draw.line([(sx, 0), (sx, pipe_y1)], fill=(180, 185, 192), width=4)
        draw.ellipse([sx - 10, pipe_y1 - 5, sx + 10, pipe_y2 + 5], outline=(200, 205, 212), width=3)

    # Ramales secundarios y Rociadores colgantes (pendant)
    for rx in range(110, width - 70, 110):
        drop_top = pipe_y2
        drop_bottom = pipe_y2 + 45
        draw.line([(rx, drop_top), (rx, drop_bottom)], fill=(185, 30, 25), width=6)
        # Cabeza de rociador en bronce/cromo
        draw.ellipse([rx - 8, drop_bottom, rx + 8, drop_bottom + 16], fill=(218, 165, 32), outline=(180, 130, 20), width=2)
        # Deflector
        draw.polygon([(rx - 12, drop_bottom + 18), (rx + 12, drop_bottom + 18), (rx, drop_bottom + 14)], fill=(200, 150, 25))

    # Válvula de mariposa con volante de supervisión al extremo derecho
    valv_x = int(width * 0.88)
    draw.rectangle([valv_x - 18, pipe_y1 - 8, valv_x + 18, pipe_y2 + 8], fill=(230, 180, 20), outline=(180, 130, 10), width=3)
    draw.ellipse([valv_x - 15, pipe_y1 - 35, valv_x + 15, pipe_y1 - 5], outline=(220, 30, 20), width=4)

    # Overlay sutil de metadatos de cámara en esquina
    try:
        font = ImageFont.truetype("arial.ttf", size=18)
    except Exception:
        font = ImageFont.load_default()

    draw.rectangle([15, 15, 360, 65], fill=(20, 24, 30, 200))
    draw.text((25, 20), f"CAM-FIELD · {zone_label}", fill=(240, 240, 240), font=font)
    draw.text((25, 42), "Red de Rociadores PCI · NFPA 13", fill=(160, 170, 180), font=font)

    return img
