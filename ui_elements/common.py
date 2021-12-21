import logging
import dash_bootstrap_components as dbc

# Generate the body controls (Feature Toggles)
def generate_feature_controls(name: str, circuit_id, checked: bool):
    control_id = {
        "type": "feature-toggle",
        "circuitId": circuit_id
        }
    body_control = dbc.Switch(
        id=control_id,
        label=name,
        value=checked, 
        class_name='me-5'
        )
    logging.info(f"Switch control id: {control_id.get('circuit_id')} generated")
    return body_control