# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from mimetypes import init
import os
import logging
import json
import time
from datetime import datetime, timedelta
# from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import dash
from dash_bootstrap_components._components.Input import Input
from dash import dcc
from dash import html
# from dash_html_components.Center import Center
# from dash_html_components.Header import Header
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import requests
from dash.dependencies import Input, Output, State, MATCH, ALL 


from utility.present import body_present, need_ui
from utility.control_functions import control_circuit, control_heater_setpoint, control_heater_status, control_lights

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

logging.basicConfig(level=logging.DEBUG)

# How often to poll api
# Set to -1 to disable polling
UPDATE_INTERVAL =  int(os.getenv('UPDATE_INTERVAL', 5))
# Number of polls before data reported as stale
STALE_INTERVAL = timedelta(seconds = UPDATE_INTERVAL * 5)
# Internal ScreenLogic data refers to pool & spa as 'bodies'
SUPPORTED_BODY_TYPES = ['pool', 'spa']

current_pool_data = {}
last_update = datetime.now()
data_status_message=''
feature_control_ids = []
# Override UPDATE_INTERVAL with an environment variable

logging.info(f"Update Interval is {UPDATE_INTERVAL}")
POOL_API_URL = os.getenv('API_BASE_URL', '')
logging.info(f"Pool API Base URL is {POOL_API_URL}")
# Get external stylesheets
external_stylesheets = [dbc.icons.FONT_AWESOME, dbc.themes.BOOTSTRAP]
logging.info(f'External Stylesheets to be retrieved: {external_stylesheets}')

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
# This will grab the global data object from the API
# Other functions will refine that data

def refresh_pool_data():
    '''Grab the current Pool/Spa data from the API'''
    global current_pool_data
    global last_update
    logging.info(f'Calling backend API at {POOL_API_URL}/all')
    api_request = requests.get(f'{POOL_API_URL}/all', timeout=0.1)
    api_request.raise_for_status()
    api_request.close()
    logging.debug(f'API call status = {api_request.status_code}')
    if api_request.status_code == 200:
        current_pool_data = api_request.json()
        last_update = datetime.now()
        return True
    
    return False


# This will be scheduled via the interval-component
@app.callback(
    Output('ConnectedStatus', 'className'),
    Input('interval-component', 'n_intervals')
    )
def get_pool_data_every(n):
    status_classname = "fa fa-lg mb-1 icon ms-2 me-2 flex-nowrap text-light"
    success = refresh_pool_data()
    stale_data = bool((datetime.now() - last_update) > STALE_INTERVAL )
    global data_status_message
    if not stale_data:
        status_classname += ' fa-eye'
        data_status_message = 'Connected to API'
        logging.info('Pool Data Refreshed')
    else:
        status_classname += ' fa-eye-slash'
        logging.info('Failed to refresh data')
        data_status_message = f'Connection to API failed, data last fetched at {last_update}'
    # print(status_classname)
    return status_classname

# Get initial data
refresh_pool_data()

# Figure out (from the pool data) which bodies I need to create a card for
bodies_present = []
for body in SUPPORTED_BODY_TYPES:
    if body_present(body, current_pool_data):
        bodies_present.append(body)
logging.info(f'Bodies Detected: {bodies_present}')

lights_present = need_ui(current_pool_data, 3)
features_present = need_ui(current_pool_data, 2)


