import requests

def control_circuit(api_endpoint: str, circuit_id: int, new_state: int) -> bool:
    '''Generic API call to change a standard Pentair Circuit'''
    api_call = requests.put(f'{api_endpoint}/circuit/{circuit_id}/{new_state}')
    if api_call.status_code == 200:
        return True
    return False

def control_heater_status(api_endpoint: str, body: str, new_mode: int) -> bool:
    '''API call to control the various heater modes
        Heater Modes are:
        0: Off
        1: Solar
        2: Solar Preferred
        3: Heat Pump
        4: No Change
    '''
    api_call = requests.put(f'{api_endpoint}/{body}/heater/mode/{new_mode}')
    if api_call.status_code == 200:
        return True
    return False

def control_heater_setpoint(api_endpoint: str, body: str, temp: int) -> bool:
    '''API Call to modify the heater setpoint.
        Temperature should be an integer in the Temp Scale your pool is configured for
    '''
    api_call = requests.put(f'{api_endpoint}/{body}/heater/setpoint/{temp}')
    if api_call.status_code == 200:
        return True
    return False

def control_lights(api_endpoint: str, light_command: int) -> bool:
    '''API Control for controling lights.
    '''
    api_call = requests.put(f'{api_endpoint}/lights/{light_command}')
    if api_call.status_code == 200:
        return True
    return False