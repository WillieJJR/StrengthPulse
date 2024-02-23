import os
import pandas as pd
import numpy as np
import dash
from dash import dcc
from dash import html
from dash import dash_table
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.figure_factory as ff
import datetime
from scipy.stats import percentileofscore
from data_retrieval import PowerliftingDataRetriever
from data_cleaning import clean_same_names, calculate_wilks, classify_wilks
from postgres_ingestion import PowerliftingDataHandler




data_retriever = PowerliftingDataRetriever()
css_path = 'assets/styles.css'

def kpi_one():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H4("Your Squat is better than:"),
                    html.Div(id = 'squat_vals'),
                ], style={'textAlign': 'center'})
            ])
        ),
    ])

def kpi_two():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H4("Your Bench Press is better than:"),
                    html.Div(id = 'bench_vals'),
                ], style={'textAlign': 'center'})
            ])
        ),
    ])

def kpi_three():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H4("Your Deadlift is better than:"),
                    html.Div(id = 'deadlift_vals'),
                ], style={'textAlign': 'center'})
            ])
        ),
    ])

def kpi_four():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H4("Times Competed:"),
                    html.Div(id = 'times-competed-kpi'),
                ], style={'textAlign': 'center'})
            ])
        ),
    ])

def kpi_five():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H4("Highest Placement: "),
                    html.Div(id = 'placement-kpi'),
                ], style={'textAlign': 'center'})
            ])
        ),
    ])

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY, css_path, dbc.icons.FONT_AWESOME], suppress_callback_exceptions=True)
server = app.server

# Define colors
text_color = '#ffffff'
link_color = '#007bff'


app.layout = html.Div(children=[
    html.Div([
        html.H1("StrengthPulse - A Powerlifting Performance Analyzer App", style={'text-align': 'center'}),
        html.Div([
            html.P("Welcome to StrengthPulse, your ultimate Powerlifting performance analyzer. "
                   "Benchmark your lifting numbers, gain insights, and optimize your training.",
                   style={'text-align': 'center'}),
        ]),
    ], style={'margin': '20px'}),

    dbc.Tabs(id='tabs', active_tab='landing-page', children=[
        dbc.Tab(label='Landing Page', tab_id='landing-page'),
        dbc.Tab(label='Most Current Competition Data', tab_id='comp-data'),
        dbc.Tab(label='Personal Powerlifting Stats', tab_id='user-stats'),
        dbc.Tab(label='Competitor Analytics', tab_id='tab-comparative-analysis'),
    ]),

    html.Div(id='tab-content', style={'margin-top': '20px'}),
])

#handle local deployment vs server deployment
try:
    from config import DATABASE_URL
    os.environ['DATABASE_URL'] = DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
except ImportError:
    print('Package is not available in Deployment environment. Setting Environment Variable')
    database_url = os.environ.get('DATABASE_URL') #the environment variable is pre-set in deployment environment



postgres_instance = PowerliftingDataHandler(database_url)
df = postgres_instance.fetch_data(table_name='powerlifting_data')

user_total = {}
user_data = {}
user_data_perc = {}
estimated_comp_class = {}
lifter_count = []
user_total_dist = []

def render_landing_page():
    return html.Div([

        # Features section (3 columns) moved down with increased spacing
        html.Div([
            html.H2("Features: ", style={'text-align': 'center'}),
            html.Div([
                html.Div([
                    html.H4(["Integrated Data Pipeline: ", html.I(className="fa-solid fa-code-branch")]),
                    dcc.Markdown(
                        "- This application has access to data provided by "
                        + "[OpenPowerlifting.com](https://openpowerlifting.gitlab.io/opl-csv/), "
                        + "and is updated regularly.",
                        style={'margin': '20px 0'}
                    ),
                ], style={'flex': '1', 'margin': '20px', 'padding': '20px', 'border': '1px solid #ecf0f1',
                          'border-radius': '10px'}),

                html.Div([
                    html.H4(["Performance Benchmarking: ", html.I(className="fa-solid fa-dumbbell")]),
                    dcc.Markdown(
                        "- Compare your Squat, Bench, and Deadlift numbers with data from actual competitions.",
                        style={'margin': '20px 0'}
                    )
                ], style={'flex': '1', 'margin': '20px', 'padding': '20px', 'border': '1px solid #ecf0f1',
                          'border-radius': '10px'}),

                html.Div([
                    html.H4(["Competitor Analytics: ", html.I(className="fa-solid fa-chart-line")]),
                    dcc.Markdown(
                        "- Users can select a lifter, and a resulting line chart will display their Squat, Bench, and Deadlift performance. "
                        "The default view is by the Date of Competition, but users have the flexibility to switch and view the chart by Age or by Weight",
                        style={'margin': '20px 0'}
                    )
                ], style={'flex': '1', 'margin': '20px', 'padding': '20px', 'border': '1px solid #ecf0f1',
                          'border-radius': '10px'}),
            ], style={'display': 'flex', 'justify-content': 'center'}), #added the height to increase the size of the features columns

        ], style={'margin': '20px'}),

        html.Div([
            html.H2("How It Works: ", style={'text-align': 'center'}),
            html.Div([
                html.Div([
                    dcc.Markdown(
                        "- **WILKS Calculation Tab:** Calculate your WILKS score and see how well you compare against others who have competed in your State.\n\n"
                        "- **Comparative Analysis Tab:** Compare your current statistics with those of fellow competitors in your selected Weight Class, Age Class, and Federation.\n\n"
                        "- **Competitor Performance Tab:** Select from available competitors to view detailed performance metrics. Customize your view by Date, Bodyweight, or Age for a comprehensive analysis."
                    ),
                ], style={'text-align': 'left', 'margin': '20px'}),
            ], style={'flex': '1', 'margin': '20px', 'padding': '20px', 'border': '1px solid #ecf0f1',
                      'border-radius': '10px', 'display': 'flex', 'justify-content': 'center'})
            ]),

        # Image Section
        html.Div([
            html.Img(src='/assets/hiclipart.com (4).png', style={'width': '18%', 'margin': 'auto', 'display': 'block'}),
        ], style={'text-align': 'center', 'margin': '20px'}),

        # html.Div(
        #     dbc.Button(
        #         children=[
        #             html.Div('Get Started',
        #                      style=dict(paddingRight='0.3vw', display='inline-block', verticalAlign='top',
        #                                 marginTop='-8px')),
        #             html.I(className='fa-solid fa-circle-right',
        #                    style=dict(display='inline-block', verticalAlign='top', lineHeight='0.8',
        #                               marginRight='5px')),
        #         ],
        #         id='get-started',
        #         n_clicks=0,
        #         size='md',
        #         style=dict(
        #             fontSize='1.7vh',
        #             backgroundColor='rgba(0, 0, 0, 0)',
        #             textAlign='center',
        #             height='32px',
        #             border='none'
        #         )
        #     ),
        #     style=dict(display='flex', justifyContent='center', alignItems='center')
        # ),

        html.P("© 2024 StrengthPulse. All rights reserved.", style={'text-align': 'center', 'color': '#7f8c8d'})

    ])