def generate_header_layout(pool_data):
    header = dbc.Nav(children=[
        html.Div(children=[
        html.Span(children=[
            html.Span(children='ScreenLogic', className='navbar-brand h1 me-1'),
            html.I(className='fa fa-info-circle fa-md icon align-middle mb-1 ms-2 text-light', id='PoolInfoIcon', n_clicks=0),
            dbc.Tooltip(
                f"{pool_data['meta']['server']['name']}", 
                placement='right', target='PoolInfoIcon', className='bs-tooltip-right'
            )], id='PoolInfo', className='nav-item'),
        html.Span(
            children=[
                html.I(className=f"fa fa-icicles fa-lg icon mb-1 ms-2 me-2 flex-nowrap text-light",
                    id='FreezeModeStatus', hidden=bool(not pool_data['meta']['freezeMode'])
                    ),
                html.I(className=f"fa fa-tools fa-lg icon mb-1 ms-2 me-2 flex-nowrap text-light", id='ServiceModeStatus', hidden=bool(not pool_data['meta']['serviceMode'])),
                html.I(className=f"fa fa-clock fa-lg icon mb-1 ms-2 me-2 flex-nowrap text-light", style={}, id='DelayStatus', hidden=bool(not pool_data['meta']['cleanerDelay'])),
                html.I(className=f"fa fa-lightbulb fa-lg mb-1 icon ms-2 me-2 flex-nowrap text-light", id='LightsStatus', hidden=bool(not pool_data['meta']['lightsOn'])),
                html.I(className=f"fa fa-eye fa-lg mb-1 icon ms-2 me-2 flex-nowrap text-light", id='ConnectedStatus'),
                dbc.Tooltip('Backend Connection Status', placement='bottom-end', target='ConnectedStatus', id='ConnectedStatusTT'),
                html.Span(children=[f"{pool_data['meta']['airTemp']}° {pool_data['meta']['tempScale']}"], className='navbar-item h5 ms-4 text-light', id='outsideTemp'
                ),
                dbc.Tooltip('Outside Air Temperature', placement='bottom-end', target='outsideTemp', id='AirTempTT')
            ], className='nav-item'
        )
                 
    ], className='container-fluid')
    ], className='navbar navbar-expand-lg navbar-dark bg-primary justify-content-between')
    
    return header

