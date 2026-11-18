"""
BuildVision AI - Inferencia real (RF-03, RNF-01)
Dos vías para obtener detecciones reales sobre una foto:
  1) run_inference(): ejecuta un modelo Ultralytics YOLO (weights/best.pt) en esta máquina.
  2) detections_from_json(): importa detecciones generadas fuera de la app con el mismo contrato.
"""
from __future__ import annotations

import json
import time
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent

APP_CLASSES = ['rociador_instalado', 'tapon_de_rociador', 'tuberia', 'soporte', 'valvula_de_control']

# clase del modelo -> clave de componente del motor de avance
CLASS_TO_COMPONENT: Dict[str, str] = {
    'rociador_instalado': 'rociadores',
    'tapon_de_rociador': 'tapones',
    'tuberia': 'tuberia',
    'soporte': 'soportes',
    'valvula_de_control': 'valvula',
}

_ALIASES = {
    'rociador_instalado': ['rociador', 'rociadores', 'sprinkler', 'sprinkler_head', 'fire_sprinkler',
                           'fire_sprinkler_head', 'sprinkler_instalado', 'cabezal_rociador'],
    'tapon_de_rociador': ['tapon', 'tapones', 'sprinkler_plug', 'sprinkler_cap', 'plug'],
    'tuberia': ['tuberias', 'tramo', 'pipe', 'fire_pipe', 'pipe_segment', 'tramo_de_tuberia'],
    'soporte': ['soportes', 'colgador', 'hanger', 'pipe_hanger', 'support', 'soporte_colgador'],
    'valvula_de_control': ['valvula', 'valve', 'control_valve', 'valvula_control'],
}
_ALIAS_LOOKUP: Dict[str, str] = {c: c for c in APP_CLASSES}
for _cls, _names in _ALIASES.items():
    for _n in _names:
        _ALIAS_LOOKUP[_n] = _cls


class InferenceUnavailable(RuntimeError):
    """No se puede ejecutar el modelo (falta Ultralytics o los pesos)."""


def _slug(name: str) -> str:
    s = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode('ascii')
    return s.strip().lower().replace('-', '_').replace(' ', '_')


def normalize_class(name: str) -> Optional[str]:
    """Devuelve una clase PCI admitida por el MVP o None si no pertenece al caso."""
    return _ALIAS_LOOKUP.get(_slug(name))


def find_weights() -> Optional[Path]:
    """Busca los pesos entrenados en weights/best.pt o best.pt en la raíz del proyecto."""
    for rel in ('weights/best.pt', 'best.pt'):
        p = ROOT_DIR / rel
        if p.is_file():
            return p
    return None


@lru_cache(maxsize=2)
def _load_model(path_str: str, mtime: float):
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover
        raise InferenceUnavailable(
            "Ultralytics no está instalado. Ejecuta: pip install -r requirements-ml.txt"
        ) from exc
    return YOLO(path_str)


def run_inference(image, weights_path: Optional[Path] = None, conf: float = 0.25,
                  imgsz: int = 1280, iou: float = 0.5) -> Dict[str, Any]:
    """
    Ejecuta YOLO sobre una imagen PIL. Devuelve:
      {'detections': [{'id','class','confidence','box':[x1,y1,x2,y2] normalizados}],
       'ignored': {nombre_clase: n}, 'engine': str, 'seconds': float, 'imgsz': int}
    conf=0.25 deja pasar las dudosas; el semáforo (0.40 / 0.80) decide qué se cuenta.
    """
    weights_path = weights_path or find_weights()
    if weights_path is None or not Path(weights_path).is_file():
        raise InferenceUnavailable(
            "No se encontró weights/best.pt. Se necesitan pesos entrenados para "
            "detectar componentes PCI; también puedes importar detecciones JSON."
        )
    model = _load_model(str(weights_path), Path(weights_path).stat().st_mtime)
    t0 = time.perf_counter()
    result = model.predict(image, conf=conf, imgsz=imgsz, iou=iou, verbose=False)[0]
    seconds = time.perf_counter() - t0

    names = result.names
    boxes = result.boxes
    detections: List[Dict[str, Any]] = []
    ignored: Dict[str, int] = {}
    if boxes is not None and len(boxes) > 0:
        xyxyn = boxes.xyxyn.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)
        for i, (bx, cf, ci) in enumerate(zip(xyxyn, confs, clss)):
            raw_name = names.get(int(ci), str(ci)) if isinstance(names, dict) else names[int(ci)]
            cls = normalize_class(raw_name)
            if cls is None:
                ignored[raw_name] = ignored.get(raw_name, 0) + 1
                continue
            detections.append({
                'id': f"det-{i + 1}",
                'class': cls,
                'confidence': round(float(cf), 4),
                'box': [round(float(v), 5) for v in bx],
            })
    return {'detections': detections, 'ignored': ignored,
            'engine': f"Ultralytics · {Path(weights_path).name}", 'seconds': round(seconds, 2), 'imgsz': imgsz}


def detections_from_json(raw) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[str]]:
    """
    Importa detecciones desde JSON (str, bytes, lista o dict con la clave 'detections').
    Cada objeto admite: class|name|label, confidence|conf|score, box|bbox = [x1,y1,x2,y2]
    (normalizados 0-1 o en píxeles). Devuelve (detecciones, ignoradas, errores).
    """
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode('utf-8')
    data = json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(data, dict):
        data = data.get('detections', data.get('predictions', []))
    if not isinstance(data, list):
        raise ValueError("El JSON debe ser una lista de detecciones o un objeto con la clave 'detections'.")

    dets: List[Dict[str, Any]] = []
    ignored: Dict[str, int] = {}
    errors: List[str] = []
    for i, item in enumerate(data, start=1):
        try:
            name = item.get('class', item.get('name', item.get('label')))
            conf = item.get('confidence', item.get('conf', item.get('score')))
            box = item.get('box', item.get('bbox'))
            if name is None or conf is None or box is None or len(box) != 4:
                raise ValueError("faltan class, confidence o box de 4 valores")
            conf = float(conf)
            box = [float(v) for v in box]
            if not 0.0 <= conf <= 1.0:
                raise ValueError(f"confianza fuera de rango ({conf})")
        except Exception as exc:
            errors.append(f"Detección {i}: {exc}")
            continue
        cls = normalize_class(name)
        if cls is None:
            ignored[str(name)] = ignored.get(str(name), 0) + 1
            continue
        dets.append({'id': str(item.get('id', f"det-{i}")), 'class': cls, 'confidence': round(conf, 4), 'box': box})
    return dets, ignored, errors
