# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from mimetypes import init
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash_html_components.Center import Center
from dash_html_components.Header import Header
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import requests

from utility.present import body_present, need_ui

# How often to poll api
# Set to -1 to disable polling
UPDATE_INTERVAL = 5
# Internal ScreenLogic data refers to pool & spa as 'bodies'
SUPPORTED_BODY_TYPES = ['pool', 'spa']

current_pool_data = {}
# Override UPDATE_INTERVAL with an environment variable
if os.getenv('UPDATE_INTERVAL'):
    UPDATE_INTERVAL = os.getenv('UPDATE_INTERVAL')

# Get external stylesheets
external_stylesheets = ['https://use.fontawesome.com/releases/v5.8.1/css/all.css']

# This will grab the global data object from the API
# Other functions will refine that data
def refresh_pool_data():
    '''Grab the current Pool/Spa data from the API'''
    global current_pool_data
    pool_api_url = os.getenv('API_BASE_URL', '')
    api_request = requests.get(f'{pool_api_url}/all')
    if api_request.status_code == 200:
        current_pool_data = api_request.json()

# This will be schedule via an executor thread below
def get_pool_data_every(period=UPDATE_INTERVAL):
    """Update the data every 'period' seconds"""
    while True:
        refresh_pool_data()
        print("data updated")
        time.sleep(period)

# Get inital data
refresh_pool_data()

# Figure out (from the pool data) which bodies I need to create a card for
bodies_present = []
for body in SUPPORTED_BODY_TYPES:
    if body_present(body, current_pool_data):
        bodies_present.append(body)

lights_present = need_ui(current_pool_data, 3)
features_present = need_ui(current_pool_data, 2)

def generate_header_layout(pool_data):
    header = html.Div(children=[
        dbc.Row([
            dbc.Col(
                [
                html.H4(children='ScreenLogic', ),
                html.H5(children=pool_data['meta']['server']['name'])
                ], id='PoolInfo', width="auto"
                ),
            dbc.Col(
                html.Span(
                    className='spacer flex-nowrap', id='HeaderSpace'
                    ), width=8
                ),
                
            dbc.Col(                
                    html.I(className=f"fa fa-clock fa-lg icon me-auto flex-nowrap", style={}, id='DelayStatus', hidden=False)
            ),
            dbc.Col([
                html.I(className=f"fa fa-tools fa-lg icon me-auto flex-nowrap", id='ServiceModeStatus')
            ]
            ),
            dbc.Col(
                html.I(className=f"fa fa-icicles fa-lg icon me-auto flex-nowrap", id='FreezeModeStatus'), 
            ),
            dbc.Col(
                html.I(className=f"fa fa-lightbulb fa-lg icon me-auto flex-nowrap", id='LightsStatus')
                ),
            dbc.Col(
                [
                html.H5(children=[f"{pool_data['meta']['airTemp']}°{pool_data['meta']['tempScale']}"], style={'text-align': 'center'}
                ),
                html.P(children='outside')
            ], id='RightSideData', className='my-sm-0 float-end flex-nowrap me-auto')
        ])
    ], className='container-fluid')
    return header

# Generate individual body layouts
def generate_body_info_layout(body_name, pool_data):
    '''Generate a UI card per body present'''
    body_info = {}
    body_icons = {
        'pool': 'swimming-pool',
        'spa': 'hot-tub'
    }
    for body in pool_data['status']['bodies']:
        if body['name'] == body_name:
            body_info = body
    card = dbc.Card([
        dbc.CardHeader(
            [
                dbc.Row(children=[
                    dbc.Col(
                        html.I(className=f"fa fa-{body_icons[body_name]} fa-lg"), 
                        width='auto'
                        ),
                    dbc.Col([
                        html.H4(children=body_info['name'].capitalize(), className="card-title"),
                        html.P(children=f"{body_info['waterTemp']}° {body_info['tempScale']}", className="card-text")
                    ], width=2),
                    dbc.Col(
                        html.Span(className='spacer')
                    ),
                    dbc.Col(
                        html.I(className='fa fa-fire fa-lg'), width=1),
                    dbc.Col(
                        html.I(className='fa fa-power-off fa-lg'), width=1)
                ])
            ]
            ),
        dbc.CardBody([
            # Data and controls here
        ])
    ], className="w-90")
    return card

def generate_lights_layout():
    return

def generate_features_layout():
    return

def make_layout():
    header = html.Header(children=generate_header_layout(current_pool_data), className='')
    body_layout = [header]
    body_card_list = []
    for p_body in bodies_present:
        body_card = generate_body_info_layout(p_body, current_pool_data)
        body_card_list.append(dbc.Col(body_card, width=6, align='middle'))
    # light_card = generate_light_layout()
    # features_card = generate_features_layout()

    body_layout.append(dbc.Row(
        children=body_card_list, className='card-list'
    ))
    
    return body_layout

app_layout = make_layout()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)



# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
app.layout = html.Div(children=app_layout, className='full-page')

# app.layout = html.Div(children=[
#     html.Header(children=[
#         html.H1(children='ScreenLogic'),
#         html.H3(children=current_pool_data['meta']['server']['name']),
#     ]),
#     # html.Div(children=json.dumps(current_pool_data)),

# ])

if UPDATE_INTERVAL != -1:
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(get_pool_data_every)

if __name__ == '__main__':
    app.run_server(debug=True)