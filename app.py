# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from mimetypes import init
import os
import logging
import json
from datetime import datetime, timedelta
import dash
from dash_bootstrap_components._components.Input import Input
from dash import dcc
from dash import html
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import requests
from dash.dependencies import Input, Output, State, MATCH, ALL 

# Import Utility Functions
from utility.present import body_present, need_ui
from utility.control_functions import control_circuit, control_heater_setpoint, control_heater_status, control_lights

# Import UI elements
from ui_elements.header import generate_header_layout
from ui_elements.common import generate_feature_controls
from ui_elements.body import generate_body_info_layout
from ui_elements.lights import generate_lights_layout
from ui_elements.features import gen_features_pumps_cards

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
    # api_request.close()
    logging.debug(f'API call status = {api_request.status_code}')
    if api_request.status_code == 200:
        current_pool_data = api_request.json()
        last_update = datetime.now()
        return True
    
    return False


# This will be scheduled via the interval-component
@app.callback(
    [
        Output('ConnectedStatus', 'className'),
        Output('ConnectedStatusTT', 'children'),
        Output('pageLayout', 'children')
    ],
    Input('interval-component', 'n_intervals')
    )
def get_pool_data_every(n):
    status_classname = "fa fa-lg mb-1 icon ms-2 me-2 flex-nowrap text-light"
    success = refresh_pool_data()
    stale_data = bool((datetime.now() - last_update) > STALE_INTERVAL )
    tt_text = ''
    if not stale_data:
        status_classname += ' fa-eye'
        tt_text = 'Connected to API'
        logging.info('Pool Data Refreshed')
    else:
        status_classname += ' fa-eye-slash'
        logging.info('Failed to refresh data')
        tt_text = 'Connection to API failed'
    page_layout = make_layout(UPDATE_INTERVAL)
    return status_classname, tt_text, page_layout

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

    change_success = control_circuit(POOL_API_URL, circuit_id, int(checked))
    status = checked if change_success else not checked
    return status
    # return checked

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

def make_layout(update_ival):
    header = html.Header(children=generate_header_layout(current_pool_data), className='mb-3')
    body_layout = []
    body_card_list = []
    for p_body in bodies_present:
        body_card = generate_body_info_layout(p_body, current_pool_data)
        body_card_list.append(dbc.Col(body_card, width=6, align='middle'))
    row_two_list = []
    light_card = generate_lights_layout(current_pool_data)
    features_card = gen_features_pumps_cards(current_pool_data)
    row_two_list.append(dbc.Col(light_card, width=6, align='middle'))
    row_two_list.append(dbc.Col(features_card, width=6, align='middle')
    )
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
app.layout = html.Div(children=app_layout, className='full-page', id='pageLayout')

# if UPDATE_INTERVAL != -1:
#     executor = ThreadPoolExecutor(max_workers=1)
#     executor.submit(get_pool_data_every)

if __name__ == '__main__':
    app.run_server(debug=True)