def render_comp_data():
    return html.Div([
        html.H3('Wilks Score Comparison', style={'color': text_color}),
        html.P(
            'This tab allows users to calculate their Wilks score, providing a standardized measure of strength that accounts for differences in body weight and gender.',
            style={'color': text_color}),
        html.Br(),
        # Row for filter components and plot
        dbc.Row([
            # Column for filter components
            dbc.Col([
                # Container for Gender filter
                dbc.Container([
                    html.Div([
                        html.Label('Lbs:'),
                        daq.BooleanSwitch(
                            id='lbs-switch-t2',
                            on=False,
                            labelPosition="top",
                            color='#008000'
                        ),
                    ], style={'display': 'flex', 'gap': '10px', 'justify-content': 'flex-start'}),
                    html.Br(),
                    html.Label('Please select a Gender..'),
                    dcc.RadioItems(
                        id='sex-filter-t2',
                        options=[{'label': 'Male', 'value': 'M'}, {'label': 'Female', 'value': 'F'}],
                        labelStyle={'display': 'block'},
                        style={'background-color': 'transparent', 'margin-bottom': '20px'}
                    ),
                ], style={'width': '100%', 'max-width': '100%', 'margin-bottom': '20px'}),


                dbc.Container([
                    html.Label('Estimated total in Kg (Squat, Bench Press, and Deadlift)..'),
                    html.Div([
                        dcc.Input(
                            id='total-filter',
                            type='number',
                            value=500,
                            placeholder='Total (Kg)',
                            style={'width': '100%', 'display': 'inline-block', 'margin-right': '5%'}
                        ),
                    ]),
                ], style={'width': '100%', 'max-width': '100%', 'margin-bottom': '20px'}),

                dbc.Container([
                    html.Label('Estimated Bodyweight in Kg..'),
                    html.Div([
                        dcc.Input(
                            id='bodyweight-filter-t2',
                            type='number',
                            placeholder='Bodyweight (Kg)',
                            style={'width': '100%', 'display': 'inline-block', 'margin-right': '5%'}
                        ),
                    ]),
                ], style={'width': '100%', 'max-width': '100%', 'margin-bottom': '20px'}),

                # Container for Federation filter
                dbc.Container([
                    html.Label('Please select a Federation..'),
                    dcc.Dropdown(
                        id='federation-filter-t2',
                        options=[{'label': Federation, 'value': Federation} for Federation in
                                 sorted(df['Federation'].unique()) if
                                 Federation is not None],
                        multi=True,
                        placeholder='Select Federation...',
                        style={'width': '100%', 'max-width': '100%', 'margin-bottom': '20px',
                               'background-color': 'transparent',
                               'color': 'black'}
                    ),
                ], style={'width': '100%', 'max-width': '100%', 'margin-bottom': '20px'}),

                dbc.Container([
                    html.Label('Please select a State..'),
                    dcc.Dropdown(
                        id='user-state-t2',
                        options=[{'label': state, 'value': state} for state in
                                 sorted(filter(None, df['MeetState'].unique())) if
                                 state is not None],
                        multi=True,
                        placeholder='Select State...',
                        style={'width': '100%', 'max-width': '100%', 'margin-bottom': '20px',
                               'background-color': 'transparent',
                               'color': 'black'}
                    ),
                ], style={'width': '100%', 'max-width': '100%', 'margin-bottom': '20px'}),

                html.Div(
                    dbc.Button(
                        children=[
                            html.Div('Calculate',
                                     style=dict(paddingRight='0.3vw', display='inline-block', verticalAlign='bottom',
                                                marginTop='-8px', fontSize='2.5vh')),
                            html.I(className='fa-solid fa-square-poll-vertical',
                                   style=dict(display='inline-block', verticalAlign='center', lineHeight='0.8',
                                              marginRight='5px', fontSize='2.5vh')),
                        ],
                        id='calculate-button',
                        n_clicks=0,
                        size='md',
                        style=dict(
                            fontSize='1.7vh',
                            backgroundColor='rgba(0, 0, 0, 0)',
                            textAlign='center',
                            height='32px',
                            border='none'
                        )
                    ),
                    style=dict(display='flex', justifyContent='flex-start', alignItems='center')
                ),

                html.Br(),
                html.Br(),

                dbc.Container([
                    html.Label('Your Estimated Strength Level is..'),
                    html.Div(
                        id='kpi-box',
                        children=[
                            html.Div(
                                id='kpi-text',
                                children="",
                                style={
                                    'background-color': 'white',
                                    'border-radius': '10px',
                                    'padding': '20px',
                                    'text-align': 'center',
                                    'box-shadow': '0 0 10px rgba(0, 0, 0, 0.1)',
                                    'font-size': '18px',
                                    'font-weight': 'bold',
                                    'color': 'black',
                                    'margin-top': '10px'
                                    #'visibility': 'hidden',  # Initial visibility set to hidden
                                }
                            ),
                        ],
                        style={'width': '100%', 'max-width': '100%', 'margin-bottom': '20px'}  # Optional: Add margin for better spacing
                    ),
                ])

                # Container for Total range filter
            ], width=2, style={'height': '100vh'}),  # Set the width to 4 (1/3 of the screen)

            # Column for the plot
            dbc.Col([
                # Add your plot component here
                html.Div([
                    dcc.Graph(
                        id='distribution-plot-t2',
                        # Add plot properties and data here
                    style={'height': '80vh'}),
                ], id='distribution-plot-container-t2', style={'height': '100%', 'display': 'none'})
            ], width=10,  style={'height': '100vh'}),  # Set the width to 8 (2/3 of the screen)
        ]),
        dcc.Store(id='kpi-store', storage_type='memory', data={'kpi_text': ''})

        # Blank container for additional content (to be filled with KPI later)
        #dbc.Container(id='additional-content-container', className='p-3'),
    ], style={'height': '100vh'})