# Generate individual body layouts
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
            generate_body_controls(
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

@app.callback(
    Output({'type': 'power-button-icon', 'circuitId': MATCH, "body_name": MATCH}, 'className'),
    [
        Input({'type': 'power-button', 'circuitId': MATCH, "body_name": MATCH}, 'id'),
        Input({'type': 'power-button', 'circuitId': MATCH, "body_name": MATCH}, 'n_clicks')
    ],
    prevent_initial_call=True
)
def handle_power_button(id, clicks):
    body_active = False
    circuit_id = id.get('circuitId')
    match_body_index = -1
    global current_pool_data
    for i, body in enumerate(current_pool_data.get('status', {}).get('bodies', [])):
        if body.get('name') == id.get('body_name'):
            body_active = body.get('active')
            match_body_index = i
    print(f"Power Button ID= {id}")
    print(body_active)
    new_status = not body_active
    current_pool_data['status']['bodies'][match_body_index]['active'] = new_status
    color_class = ''
    if new_status:
        color_class = 'text-success'
    new_style = f'fa fa-power-off fa-lg {color_class}'
    return new_style

# Generate the body controls (Feature Toggles)
def generate_body_controls(name: str, circuit_id, checked: bool):
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
        
    global feature_control_ids
    feature_control_ids.append(str(circuit_id))
    logging.info(f"Switch control id: {control_id.get('circuit_id')} generated")
    return body_control

## Feature Toggle Callback and Handler
@app.callback(
    Output({'type': 'feature-toggle', 'circuitId': MATCH}, 'value'),
    [
        Input({'type': 'feature-toggle', 'circuitId': MATCH}, 'id'),
        Input({'type': 'feature-toggle', 'circuitId': MATCH}, 'value')
    ],
    prevent_initial_call=True   
)
def handle_feature_toggle(id: dict, checked: bool):
    circuit_id = id.get('circuitId', 0)
    new_mode = 'on' if checked else 'off'
    logging.info(f"Got Event for circuit {circuit_id}, switching to {new_mode}")

    # change_success = control_circuit(POOL_API_URL, circuit_id, int(checked))
    # status = checked if change_success else not checked
    # return status
    return checked

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

# Heater Controls Handlers
# Handle Slider Move
@app.callback(
    Output({'type': 'setpoint-label', 'id': MATCH, 'body': MATCH}, 'children'),
    [
        Input({'type': 'setpoint-slider', 'id': MATCH, 'body': MATCH}, 'id'),
        Input({'type': 'setpoint-slider', 'id': MATCH, 'body': MATCH}, 'value')
    ],
    prevent_initial_call=True   
)
def handle_heater_setpoint_slider_change(slider_id, value):
    body = slider_id.get('body')
    logging.info(f'Setpoint Slider for {body} changed to {value}.')
    logging.info(slider_id)
    logging.info(value)
    # call_success = control_heater_setpoint(POOL_API_URL, body, value)
    return value

# Handle Min/Max Buttons
# Note: Min/Max Buttons only manipulate the slider. The Callback on the Slider does the API call to the back end.
@app.callback(
    Output({'type': 'setpoint-slider', 'id': ALL, 'body': MATCH}, 'value'),
    [
        Input({'type': f'setpoint-button', 'id': ALL, 'body': MATCH}, 'n_clicks'),
        Input({'type': f'setpoint-button', 'id': ALL, 'body': MATCH}, 'value')
    ],
    prevent_initial_call=True    
)
def handle_setpoint_button(n_clicks, button_values):
    ctx = dash.callback_context
    button_id_dict = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
    value_index = 0
    button_id = button_id_dict.get('id')
    if 'min' in button_id:
        value_index = 0
    elif 'max' in button_id:
        value_index = 1
    else:
        logging.error(f'Did not find one of the expected button IDs. Expected min or max in id, got {button_id}')
    return_value = button_values[value_index]
    logging.info(f'{button_id} event received, setting setpoint slider to {return_value}')
    return [return_value]

@app.callback(
    Output({'type': 'heater-function-buttons', 'body': MATCH}, 'value'),
    Input({'type': 'heater-function-buttons', 'body': MATCH}, 'value'),
    prevent_initial_call=True
)
def handle_heater_mode_change(heat_mode):
    ctx = dash.callback_context
    button_info = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
    body = button_info.get('body')
    logging.info(f'Got heater mode {heat_mode} for {body}.')
    # call_success = control_heater_status(POOL_API_URL, body, heat_mode)
    return heat_mode

def generate_lights_layout(pool_data):
    '''Generate layout for Lights Controls'''
    if pool_data.get('meta', {}).get('lightsOn'):
        card_icon_color_class = 'text-primary'
        text_color_class = 'text-success'
        card_border_class = 'card border-primary'
    else:
        card_icon_color_class = ''
        text_color_class = ''
        card_border_class = ''
    button_color = 'secondary'
    intellibrite_labels = [
        'Party',
        'Romance',
        'Caribbean',
        'American',
        'Sunset',
        'Royal',
    ]
    intellibrite_buttons = []
    for label in intellibrite_labels:
        intellibrite_buttons.append(
            dbc.Button(label, outline=True, color=button_color, className="me-1", id=f"ibb-{label}")
        )
    solid_buttons = [
        dbc.Button("", className="btn-xl btn-circle me-2 ibrite-blue", id="const-blue"),
        dbc.Button("", className="btn-xl btn-circle me-2 ibrite-green", id="const-green"),
        dbc.Button("", className="btn-xl btn-circle me-2 ibrite-red", id="const-red"),
        dbc.Button("", className="btn-xl btn-circle me-2 ibrite-white", id="const-white"),
        dbc.Button("", className="btn-xl btn-circle me-2 ibrite-purple", id="const-purple"),
        
    ]

    light_card = dbc.Card([
        dbc.CardHeader(
            [
                dbc.Row(children=[
                    dbc.Col(
                        html.I(className=f"fa fa-lightbulb fa-lg {card_icon_color_class} mt-2"), 
                        width='auto', class_name='p-2 bd-highlight'
                        ),
                    dbc.Col([
                        html.H4(children='Lights', className="card-title")
                    ], width='auto', className='p-2'),
                    dbc.Col([
                        html.Div([
                            dbc.Button(
                                "Set", color="secondary", className="me-1",
                                id='lights-set-button'
                            ),
                            dbc.Button(
                                "Sync", color="secondary", className="me-1",
                                id='lights-sync-button'
                            ),
                            dbc.Button(
                                "Swim",color="secondary", className="me-1",
                                id='lights-swim-button'
                            )
                        ]),
                            
                    ], class_name='ms-5  p-2 bd-highlight'),
                    # Power Button Column
                    dbc.Col(
                        dbc.Button(
                            html.I(className=f'fa fa-power-off fa-lg {text_color_class}',
                            id={
                                "type": "power-button-icon",
                                "id": "lights-power-icon"
                            }
                            ),
                            class_name='btn-pwr-circle me-0',
                            color="light",
                            n_clicks=0,
                            id={
                                "type" : "power-button",
                                "id": "lights-power-button"
                            }
                        ), 
                        width=1, class_name='ms-auto p-2 bd-highlight'
                    )
                ], class_name='d-flex bd-highlight'
                )
            ]
            ),
    dbc.CardBody(
        [
            dbc.Row(
                html.H6(children="IntelliBrite")
            ),
            dbc.Row(
                dbc.Col(
                    intellibrite_buttons
                )
            ),
            dbc.Row(
                html.H6(children="Constant Colors", className='mt-3')
            ),
            dbc.Row(
                dbc.Col(
                    solid_buttons
                )
            )
        ]
        )
    ], class_name=f"w-90, {card_border_class}")
    return light_card

def generate_features_layout(pool_data):
    '''Generate layout for Feature Controls'''
    # Figure out what features go in the card
    body_array = pool_data.get('controllerConfig', {}).get('bodyArray')
    features_data = []
    for circuit in body_array:
        if circuit.get('interface') == 2:
            features_data.append(
                {
                    "label": circuit.get('name'),
                    "value": circuit.get('state'),
                    "circuit_id": circuit.get('circuitId'),
                    "name_index": circuit.get('nameIndex')
                }
            )
    features_array = []
    for control in features_data:
            features_array.append(
                generate_body_controls(
                    control.get('label'), control.get('circuit_id'), bool(control.get('value'))
                )
            )
    
    ## Generate the Card
    features_card = dbc.Card([
        dbc.CardHeader(
            [
                dbc.Row(children=[
                    dbc.Col(
                        html.I(className=f"fa fa-toggle-on fa-lg mt-2"), 
                        width='auto', class_name='p-2 bd-highlight'
                        ),
                    dbc.Col([
                        html.H4(children='Features', className="card-title")
                    ], width='auto', className='p-2')     
            ]
        ),
            ]),
    dbc.CardBody(
            features_array
        )
    ])
    return features_card

def make_layout(update_ival):
    header = html.Header(children=generate_header_layout(current_pool_data), className='mb-3')
    body_layout = []
    body_card_list = []
    for p_body in bodies_present:
        body_card = generate_body_info_layout(p_body, current_pool_data)
        body_card_list.append(dbc.Col(body_card, width=6, align='middle'))
    row_two_list = []
    light_card = generate_lights_layout(current_pool_data)
    features_card = generate_features_layout(current_pool_data)
    row_two_list.append(dbc.Col(light_card, width=6, align='middle'))
    row_two_list.append(dbc.Col(features_card, width=6, align='middle'))
    #Append each section in turn...
    body_layout.append(header)
    body_layout.append(dbc.Row(
        children=body_card_list, class_name='card-list, mb-4'
    ))
    body_layout.append(dbc.Row(children=row_two_list, className='card-list'))
    if update_ival == abs(update_ival):
        body_layout.append(
            dcc.Interval(
                id='interval-component',
                interval= update_ival * 1000, # in milliseconds
                n_intervals=0
            ))
    return body_layout

app_layout = make_layout(UPDATE_INTERVAL)



# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
app.layout = html.Div(children=app_layout, className='full-page')

# if UPDATE_INTERVAL != -1:
#     executor = ThreadPoolExecutor(max_workers=1)
#     executor.submit(get_pool_data_every)

if __name__ == '__main__':
    app.run_server(debug=True)