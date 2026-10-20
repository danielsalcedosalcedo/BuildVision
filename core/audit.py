"""
BuildVision AI - Sistema de Auditoría y Trazabilidad HITL (RF-06, Sección 3 Etapa G)
Registra cada decisión humana: quién, qué, cuándo, valor anterior y nuevo.
Permite función de deshacer (CP-07) e historial para peritaje de avance.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

class AuditTrail:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self._undo_stack: List[Dict[str, Any]] = []

    def log_action(
        self,
        user: str,
        action: str,
        zone_id: str,
        target_component: str,
        old_val: Any,
        new_val: Any,
        note: str = ""
    ) -> Dict[str, Any]:
        """
        Registra una acción de auditoría inmutable
        """
        entry = {
            'id': len(self.logs) + 1,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user': user,
            'action': action,
            'zone_id': zone_id,
            'component': target_component,
            'old_value': old_val,
            'new_value': new_val,
            'note': note
        }
        self.logs.append(entry)
        self._undo_stack.append(entry)
        return entry

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def get_last_action(self) -> Optional[Dict[str, Any]]:
        if self._undo_stack:
            return self._undo_stack[-1]
        return None

    def pop_undo(self) -> Optional[Dict[str, Any]]:
        if self._undo_stack:
            last = self._undo_stack.pop()
            # Registramos también el evento de revertir
            self.logs.append({
                'id': len(self.logs) + 1,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'user': last['user'],
                'action': 'DESHACER (Reversión)',
                'zone_id': last['zone_id'],
                'component': last['component'],
                'old_value': last['new_value'],
                'new_value': last['old_value'],
                'note': f"Reversión de acción ID #{last['id']}"
            })
            return last
        return None

    def get_logs_as_dicts(self) -> List[Dict[str, Any]]:
        return list(reversed(self.logs))