def render_user_stats():
    return html.Div([
        html.H3('User Stats Analysis', style={'color': text_color}),
        html.P('This tab allows users to benchmark their current Squat, Bench and Deadlift maxes against actual competitors.',
               style={'color': text_color}),
        html.Div(id='output-container', className='callout-container'),
        html.Div(id='output-container-2', className='callout-container'),

        dcc.Dropdown(
            id='federation-filter',
            options=[{'label': Federation, 'value': Federation} for Federation in sorted(df['Federation'].unique()) if
                     Federation is not None],
            multi=True,
            placeholder='Select Federation...',
            style={'width': '49%', 'margin': '0 10px 10px 0', 'background-color': 'transparent', 'color': 'black'}
        ),
        html.Div([
            html.Label('Lbs:'),
            daq.BooleanSwitch(
                id='lbs-switch-t3',
                on=False,
                labelPosition="top",
                color='#008000'
            ),
        ], style={'display': 'flex', 'gap': '10px', 'justify-content': 'flex-start'}),
        dcc.RadioItems(
            id='sex-filter',
            options=[{'label': 'Male', 'value': 'M'}, {'label': 'Female', 'value': 'F'},
                     {'label': 'Mx', 'value': 'Mx'}],
            labelStyle={'display': 'inline', 'margin-right': '10px'},
            style={'background-color': 'transparent', 'margin-bottom': '10px'}
        ),
        html.Button('Tested', id='tested-button', n_clicks=0),

        dcc.Input(id='name-input', type='text', placeholder='Enter Name'),
        dcc.Input(id='age-input', type='number', placeholder='Enter Age'),
        dcc.Input(id='weight-input', type='number', placeholder='Enter Weight'),
        dcc.Input(id='squat-input', type='number', placeholder='Competition Squat'),
        dcc.Input(id='bench-input', type='number', placeholder='Competition bench Press'),
        dcc.Input(id='deadlift-input', type='number', placeholder='Competition Deadlift'),
        #html.Button('Add Data', id='add-data-button'),
        dbc.Button(
            children=[
                html.I(className='fa-solid fa-plus', style=dict(display='inline-block', verticalAlign='top', lineHeight='0.8', marginRight='5px')),
                html.Div('Add Data', style=dict(paddingRight='0.3vw', display='inline-block', verticalAlign='top', marginTop='-8px'))
            ],
            id='add-data-button',
            n_clicks=0,
            size='md',
            style=dict(fontSize='1.7vh', backgroundColor='rgba(0, 0, 0, 0)', textAlign='center', height='32px', marginTop='-5px', border='none')
        ),
        dbc.Button(
            children=[
                html.I(className='fa-solid fa-eraser',
                       style=dict(display='inline-block', verticalAlign='top', lineHeight='0.8', marginRight='5px')),
                html.Div('Clear Data', style=dict(paddingRight='0.3vw', display='inline-block', verticalAlign='top',
                                                 marginTop='-8px', color = 'red'))
            ],
            id='clear-data-button',
            n_clicks=0,
            size='md',
            style=dict(fontSize='1.7vh', backgroundColor='rgba(0, 0, 0, 0)', textAlign='center', height='32px',
                       marginTop='-5px', border='none')
        ),
        html.Div(id='output-container-3', className='callout-container'),

        html.Div([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            kpi_one(),
                            html.Div(style={'height': '0.2in'}),
                            dcc.Graph(
                                id='squat_indicator_chart',
                                figure=go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=0,  # Initial value, it will be updated dynamically
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "Squat"},
                                    gauge=dict(
                                        axis=dict(range=[0, 100]),  # Assuming percentiles from 0 to 100
                                        bar=dict(color="blue"),
                                    )
                                )),
                                style={'display': 'none'}
                            ),
                        ], width=4),
                        dbc.Col([
                            kpi_two(),
                            html.Div(style={'height': '0.2in'}),
                            dcc.Graph(
                                id='bench_indicator_chart',
                                figure=go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=0,  # Initial value, it will be updated dynamically
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "Bench"},
                                    gauge=dict(
                                        axis=dict(range=[0, 100]),  # Assuming percentiles from 0 to 100
                                        bar=dict(color="blue"),
                                    )
                                )),
                                style={'display': 'none'}
                            ),
                        ], width=4),
                        dbc.Col([
                            kpi_three(),
                            html.Div(style={'height': '0.2in'}),
                            dcc.Graph(
                                id='deadlift_indicator_chart',
                                figure=go.Figure(go.Indicator(
                                    mode="gauge+number",
                                    value=0,  # Initial value, it will be updated dynamically
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "Deadlift"},
                                    gauge=dict(
                                        axis=dict(range=[0, 100]),  # Assuming percentiles from 0 to 100
                                        bar=dict(color="blue"),
                                    )
                                )),
                                style={'display': 'none'}
                            )
                        ], width=4),
                    ], align='center'),
                ])
            ], className='mb-2', style={
                'backgroundColor': 'rgba(0,0,0,0)',
                'color': 'white',
                'text-align': 'center'
            })
        ], className="row"),
    ])


def render_comparative_analysis():
    return html.Div([
        html.H3('Lifter Analytics', style={'color': text_color}),
        html.P('This tab allows the user to display competitors performance based on Date, Weight (kg), or Age.',
               style={'color': text_color}),
        dcc.Markdown('**Note: Due to the absence of unique identifiers in competition data, individuals with the same name may not be fully distinguished. We are actively working to enhance this feature for accuracy'),
        html.Div([
            html.Div([
                html.P('Please select a Gender: '),
                dcc.RadioItems(
                    id='sex-filter-t3',
                    options=[{'label': 'Male', 'value': 'M'}, {'label': 'Female', 'value': 'F'},
                             {'label': 'Mx', 'value': 'Mx'}],
                    labelStyle={'display': 'inline', 'margin-right': '10px'},
                    style={'background-color': 'transparent', 'margin-bottom': '10px', 'margin-left': '10px'}
                ),
                html.P('Please select a Lifter: '),
                dcc.Dropdown(
                    id='comp-lifter-filter',
                    options=[{'label': 'Lifter 1', 'value': 'lifter1'}, {'label': 'Lifter 2', 'value': 'lifter2'}],
                    multi=False,
                    placeholder='Select Lifter...',
                    style={'width': '25%', 'margin-bottom': '10px', 'background-color': 'transparent', 'color': 'black'},
                ),
            ]),
            html.Div([
                html.Div(id='player-card-1-container', style={'width': '45%', 'display': 'inline-block'}),
                html.Div(id='player-card-2-container', style={'width': '45%', 'display': 'inline-block'}),
            ], style={'width': '90%', 'display': 'flex', 'justify-content': 'center', 'gap': '20px'}),
        ]),
    ])

