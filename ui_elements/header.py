from dash import html
import dash_bootstrap_components as dbc

# Generate the Header layout
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
                dbc.Tooltip(children = ['Connected to API'], placement='bottom-end', target='ConnectedStatus', id='ConnectedStatusTT'),
                html.Span(children=[f"{pool_data['meta']['airTemp']}° {pool_data['meta']['tempScale']}"], className='navbar-item h5 ms-4 text-light', id='outsideTemp'
                ),
                dbc.Tooltip('Outside Air Temperature', placement='bottom-end', target='outsideTemp', id='AirTempTT')
            ], className='nav-item'
        )
                 
    ], className='container-fluid')
    ], className='navbar navbar-expand-lg navbar-dark bg-primary justify-content-between')
    
    return header