"""
BuildVision AI - Motor de Cálculo de Avance Físico
Implementación estricta de la Sección 5 (Estrategia de IA) y Caso CP-05
Grupo 15: Diego Avella, Patricia Luna, Daniel Salcedo
"""
from typing import Dict, Any, Tuple, List

# Pesos acordados según Sección 5
DEFAULT_WEIGHTS: Dict[str, float] = {
    'tuberia': 0.45,           # Tuberías principales y ramales (tramos)
    'soportes': 0.15,          # Soportes sismorresistentes y colgadores tipo pera
    'rociadores': 0.30,        # Rociadores (sprinklers) instalados
    'valvula': 0.05,           # Válvula de control sectorial
    'prueba_hidraulica': 0.05  # Prueba hidráulica estanca (casilla manual ITO)
}

COMPONENT_NAMES: Dict[str, str] = {
    'tuberia': 'Tubería (tramos)',
    'soportes': 'Soportes y Colgadores',
    'rociadores': 'Rociadores instalados',
    'valvula': 'Válvula de control',
    'prueba_hidraulica': 'Prueba hidráulica (inspección manual)'
}

def calculate_zone_progress(
    validated_counts: Dict[str, int],
    plan_units: Dict[str, int],
    weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Calcula el avance de una zona z siguiendo la fórmula de la Sección 5:
    p(c,z) = min(n(c,z) / N(c,z), 1.0)
    A(z) = sum(w(c) * p(c,z))
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    components_detail = []
    total_progress = 0.0
    inconsistencies = []

    for comp_key, weight in weights.items():
        n_val = validated_counts.get(comp_key, 0)
        n_plan = plan_units.get(comp_key, 1)  # evitar división por cero
        
        if n_plan <= 0:
            p_cz = 1.0 if n_val > 0 else 0.0
        else:
            p_cz = min(float(n_val) / float(n_plan), 1.0)

        # Alerta de inconsistencia si supera el plan
        if n_val > n_plan:
            inconsistencies.append(
                f"{COMPONENT_NAMES.get(comp_key, comp_key)}: {n_val} detectados superan la meta planificada de {n_plan}."
            )

        contribution = weight * p_cz
        total_progress += contribution

        components_detail.append({
            'key': comp_key,
            'name': COMPONENT_NAMES.get(comp_key, comp_key),
            'weight': weight,
            'validated': n_val,
            'plan': n_plan,
            'ratio_p': round(p_cz, 4),
            'contribution': round(contribution, 4)
        })

    return {
        'progress_pct': round(total_progress * 100.0, 1),
        'progress_raw': total_progress,
        'components': components_detail,
        'inconsistencies': inconsistencies
    }

def calculate_level_progress(
    zones_data: List[Dict[str, Any]],
    weights: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Calcula el avance agregado de una partida / nivel:
    A = sum(P(z) * A(z)) / sum(P(z))
    Donde P(z) es la suma total de unidades del plan en la zona z.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    total_weighted_sum = 0.0
    total_plan_units = 0
    evaluated_zones = []

    for z in zones_data:
        z_name = z['name']
        plan = z['plan']
        val = z['validated']
        coverage = z.get('coverage', 'Total')
        plan_week_pct = z.get('plan_week_pct', 85.0)

        z_calc = calculate_zone_progress(val, plan, weights)
        p_z = sum(plan.values())
        total_plan_units += p_z
        total_weighted_sum += p_z * z_calc['progress_raw']

        deviation_pp = z_calc['progress_pct'] - plan_week_pct
        if deviation_pp <= -10.0:
            alert_status = 'CRÍTICA'
            alert_color = '#DC2626' # Rojo
        elif deviation_pp <= -5.0:
            alert_status = 'DESVIACIÓN'
            alert_color = '#D97706' # Ámbar
        else:
            alert_status = 'CONFORME'
            alert_color = '#059669' # Verde

        evaluated_zones.append({
            'id': z.get('id', z_name),
            'name': z_name,
            'plan_units_total': p_z,
            'progress_pct': z_calc['progress_pct'],
            'plan_week_pct': plan_week_pct,
            'deviation_pp': round(deviation_pp, 1),
            'alert_status': alert_status,
            'alert_color': alert_color,
            'coverage': coverage,
            'needs_review': z.get('needs_review', False),
            'components': z_calc['components'],
            'inconsistencies': z_calc['inconsistencies']
        })

    level_progress_pct = (
        round((total_weighted_sum / total_plan_units) * 100.0, 1)
        if total_plan_units > 0 else 0.0
    )

    return {
        'level_progress_pct': level_progress_pct,
        'zones': evaluated_zones,
        'total_plan_units': total_plan_units
    }