@app.callback(Output('tab-content', 'children'), [Input('tabs', 'active_tab')])
def render_content(active_tab):
    if active_tab == 'landing-page':
        return render_landing_page()
    elif active_tab == 'comp-data':
        return render_comp_data()
    elif active_tab == 'user-stats':
        return render_user_stats()
    elif active_tab == 'tab-comparative-analysis':
        return render_comparative_analysis()
    else:
        return html.Div([])

''' Landing Page Tab'''
##need to add button functionalitty here


''' Competition Data Tab '''

@app.callback(
    [Output('weightclass-filter', 'options'),
     Output('ageclass-filter', 'options')],
    [Input('federation-dropdown-filter', 'value'),
     Input('sex-filter', 'value')]
)
def update_dropdown_options(selected_federation, selected_sex):
    if selected_federation is None or selected_sex is None:
        # If either federation or sex is not selected, return no options for weightclass and ageclass
        weightclass_options = []
        ageclass_options = []
    else:
        # Filter options based on both selected federation and sex
        subset_df = df[(df['Federation'].isin(selected_federation)) & (df['Sex'] == selected_sex)]
        weightclass_options = [{'label': weightClass, 'value': weightClass} for weightClass in sorted(subset_df['WeightClassKg'].unique(), key=float) if weightClass is not None]
        ageclass_options = [{'label': ageClass, 'value': ageClass} for ageClass in sorted(subset_df['AgeClass'].unique()) if ageClass is not None]

    return weightclass_options, ageclass_options

@app.callback(
    Output('data-table-container', 'children'),
    Input('load-data-button', 'n_clicks'),
    State('weightclass-filter', 'value'),
    State('ageclass-filter', 'value'),
    State('sex-filter', 'value'),
    State('federation-dropdown-filter', 'value')
)
def load_and_filter_data(n_clicks, selected_weightclasses, selected_ageclasses, selected_sex, selected_federation):
    if n_clicks:
        print("Selected Weight Classes:", selected_weightclasses)
        print("Selected Age Classes:", selected_ageclasses)
        print("Selected Sex:", selected_sex)
        print("Selected Federation:", selected_federation)

        highlight_condition = [
            {'backgroundColor': 'rgba(8,43,55,255)', 'color': 'white'}
        ]

        if selected_weightclasses is not None and selected_ageclasses is not None and selected_sex is not None and selected_federation is not None:
            # Filter the data based on selections
            filtered_df = df[df['WeightClassKg'].isin(selected_weightclasses) & df['AgeClass'].isin(selected_ageclasses) & (df['Sex'] == selected_sex) & df['Federation'].isin(selected_federation)]

            # Populate the filtered data in the DataTable
            return dash_table.DataTable(filtered_df.to_dict('records'), [{"name": i, "id": i} for i in filtered_df.columns], page_size=10,
                                        style_data={'backgroundColor': 'rgba(0,0,0,0)', 'color': 'white'},
                                        style_header={'backgroundColor': 'rgba(0,0,0,0)', 'color': 'white'},
                                        style_data_conditional=highlight_condition,
                                        style_header_conditional=highlight_condition)

    # Initially, return an empty div
    return html.Div()


@app.callback(
    [Output('kpi-text', 'children'),
     Output('kpi-box', 'style')],
    [Input('calculate-button', 'n_clicks'),
     Input('lbs-switch-t2', 'on')],
    [State('sex-filter-t2', 'value'),
     State('total-filter', 'value'),
     State('bodyweight-filter-t2', 'value')]
)
def update_kpi_text(n_clicks, switch, gender, total, bw):

    if n_clicks:
        if switch:
            wilks_e = calculate_wilks(gender=gender, total=total, bodyweight=bw, lbs = True)
            print('On: ', wilks_e)
        else:
            wilks_e = calculate_wilks(gender=gender, total=total, bodyweight=bw, lbs = False)
            print('Off: ', wilks_e)

        kpi_value = classify_wilks(wilks_e)

        # Format the KPI value as text
        kpi_text = f"KPI: {kpi_value}"

        if len(user_total_dist) > 0:
            user_total_dist.clear()
            user_total_dist.append(wilks_e)
        else:
            user_total_dist.append(wilks_e)

        # Make the box visible
        updated_style = {'visibility': 'visible'}
    else:
        # If button is not clicked, keep the box hidden
        kpi_text = ""
        updated_style = {'visibility': 'hidden'}

    return kpi_text, updated_style


@app.callback(
    [Output('distribution-plot-t2', 'figure'),
     Output('distribution-plot-container-t2', 'style')],
    [Input('calculate-button', 'n_clicks')],
     [State('federation-filter-t2', 'value'),
     State('user-state-t2', 'value'),
     State('sex-filter-t2', 'value'),
     State('total-filter', 'value'),
     State('bodyweight-filter-t2', 'value')]
)
def create_wilks_distribution(n_clicks, federation, location, gender, total, bw):

    if n_clicks:

        wilks_df = df[(df['Federation'].isin(federation)) & (df['MeetState'].isin(location))]
        print(len(wilks_df))
        wilks_df = wilks_df.dropna(subset=['Wilks']).replace('', np.nan).dropna(subset=['Wilks'])
        print(len(wilks_df))

        if not wilks_df.empty:
            kpi_val = round(user_total_dist[0],2)

            fig = ff.create_distplot([wilks_df['Wilks']], group_labels=['Wilks Score'], colors=['white'],
                                     show_hist=True, bin_size=0)

            strength_levels = {100: 'Beginner', 300: 'Intermediate', 400: 'Advanced', 500: 'Elite'}
            colors = {'Beginner': '#FCD5D1', 'Intermediate': '#FB9D98', 'Advanced': '#F76D66', 'Elite': '#F43939'}

            for value, level in strength_levels.items():
                fig.add_vline(x=value, line=dict(color=colors[level], width=2),
                              annotation_text=f'Strength Level: {level}', annotation_position="top",
                              annotation_font=dict(color=colors[level]))

            fig.add_vline(x=kpi_val, line=dict(color='green', width=2),
                          annotation_text=f'Your Wilks Score: {kpi_val}', annotation_position="bottom",
                          annotation_font=dict(color='green'))

            # Customize the layout
            fig.update_layout(
                title='Wilks Distribution',
                xaxis_title='Wilks Score',
                yaxis_title='Density',
                showlegend=True,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                font=dict(color='white'),  # Set font color to white
            )

            updated_style = {'display': 'block', 'height': '100%'}
        else:
            fig = go.Figure()
            updated_style = {'display': 'none'}

        return fig, updated_style
    else:
        #updated_style = {'visibility': 'hidden'}
        updated_style = {'display': 'none'}
        return go.Figure(), updated_style


