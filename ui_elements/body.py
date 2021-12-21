import logging
from dash import html, dcc
import dash_bootstrap_components as dbc
from ui_elements.common import generate_feature_controls

# Generate individual body (of water, i.e. pool/spa) layouts
def generate_body_info_layout(body_name, pool_data):
    '''Generate a UI card per body present'''
    # print(body_name)
    body_info = {}
    body_control_data = []
    body_icons = {
        'pool': 'swimming-pool',
        'spa': 'hot-tub'
    }
    for body in pool_data['status']['bodies']:
        if body['name'] == body_name:
            body_info = body
    if body_info['active']:
        card_icon_color_class = 'text-primary'
        text_color_class = 'text-success'
        card_border_class = 'card border-primary'
    else:
        card_icon_color_class = ''
        text_color_class = ''
        card_border_class = ''

    if body_info['heater']['active']:
        heater_color_class = 'text-warning'
    else:
        heater_color_class = ''
    # Figure out what controls go on this card
    interface_id = body_info['interfaceId']
    for circuit in pool_data['controllerConfig']['bodyArray']:
        if circuit.get('interface') == interface_id and circuit.get('name').lower() != body_name:
            body_control_data.append(
                {
                    "label": circuit.get('name'),
                    "value": circuit.get('state'),
                    "circuit_id": circuit.get('circuitId'),
                    "name_index": circuit.get('nameIndex')
                }
            )
    body_control_data.sort(key=lambda k: k.get('name_index'))
    body_controls = []
    for control in body_control_data:
        body_controls.append(
            generate_feature_controls(
                control.get('label'), control.get('circuit_id'), bool(control.get('value'))
            )
        )
    card = dbc.Card([
        dbc.CardHeader(
            [
                dbc.Row(children=[
                    dbc.Col(
                        html.I(className=f"fa fa-{body_icons[body_name]} fa-lg {card_icon_color_class} mt-2"), 
                        width='auto', class_name='p-2 bd-highlight'
                        ),
                    dbc.Col([
                        html.H4(children=body_info['name'].capitalize(), className=""),
                    ], width='auto', className='bd-highlight p-2'),
                    dbc.Col([
                        html.H6(children=f"{body_info['waterTemp']}° {body_info['tempScale']}", className="")
                    ], width='auto', className='bd-highlight p-2 mt-1 ms-3'),
                    dbc.Col(
                        html.I(className=f'fa fa-fire fa-lg mt-2 {heater_color_class}', hidden=bool(not body_info.get('heater', {}).get('equipPresent', {}).get('heater', {})) ), width=1, class_name='ms-auto p-2 bd-highlight'),
                    dbc.Col(
                        dbc.Button(
                            html.I(className=f'fa fa-power-off fa-lg {text_color_class}',
                            id={
                                "type": "power-button-icon",
                                "circuitId": body_info.get('circuitId'),
                                "body_name": body_info.get('name') 
                            }
                            ),
                            class_name='btn-pwr-circle me-0',
                            color="light",
                            n_clicks=0,
                            id={
                                "type" : "power-button",
                                "circuitId": body_info.get('circuitId'),
                                "body_name": body_info.get('name')
                            }
                        ), 
                        width=1, class_name='p-2 bd-highlight'
                    )
                ], class_name='d-flex bd-highlight'
                )
            ]
            ),
        dbc.CardBody([
            html.Div(
                children=body_controls,
                className='input-group'
            ),
            html.Hr(),
            html.Div(
                children=generate_body_heater_controls(body_info),
            )
                
            
        ])
    ], className=f"w-90, {card_border_class}")
    return card

# Generate Heater controls for each card
def generate_body_heater_controls(body_info):
    setpoint_config = body_info.get('heater', {}).get('setpoint',{})
    heater_options_present = []
    heater_buttons = [
        {"label": "Off", "value": 0},  
    ]
    for key in body_info.get('heater', {}).get('equipPresent'):
        if not key.endswith('isheater'):
            if body_info.get('heater', {}).get('equipPresent',{}).get(key):
                heater_options_present.append(key)
    print(heater_options_present)
    for option in heater_options_present:
        if option == "heater":
            heater_buttons.append({"label": "Heater", "value": 3})
        if option == "solar":
            heater_buttons.append({"label": "Solar", "value": 1})
            heater_buttons.append({"label": "Solar Preferred", "value": 2})
    logging.info(f'Need {len(heater_buttons)} buttons for heater controls')
    controls = []
    heater_slider = html.Div(children = [
        dbc.Row([
            html.H5('Heater')
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    setpoint_config.get('min'),
                    class_name='btn-setpoint-circle mx-0',
                    color="light",
                    n_clicks=0,
                    value=setpoint_config.get('min'),
                    id={
                        'type': 'setpoint-button',
                        'id': f'{body_info.get("name")}-setpoint-min',
                        'body': body_info.get("name")
                    }
            )], width=1, class_name='mx-0 p-2 bd-highlight'),
            dbc.Col(
                [
                    dcc.Slider(
                        id={
                            'type': 'setpoint-slider',
                            'id': f'{body_info.get("name")}-setpoint',
                            'body': body_info.get("name")
                        },
                        step=1,
                        min=setpoint_config.get('min', 40),
                        max=setpoint_config.get('max', 104),
                        value=setpoint_config.get('current', 0),
                        className='mx-0')
                ], 
                class_name='mx-0 mt-3 ms-auto p-2 bd-highlight'
            ),
            dbc.Col([dbc.Button(
                setpoint_config.get('max'),
                class_name='btn-setpoint-circle mx-0',
                color="light",
                n_clicks=0,
                value=setpoint_config.get('max'),
                id={
                    'type': 'setpoint-button',
                    'id': f'{body_info.get("name")}-setpoint-max',
                    'body': body_info.get("name")
                }
            )], width=1, class_name='mx-0 mb-0 ms-auto p-2 bd-highlight'),
            dbc.Col([
                dbc.Label(children=[f'{setpoint_config.get("current")}'], class_name='h5 me-0 mt-2',
                id={
                    'type': 'setpoint-label',
                    'id': f'{body_info.get("name")}-setpoint',
                    'body': body_info.get("name")
                }),
                dbc.Label(f'° {body_info.get("tempScale")}', class_name='h5')       
                ], 
                width=2, class_name='mx-0 mb-0 p-2 bd-highlight') 
            ]
        ),
        dbc.Row(
            dbc.Col(
                html.Div(
                    dbc.RadioItems(
                        id={
                            'type': 'heater-function-buttons',
                            'body': body_info.get("name")
                            },
                        class_name="btn-group btn-group-toggle",
                        input_class_name="btn-check",
                        label_class_name="btn btn-outline-primary",
                        label_checked_class_name="active",
                        options=heater_buttons,
                        value=body_info.get('modeCode', 0)
                    ), 
                className="ms-2 radio-group")
            )
        )
    ])
    controls.append(heater_slider)
    return controls