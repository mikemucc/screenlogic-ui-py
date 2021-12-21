
from dash import html
import dash_bootstrap_components as dbc

def generate_lights_layout(pool_data):
    '''Generate layout for Lights Controls'''
    if pool_data.get('meta', {}).get('lightsOn'):
        card_icon_color_class = 'text-warning'
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