''' User Stats Tab '''
@app.callback(
    [Output('squat-input', 'value'),
     Output('bench-input', 'value'),
     Output('deadlift-input', 'value'),
     Output('age-input', 'value'),
     Output('weight-input', 'value')],
    [Output('add-data-button', 'n_clicks')],
    [Input('clear-data-button', 'n_clicks')],
    prevent_initial_call=True
)
def clear_input_values(n_clicks_clear):
    if n_clicks_clear is None:
        # If the clear button is not clicked, do nothing
        raise dash.exceptions.PreventUpdate
    else:
        user_data.clear()
        user_data_perc.clear()

    # Clear the values of the input components
    return None, None, None, None, None, 0  # Set n_clicks to 0

@app.callback(
    Output('tested-button', 'style'),
    Input('tested-button', 'n_clicks')
)
def update_tested_button(n_clicks):
    if n_clicks and n_clicks % 2 == 0:
        tested_button_style = {
            'borderRadius': '12px',
            'background-color': 'rgba(0, 255, 0, 0.5) ',
            'color': 'white',
            'height': '30px',  # set the height of the buttons
            'width': '90px',  # set the width of the buttons
        }
    else:
        tested_button_style = {
            'borderRadius': '12px',
            'background-color': 'rgba(211, 211, 211, 0.5)',
            'color': 'white',
            'height': '30px',  # set the height of the buttons
            'width': '90px',  # set the width of the buttons
        }

    return tested_button_style

#Define callback to add user data to the list
@app.callback(
    Output('squat_vals', 'children'),
    Output('bench_vals', 'children'),
    Output('deadlift_vals', 'children'),
    Output('output-container', 'children'),
    Output('output-container-2', 'children'),
    Output('output-container-3', 'children'),
    Input('tested-button', 'n_clicks'),
    Input('federation-filter', 'value'),
    Input('sex-filter', 'value'),
    Input('add-data-button', 'n_clicks'),
    Input('lbs-switch-t3', 'on'),
    State('name-input', 'value'),
    State('age-input', 'value'),
    State('weight-input', 'value'),
    State('squat-input', 'value'),
    State('bench-input', 'value'),
    State('deadlift-input', 'value'),
)
def add_user_data_calculation(tested, federation, sex, n_clicks, lbs_switch, name, age, weight, squat, bench, deadlift):

    if n_clicks:
        if name and age and weight and federation:
            if lbs_switch:
                user_data.update(
                    {'Name': name, 'Age': age, 'BodyweightKg': weight / float(2.2), 'Best3SquatKg': squat,
                     'Best3BenchKg': bench,
                     'Best3DeadliftKg': deadlift})
            else:
                user_data.update(
                    {'Name': name, 'Age': age, 'BodyweightKg': weight, 'Best3SquatKg': squat, 'Best3BenchKg': bench,
                     'Best3DeadliftKg': deadlift})

            if tested % 2 == 0:

                df_weight_match = df[df['Federation'].isin(federation) & (df['Sex'] == sex) & (df['Tested'] == 'Yes')]
                closest_lower_weight_class = df_weight_match.loc[
                    (df_weight_match['BodyweightKg'] - user_data['BodyweightKg']).abs().idxmin(),
                    'WeightClassKg'
                ]

                closest_age_class = df_weight_match.loc[
                    (df_weight_match['Age'] - user_data['Age']).abs().idxmin(),
                    'AgeClass'
                ]

                filtered_df = df[df['Federation'].isin(federation) & (df['Sex'] == sex) & (
                            df['WeightClassKg'] == closest_lower_weight_class) & (df['Tested'] == 'Yes') & (
                                            df['AgeClass'] == closest_age_class)]

                if len(lifter_count) > 0:
                    lifter_count.pop()
                    lifter_count.append(len(filtered_df))
                else:
                    lifter_count.append(len(filtered_df))

                estimated_comp_class.update({'ageclass': closest_age_class, 'weightclass': closest_lower_weight_class})

            else:
                df_weight_match = df[df['Federation'].isin(federation) & (df['Sex'] == sex)]
                closest_lower_weight_class = df_weight_match.loc[
                    (df_weight_match['BodyweightKg'] - user_data['BodyweightKg']).abs().idxmin(),
                    'WeightClassKg'
                ]

                closest_age_class = df_weight_match.loc[
                    (df_weight_match['Age'] - user_data['Age']).abs().idxmin(),
                    'AgeClass'
                ]

                filtered_df = df[df['Federation'].isin(federation) & (df['Sex'] == sex) & (
                            df['WeightClassKg'] == closest_lower_weight_class) & (df['AgeClass'] == closest_age_class)]

                if len(lifter_count) > 0:
                    lifter_count.pop()
                    lifter_count.append(len(filtered_df))
                else:
                    lifter_count.append(len(filtered_df))

                estimated_comp_class.update({'ageclass': closest_age_class, 'weightclass': closest_lower_weight_class})

            df_grouped = filtered_df.groupby('Name').agg(squat=('Best3SquatKg', 'max'),
                                                         bench=('Best3BenchKg', 'max'),
                                                         deadlift=('Best3DeadliftKg', 'max'),
                                                         wilks=('Wilks', 'max')
                                                         ).reset_index()


            squat_perc, bench_perc, deadlift_perc = None, None, None
            if squat:
                if lbs_switch:
                    df_grouped['squat'] = df_grouped['squat'].fillna(0)
                    squat_perc = percentileofscore(df_grouped['squat'], user_data['Best3SquatKg'] / float(2.2))
                    squat_perc_rounded = '{:.1%}'.format(squat_perc / 100)
                    squat_perc_val = squat_perc
                    user_data_perc.update({'squat_perc': squat_perc_val})
                else:
                    df_grouped['squat'] = df_grouped['squat'].fillna(0)
                    squat_perc = percentileofscore(df_grouped['squat'], user_data['Best3SquatKg'])
                    squat_perc_rounded = '{:.1%}'.format(squat_perc / 100)
                    squat_perc_val = squat_perc
                    user_data_perc.update({'squat_perc': squat_perc_val})

            if bench:
                if lbs_switch:
                    df_grouped['bench'] = df_grouped['bench'].fillna(0)
                    bench_perc = percentileofscore(df_grouped['bench'], user_data['Best3BenchKg'] / float(2.2))
                    bench_perc_rounded = '{:.1%}'.format(bench_perc / 100)
                    bench_perc_val = bench_perc
                    user_data_perc.update({'bench_perc': bench_perc_val})
                else:
                    df_grouped['bench'] = df_grouped['bench'].fillna(0)
                    bench_perc = percentileofscore(df_grouped['bench'], user_data['Best3BenchKg'])
                    bench_perc_rounded = '{:.1%}'.format(bench_perc / 100)
                    bench_perc_val = bench_perc
                    user_data_perc.update({'bench_perc': bench_perc_val})

            if deadlift:
                if lbs_switch:
                    df_grouped['deadlift'] = df_grouped['deadlift'].fillna(0)
                    deadlift_perc = percentileofscore(df_grouped['deadlift'], user_data['Best3DeadliftKg'] / float(2.2))
                    deadlift_perc_rounded = '{:.1%}'.format(deadlift_perc / 100)
                    deadlift_perc_val = deadlift_perc
                    user_data_perc.update({'deadlift_perc': deadlift_perc_val})
                else:
                    df_grouped['deadlift'] = df_grouped['deadlift'].fillna(0)
                    deadlift_perc = percentileofscore(df_grouped['deadlift'], user_data['Best3DeadliftKg'])
                    deadlift_perc_rounded = '{:.1%}'.format(deadlift_perc / 100)
                    deadlift_perc_val = deadlift_perc
                    user_data_perc.update({'deadlift_perc': deadlift_perc_val})

            if len(federation) == 1:
                federation = federation[0]
            else:
                federation = ', '.join(str(x) for x in federation)

            output1 = [
                html.Div([
                    html.H5(f'Current Weight Class in {federation}: {estimated_comp_class.get("weightclass", 0)} Kg',
                            className='callout-content', style={'color': 'red'})
                ], className='callout'),
            ]
            output2 = [
                html.Div([
                    html.H5(f'Current Age Class in {federation}: {estimated_comp_class.get("ageclass", 0)}',
                            className='callout-content', style={'color': 'red'})
                ], className='callout'),
            ]

            output3 = [
                html.Div([
                    html.H5(f'Comparison based on performance among {lifter_count[0]} other lifters',
                            className='callout-content', style={'color': 'red'})
                ], className='callout'),
            ]

            return squat_perc_rounded, bench_perc_rounded, deadlift_perc_rounded, output1, output2, output3

        else:
            return "Please enter both name and age", name, age, '', '', ''
    return '', '', '', '', '', ''


