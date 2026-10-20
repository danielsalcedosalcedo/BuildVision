from core.progress_calculator import calculate_zone_progress, calculate_level_progress

def test_cp05():
    # Caso dorado CP-05 (Sección 5)
    plan = {
        'tuberia': 12,
        'soportes': 18,
        'rociadores': 24,
        'valvula': 1,
        'prueba_hidraulica': 1
    }
    validated = {
        'tuberia': 12,
        'soportes': 14,
        'rociadores': 15,
        'valvula': 1,
        'prueba_hidraulica': 0
    }
    res = calculate_zone_progress(validated, plan)
    print("CP-05 Result:", res['progress_pct'], "%")
    assert res['progress_pct'] == 80.4, f"Expected 80.4, got {res['progress_pct']}"
    print("CP-05 Passed successfully!")

if __name__ == '__main__':
    test_cp05()
