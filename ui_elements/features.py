
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd

from ui_elements.common import generate_feature_controls

def gen_features_pumps_cards(pool_data):
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
                generate_feature_controls(
                    control.get('label'), control.get('circuit_id'), bool(control.get('value'))
                )
            )
    card_list = []
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
    # Pumps card
    pumps_array = pool_data.get('status', {}).get('pumps', {})
    pumps_transformed = []
    for key in pumps_array:
        pump = pumps_array.get(key)
        pump_status = 'Running' if pump.get('isRunning') else 'Off'
        pump_data = {
            'Pump': key,
            'Type' : pump.get('pumpTypeName'),
            'Status': pump_status,
            'Speed (RPM)' : pump.get('pumpRPMs'),
            'Power Usage (Watts)' : pump.get('pumpWatts'),
        }
        pumps_transformed.append(pump_data)
    pump_df = pd.DataFrame(pumps_transformed)
    pumps_card = dbc.Card([
        dbc.CardHeader(
            [
                dbc.Row(children=[
                    dbc.Col(
                        html.I(className=f"fa fa-water fa-lg mt-2"), 
                        width='auto', class_name='p-2 bd-highlight'
                        ),
                    dbc.Col([
                        html.H4(children='Pumps', className="card-title")
                    ], width='auto', className='p-2')     
            ]
        ),
            ]),
    dbc.CardBody(
        dbc.Table.from_dataframe(pump_df, striped=True, borderless=True, hover=True)
    )
    ], class_name='mt-2')
    card_list.append(features_card)
    card_list.append(pumps_card)
    return card_list