@app.callback(
    [Output('squat_indicator_chart', 'figure'),
     Output('squat_indicator_chart', 'style')],
    [Input('add-data-button', 'n_clicks')],
    [Input('squat_vals', 'children')]
)
def update_squat_chart(n_clicks, squat_vals):
    if n_clicks is None:

        return go.Figure(), {'display': 'none'}

    squat_percentile = user_data_perc.get('squat_perc', 0)

    if squat_percentile:

        squat_figure = go.Figure(go.Indicator(
            mode="gauge+number",
            value=squat_percentile,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Squat", 'font': {'color': 'white'}},
            gauge=dict(
                axis=dict(range=[0, 100], tickfont={'color': 'white'}),
                #bar=dict(color="rgba(104,111,254,255)"),
                bar=dict(color="rgba(255, 255, 255, 1)"),
                bgcolor="rgba(0, 0, 0, 0)"
            ),
            number={'font': {'color': 'white'}, 'suffix':"%"}
        ))

        squat_figure.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )


        squat_style = {'display': 'block'}

        return squat_figure, squat_style

    else:

        return go.Figure(), {'display': 'none'}



@app.callback(
    [Output('bench_indicator_chart', 'figure'),
     Output('bench_indicator_chart', 'style')],
    [Input('add-data-button', 'n_clicks')],
    [Input('bench_vals', 'children')]
)
def update_bench_chart(n_clicks, squat_vals):
    if n_clicks is None:

        return go.Figure(), {'display': 'none'}


    bench_percentile = user_data_perc.get('bench_perc', 0)

    if bench_percentile:

        bench_figure = go.Figure(go.Indicator(
            mode="gauge+number",
            value=bench_percentile,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Bench", 'font': {'color': 'white'}},
            gauge=dict(
                axis=dict(range=[0, 100], tickfont={'color': 'white'}),
                #bar=dict(color="rgba(104,111,254,255)"),
                bar=dict(color="rgba(255, 255, 255, 1.0)"),
                bgcolor="rgba(0, 0, 0, 0)"
            ),
            number={'font': {'color': 'white'}, 'suffix':"%"}
        ))

        bench_figure.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )

        # Show the chart by updating the style property
        bench_style = {'display': 'block'}

        return bench_figure, bench_style

    else:

        return go.Figure(), {'display': 'none'}


@app.callback(
    [Output('deadlift_indicator_chart', 'figure'),
     Output('deadlift_indicator_chart', 'style')],
    [Input('add-data-button', 'n_clicks')],
    [Input('deadlift_vals', 'children')]
)
def update_deadlift_chart(n_clicks, squat_vals):
    if n_clicks is None:

        return go.Figure(), {'display': 'none'}


    deadlift_percentile = user_data_perc.get('deadlift_perc', 0)

    if deadlift_percentile:

        deadlift_figure = go.Figure(go.Indicator(
            mode="gauge+number",
            value=deadlift_percentile,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Deadlift", 'font': {'color': 'white'}},
            gauge=dict(
                axis=dict(range=[0, 100], tickfont={'color': 'white'}),
                #bar=dict(color="rgba(104,111,254,255)"),
                bar=dict(color="rgba(255, 255, 255, 1.0)"),
                bgcolor="rgba(0, 0, 0, 0)"
            ),
            number={'font': {'color': 'white'}, 'suffix':"%"}
        ))

        deadlift_figure.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )


        deadlift_style = {'display': 'block'}

        return deadlift_figure, deadlift_style

    else:

        return go.Figure(), {'display': 'none'}


'''Lifter Competition Analytics'''

@app.callback(
    [Output('comp-lifter-filter', 'options')],
    [Input('sex-filter-t3', 'value')]
)
def update_dropdown_options(selected_gender):

    if selected_gender is None:
        return [[]]

    subset_df = df[(df['Sex'] == selected_gender) & (df['Event'] == 'SBD')]
    print(user_data)


    comp_lifter_filter = [{'label': Lifter, 'value': Lifter} for Lifter in subset_df['Name'].unique()]

    return [comp_lifter_filter]

@app.callback(
    Output('times-competed-kpi', 'children'),
    [Input('comp-lifter-filter', 'value')]
)
def update_kpi_competitions(selected_lifter):

    competition_df = df

    if selected_lifter is None:
        competition_cnt = f'''Please select a lifter'''
    else:
        competition_lifter_df = competition_df[(competition_df['Name'] == selected_lifter) & (competition_df['Event'] == 'SBD')]


        if len(competition_lifter_df) != 0:

            competition_cnt = competition_lifter_df.groupby(['MeetName', 'Date']).size().reset_index(name='Count').shape[0]

            # unique_lifter_validation = clean_same_names(competition_lifter_df, 1)
            unique_lifter_validation = clean_same_names(competition_lifter_df)
            if unique_lifter_validation['persona'].nunique() > 1:
                competition_cnt = 'Identified more than one lifter'


        else:

            competition_cnt = 0


    return competition_cnt


