def body_present(body_name: str, pool_data: dict) -> bool:
    for body in pool_data['status']['bodies']:
        if body['name'] == body_name:
            return True
    return False

def need_ui(pool_data: dict, ui_int: int):
    for config in pool_data['controllerConfig']['bodyArray']:
        if config['interface'] == ui_int:
            return True
    return False

# Data I will need later for lights...
# light_config['name'] = config['name']
# light_config['present'] = True
# light_config['circuitId'] = config['circuitId']
# light_config['function'] = config['function']