@app.callback(
    Output('placement-kpi', 'children'),
    [Input('comp-lifter-filter', 'value')]
)
def update_highest_placement(selected_lifter):

    competition_df = df

    if selected_lifter is None:
        highest_placement = "Please select a lifter"
    else:
        placement_lifter_df = competition_df[
            (competition_df['Name'] == selected_lifter) & (competition_df['Event'] == 'SBD')]

        if not placement_lifter_df.empty:

            num_values = pd.to_numeric(placement_lifter_df['Place'], errors='coerce')
            highest_placement = num_values.min()

            #unique_lifter_validation = clean_same_names(placement_lifter_df, 1)
            unique_lifter_validation = clean_same_names(placement_lifter_df)
            if unique_lifter_validation['persona'].nunique() > 1:
                highest_placement = 'Identified more than one lifter'


            if highest_placement == 1 and len(placement_lifter_df) == 1:
                meetname, meetdate = placement_lifter_df.iloc[0]['MeetName'], placement_lifter_df.iloc[0]['Date']

                multiple_lifters = len(competition_df[(competition_df['MeetName'] == meetname) & (
                            competition_df['Date'] == meetdate) & (competition_df['Event'] == 'SBD')]) > 1

                if not multiple_lifters:
                    highest_placement = f"{highest_placement} *"

        else:
            highest_placement = "N/A"

    return highest_placement


@app.callback(
    Output('line-chart', 'figure'),
    Output('line-chart', 'style'),
    [Input('comp-lifter-filter', 'value'),
     Input('view-selection', 'value')]
)
def update_line_chart(selected_lifter, view_type):
    if selected_lifter is None:
        return px.line(title='Line Chart'), {'display': 'none'}

    lifter_stats_df = df

    if view_type == 'date':
        cols = ['Date', 'MeetName']

        lifter_stats_df = lifter_stats_df[(lifter_stats_df['Name'] == selected_lifter) & (lifter_stats_df['Event'] == 'SBD')]
        lifter_stats_df = lifter_stats_df.drop_duplicates(subset=cols)


        unique_lifter_validation = clean_same_names(lifter_stats_df)
        if unique_lifter_validation['persona'].nunique() > 1:
            cols.append('name_with_persona')
            lifter_stats_df = clean_same_names(lifter_stats_df)

        lifter_stats_df_agg = lifter_stats_df.groupby(cols).agg({'Best3SquatKg': 'sum', 'Best3BenchKg': 'sum', 'Best3DeadliftKg': 'sum'}).reset_index()
        lifter_stats_df_agg[['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']] = lifter_stats_df_agg[
            ['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']].astype(float)

        facet_col_expression = f'name_with_persona' if 'name_with_persona' in cols else None


        line_chart_date = px.line(
            lifter_stats_df_agg,
            x='Date',
            y=['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg'],
            facet_col=facet_col_expression,
            facet_col_wrap=7,
            title=f'Competition Performance by Date for {selected_lifter}',
            markers=True,
            line_shape='linear',
            hover_data = {'MeetName': True}
        )

        line_color_white_rgba = 'rgba(255, 255, 255, 1.0)'
        line_color_light_blue_rgba = 'rgba(144, 238, 144, 1.0)'
        line_color_cyan_rgba = 'rgba(0, 255, 255, 1.0)'

        line_chart_date.update_traces(
            line_color=line_color_white_rgba,
            selector={'name': 'Best3SquatKg'}
        )
        line_chart_date.update_traces(
            line_color=line_color_light_blue_rgba,
            selector={'name': 'Best3BenchKg'}
        )
        line_chart_date.update_traces(
            line_color=line_color_cyan_rgba,
            selector={'name': 'Best3DeadliftKg'}
        )

        line_chart_date.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            hovermode='x'
        )

        line_chart_date.update_layout(
            xaxis_title='Date',
            yaxis_title='Weight (Kg)'
        )

        line_chart_date.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

        for i in range(1, len(line_chart_date.data) + 1):
            line_chart_date.update_xaxes(matches=f'x{i}', showgrid=False)
            line_chart_date.update_yaxes(matches=f'y{i}', showgrid=False)


        return line_chart_date, {'display': 'block'}

    elif view_type == 'weight':
        cols = ['BodyweightKg', 'MeetName', 'Date']


        lifter_stats_df = lifter_stats_df[(lifter_stats_df['Name'] == selected_lifter) & (lifter_stats_df['Event'] == 'SBD')]
        lifter_stats_df = lifter_stats_df.drop_duplicates(subset=cols)

        unique_lifter_validation = clean_same_names(lifter_stats_df)
        if unique_lifter_validation['persona'].nunique() > 1:
            cols.append('name_with_persona')
            lifter_stats_df = clean_same_names(lifter_stats_df)

        lifter_stats_df_agg = lifter_stats_df.groupby(cols).agg({'Best3SquatKg': 'sum', 'Best3BenchKg': 'sum', 'Best3DeadliftKg': 'sum'}).reset_index()
        lifter_stats_df_agg[['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']] = lifter_stats_df_agg[
            ['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']].astype(float)

        facet_col_expression = f'name_with_persona' if 'name_with_persona' in cols else None

        line_chart_weight = px.line(
            lifter_stats_df_agg,
            x='BodyweightKg',
            y=['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg'],
            facet_col=facet_col_expression,
            facet_col_wrap=7,
            title=f'Competition Performance by Weight (Kg) for {selected_lifter}',
            markers=True,
            line_shape='linear',
            hover_data={'MeetName': True, 'Date': True}
        )

        line_color_white_rgba = 'rgba(255, 255, 255, 1.0)'
        line_color_light_blue_rgba = 'rgba(144, 238, 144, 1.0)'
        line_color_cyan_rgba = 'rgba(0, 255, 255, 1.0)'

        line_chart_weight.update_traces(
            line_color=line_color_white_rgba,
            selector={'name': 'Best3SquatKg'}
        )
        line_chart_weight.update_traces(
            line_color=line_color_light_blue_rgba,
            selector={'name': 'Best3BenchKg'}
        )
        line_chart_weight.update_traces(
            line_color=line_color_cyan_rgba,
            selector={'name': 'Best3DeadliftKg'}
        )

        line_chart_weight.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            hovermode='x'
        )

        line_chart_weight.update_layout(
            xaxis_title='Bodyweight (Kg)',
            yaxis_title='Weight (Kg)'
        )

        line_chart_weight.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

        for i in range(1, len(line_chart_weight.data) + 1):
            line_chart_weight.update_xaxes(matches=f'x{i}', showgrid=False)
            line_chart_weight.update_yaxes(matches=f'y{i}', showgrid=False)

        return line_chart_weight, {'display': 'block'}

    elif view_type == 'age':
        cols = ['Age', 'MeetName', 'Date']

        lifter_stats_df = lifter_stats_df[
            (lifter_stats_df['Name'] == selected_lifter) & (lifter_stats_df['Event'] == 'SBD')]
        lifter_stats_df = lifter_stats_df.drop_duplicates(subset=cols)

        unique_lifter_validation = clean_same_names(lifter_stats_df)
        if unique_lifter_validation['persona'].nunique() > 1:
            cols.append('name_with_persona')
            lifter_stats_df = clean_same_names(lifter_stats_df)

        lifter_stats_df_agg = lifter_stats_df.groupby(cols).agg(
            {'Best3SquatKg': 'sum', 'Best3BenchKg': 'sum', 'Best3DeadliftKg': 'sum'}).reset_index()
        lifter_stats_df_agg[['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']] = lifter_stats_df_agg[
            ['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']].astype(float)

        facet_col_expression = f'name_with_persona' if 'name_with_persona' in cols else None

        line_chart_age = px.line(
            lifter_stats_df_agg,
            x='Age',
            y=['Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg'],
            facet_col=facet_col_expression,
            facet_col_wrap=7,
            title=f'Competition Performance by Age for {selected_lifter}',
            markers=True,
            line_shape='linear',
            hover_data={'MeetName': True, 'Date': True}
        )

        line_color_white_rgba = 'rgba(255, 255, 255, 1.0)'
        line_color_light_blue_rgba = 'rgba(144, 238, 144, 1.0)'
        line_color_cyan_rgba = 'rgba(0, 255, 255, 1.0)'

        line_chart_age.update_traces(
            line_color=line_color_white_rgba,
            selector={'name': 'Best3SquatKg'}
        )
        line_chart_age.update_traces(
            line_color=line_color_light_blue_rgba,
            selector={'name': 'Best3BenchKg'}
        )
        line_chart_age.update_traces(
            line_color=line_color_cyan_rgba,
            selector={'name': 'Best3DeadliftKg'}
        )

        line_chart_age.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            hovermode='x'
        )

        line_chart_age.update_layout(
            xaxis_title='Age',
            yaxis_title='Weight (Kg)'
        )

        line_chart_age.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

        for i in range(1, len(line_chart_age.data) + 1):
            line_chart_age.update_xaxes(matches=f'x{i}', showgrid=False)
            line_chart_age.update_yaxes(matches=f'y{i}', showgrid=False)

        return line_chart_age, {'display': 'block'}

@app.callback(
    Output('player-card-1-container', 'children'),
    [Input('comp-lifter-filter', 'value')]
)
def update_player_card_1(selected_lifter):
    if selected_lifter:
        return html.Div([
            html.Img(src='player_image_url', style={'width': '100px', 'height': '100px'}),
            html.H3('Player Name 1'),
            html.P('Team: Team Name 1'),
            html.P('Position: Position Name 1'),
            html.P('Age: 25'),
            html.P('Height: 6\'2"'),
            html.P('Weight: 200 lbs'),
            html.P('Goals: 10'),
            html.P('Assists: 5'),
            html.P('Yellow Cards: 2'),
            html.P('Red Cards: 0'),
        ], style={'border': '1px solid white', 'padding': '10px', 'border-radius': '10px', 'text-align': 'center'})
    else:
        return html.Div()  # Empty div when no lifter is selected

@app.callback(
    Output('player-card-2-container', 'children'),
    [Input('comp-lifter-filter', 'value')]
)
def update_player_card_2(selected_lifter):
    if selected_lifter:
        lifter_stats_df = df
        lifter_stats_df = lifter_stats_df[(lifter_stats_df['Name'] == selected_lifter) & (lifter_stats_df['Event'] == 'SBD')]
        lifter_dict = lifter_stats_df.to_dict(orient='list')
        name = str(lifter_dict['Name'][0])
        min_age, max_age = min(lifter_dict['Age']), max(lifter_dict['Age'])
        weightclasses = lifter_dict['WeightClassKg']
        weightclasses_list = ', '.join(weightclasses)
        times_competed = len(lifter_dict)
        max_year = pd.to_datetime(max(lifter_dict['Date'], key=pd.to_datetime)).year
        active_flag = 'Yes' if max_year == datetime.datetime.now().year else 'No'
        best_squat_kg, best_squat_lbs = max(lifter_dict['Best3SquatKg']), round(max(lifter_dict['Best3SquatKg']) * 2.2, 1)
        best_bench_kg, best_bench_lbs = max(lifter_dict['Best3BenchKg']), round(max(lifter_dict['Best3BenchKg']) * 2.2, 1)
        best_deadlift_kg, best_deadlift_lbs = max(lifter_dict['Best3DeadliftKg']), round(max(lifter_dict['Best3DeadliftKg']) * 2.2, 1)

        unique_lifter_validation = clean_same_names(lifter_stats_df)
        warning = None
        if unique_lifter_validation['persona'].nunique() > 1:
            warning = f"Identified more than one unique lifter associated with this competitor's name."

        return html.Div([
            html.Img(src='player_image_url', style={'width': '100px', 'height': '100px'}),
            html.H3(f"{name}"),
            html.Br(),
            html.P(f"Currently Active: {active_flag}"),
            html.P(f"Age's Competed: {min_age} - {max_age} "),
            html.P(f"Weightclasses Competed: {weightclasses_list}"),
            html.P(f"Number of SBD competitions: {times_competed}"),
            html.P(f"Best Competition Squat: {best_squat_kg} (kg)/{best_squat_lbs} (lbs)"),
            html.P(f"Best Competition Bench: {best_bench_kg} (kg)/{best_bench_lbs} (lbs)"),
            html.P(f"Best Competition Deadlift: {best_deadlift_kg} (kg)/{best_deadlift_lbs} (lbs)")
        ], style={'border': '1px solid white', 'padding': '10px', 'border-radius': '10px', 'text-align': 'center'})
    else:
        return html.Div()  # Empty div when no lifter is selected

if __name__ == '__main__':
    app.run_server(debug=False, host= '0.0.0.0')
