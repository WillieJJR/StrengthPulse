import pandas as pd
import dash
from dash import dcc
from dash import html
from dash import dash_table
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
from scipy.stats import percentileofscore
from data_retrieval import retrieve_and_process_csv
from data_cleaning import remove_special_chars, convert_kg_to_lbs, apply_business_rules


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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR], suppress_callback_exceptions=True)

# Define colors
text_color = '#ffffff'
link_color = '#007bff'


app.layout = html.Div(children=[
    html.H1("StrengthPulse", style={'textAlign': 'center', 'color': text_color}),
    html.H3("How do you compare?", style={'textAlign': 'center', 'color': text_color}),

    dbc.Tabs(id='tabs', active_tab='tab-features', children=[
        dbc.Tab(label='Most Current Competition Data', tab_id='comp-data'),
        dbc.Tab(label='Personal Powerlifting Stats', tab_id='user-stats'),
        dbc.Tab(label='How do you Measure Up?', tab_id='tab-comparative-analysis'),
    ]),

    html.Div(id='tab-content', style={'margin-top': '20px'}),
])

df = retrieve_and_process_csv()
remove_special_chars(df)
df = convert_kg_to_lbs(df)
df = apply_business_rules(df)
user_data = {}
user_data_perc = {}
estimated_comp_class = {}

def render_comp_data():
    return html.Div([
        html.H3(f'Most recent competition data as of {datetime.now().date()} ', style={'color': text_color}),
        html.P('This tab provides exploration of the most up-to-date Powerlifting data available from openpowerlifting.org',
               style={'color': text_color}),
        dcc.Markdown('**Data needs to be filtered:** Filter the data by selecting filter criteria below.'),
        dcc.Dropdown(
            id='federation-dropdown-filter',
            options=[{'label': federation, 'value': federation} for federation in df['Federation'].unique()],
            multi=True,
            placeholder='Select Federation...',
            style={'width': '49%', 'margin': '0 10px 10px 0', 'background-color': 'transparent', 'color': 'black'}
        ),
        dcc.Dropdown(
            id='weightclass-filter',
            options=[{'label': weightClass, 'value': weightClass} for weightClass in df['WeightClassKg'].unique()],
            multi=True,
            placeholder='Select weight class (Kg)...',
            style={'width': '49%', 'margin': '0 10px 10px 0', 'background-color': 'transparent', 'color': 'black'}
        ),
        dcc.Dropdown(
            id='ageclass-filter',
            options=[{'label': ageClass, 'value': ageClass} for ageClass in df['AgeClass'].unique() if
                     ageClass is not None],
            multi=True,
            placeholder='Select age class...',
            style={'width': '49%', 'margin': '0 10px 10px 0', 'background-color': 'transparent', 'color': 'black'}
        ),
        html.P('Please select Gender'),
        dcc.RadioItems(
            id='sex-filter',
            options=[{'label': 'Male', 'value': 'M'}, {'label': 'Female', 'value': 'F'},
                     {'label': 'Mx', 'value': 'Mx'}],
            labelStyle={'display': 'inline', 'margin-right': '10px'},
            style={'background-color': 'transparent', 'margin-bottom': '10px'}
        ),
        html.Button('Load Data', id='load-data-button'),
        #'''Implement UI for a kg vs lb button here'''
        dcc.Loading(id="loading", type="default", children=[html.Div(id='data-table-container')]),
    ])


def render_user_stats():
    return html.Div([
        html.H3('Model Overview', style={'color': text_color}),
        html.P('This tab provides an explanation of the predictive model and its methodology.',
               style={'color': text_color}),
        html.Div(id='output-container', className='callout-container'),
        html.Div(id='output-container-2', className='callout-container'),

        dcc.Dropdown(
            id='federation-filter',
            options=[{'label': Federation, 'value': Federation} for Federation in df['Federation'].unique() if
                     Federation is not None],
            multi=True,
            placeholder='Select Federation...',
            style={'width': '49%', 'margin': '0 10px 10px 0', 'background-color': 'transparent', 'color': 'black'}
        ),
        html.Button('Lbs', id='lbs-button'),
        dcc.RadioItems(
            id='sex-filter',
            options=[{'label': 'Male', 'value': 'M'}, {'label': 'Female', 'value': 'F'},
                     {'label': 'Mx', 'value': 'Mx'}],
            labelStyle={'display': 'inline', 'margin-right': '10px'},
            style={'background-color': 'transparent', 'margin-bottom': '10px'}
        ),
        html.Button('Tested', id='tested-button', n_clicks=0),
        # dcc.RadioItems(
        #     id='tested-filter',
        #     options=[{'label': 'Tested', 'value': 'Yes'}, {'label': 'Not Known', 'value': 'Not Known'}],
        #     labelStyle={'display': 'inline', 'margin-right': '10px'},
        #     style={'background-color': 'transparent', 'margin-left': '4in'}  # Adjust margin-left for separation
        # ),

        dcc.Input(id='name-input', type='text', placeholder='Enter Name'),
        dcc.Input(id='age-input', type='number', placeholder='Enter Age'),
        dcc.Input(id='weight-input', type='number', placeholder='Enter Weight'),
        dcc.Input(id='squat-input', type='number', placeholder='Competition Squat'),
        dcc.Input(id='bench-input', type='number', placeholder='Competition bench Press'),
        dcc.Input(id='deadlift-input', type='number', placeholder='Competition Deadlift'),
        html.Button('Add Data', id='add-data-button'),

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
        html.H3('Price Predictor', style={'color': text_color}),
        html.P('This tab allows you to input values and see predictions for specific scenarios.',
               style={'color': text_color}),

    ])


@app.callback(Output('tab-content', 'children'), [Input('tabs', 'active_tab')])
def render_content(active_tab):
    if active_tab == 'comp-data':
        return render_comp_data()
    elif active_tab == 'user-stats':
        return render_user_stats()
    elif active_tab == 'tab-comparative-analysis':
        return render_comparative_analysis()
    else:
        return html.Div([])

@app.callback(
    [Output('weightclass-filter', 'options'),
     Output('ageclass-filter', 'options')],
    [Input('federation-dropdown-filter', 'value')]
)
def update_dropdown_options(selected_federation):
    if selected_federation is None:
        # If no federation is selected, return all options for weightclass and ageclass
        weightclass_options = [{'label': weightClass, 'value': weightClass} for weightClass in df['WeightClassKg'].unique()]
        ageclass_options = [{'label': ageClass, 'value': ageClass} for ageClass in df['AgeClass'].unique() if ageClass is not None]
    else:
        # Filter options based on the selected federation
        subset_df = df[df['Federation'].isin(selected_federation)]
        weightclass_options = [{'label': weightClass, 'value': weightClass} for weightClass in subset_df['WeightClassKg'].unique()]
        ageclass_options = [{'label': ageClass, 'value': ageClass} for ageClass in subset_df['AgeClass'].unique() if ageClass is not None]

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

        if selected_weightclasses is not None and selected_ageclasses is not None and selected_sex is not None and selected_federation is not None:
            # Filter the data based on selections
            filtered_df = df[df['WeightClassKg'].isin(selected_weightclasses) & df['AgeClass'].isin(selected_ageclasses) & (df['Sex'] == selected_sex) & df['Federation'].isin(selected_federation)]

            # Print the length of the filtered DataFrame
            print("Filtered DataFrame Length:", len(filtered_df))

            # Populate the filtered data in the DataTable
            return dash_table.DataTable(filtered_df.to_dict('records'), [{"name": i, "id": i} for i in filtered_df.columns], page_size=10,
                                        style_data={'backgroundColor': 'rgba(0,0,0,0)', 'color': 'white'},
                                        style_header={'backgroundColor': 'rgba(0,0,0,0)', 'color': 'white'})

    # Initially, return an empty div
    return html.Div()

@app.callback(
    Output('lbs-button', 'style'),
    Input('lbs-button', 'n_clicks')
)

def update_kg_lb_button(n_clicks):
    if n_clicks and n_clicks % 2 == 0:
        lbs_button_style = {
            'borderRadius': '12px',
            'background-color': 'rgba(0, 255, 0, 0.5)',
            'color': 'white',
            'height': '30px',  # set the height of the buttons
            'width': '90px',  # set the width of the buttons
        }
        print('on')
    else:
        lbs_button_style = {
            'borderRadius': '12px',
            'background-color': 'rgba(211, 211, 211, 0.5)',
            'color': 'white',
            'height': '30px',  # set the height of the buttons
            'width': '90px',  # set the width of the buttons
        }
        print('off')

    return lbs_button_style

@app.callback(
    Output('tested-button', 'style'),
    Input('tested-button', 'n_clicks')
)
def update_tested_button(n_clicks):
    if n_clicks and n_clicks % 2 == 0:
        tested_button_style = {
            'borderRadius': '12px',
            'background-color': 'rgba(255, 0, 0, 0.5)',
            'color': 'white',
            'height': '30px',  # set the height of the buttons
            'width': '90px',  # set the width of the buttons
        }
        print('on')
    else:
        tested_button_style = {
            'borderRadius': '12px',
            'background-color': 'rgba(211, 211, 211, 0.5)',
            'color': 'white',
            'height': '30px',  # set the height of the buttons
            'width': '90px',  # set the width of the buttons
        }
        print('off')

    return tested_button_style

#Define callback to add user data to the list
@app.callback(
    Output('squat_vals', 'children'),
    Output('bench_vals', 'children'),
    Output('deadlift_vals', 'children'),
    Output('output-container', 'children'),
    Output('output-container-2', 'children'),
    Input('tested-button', 'n_clicks'),
    Input('federation-filter', 'value'),
    Input('sex-filter', 'value'),
    Input('add-data-button', 'n_clicks'),
    Input('lbs-button', 'n_clicks'),
    State('name-input', 'value'),
    State('age-input', 'value'),
    State('weight-input', 'value'),
    State('squat-input', 'value'),
    State('bench-input', 'value'),
    State('deadlift-input', 'value'),
)
def update_output(tested, federation, sex, n_clicks, lbs_n_clicks, name, age, weight, squat, bench, deadlift):
    if n_clicks:
        if name and age and weight and federation:
            if lbs_n_clicks and lbs_n_clicks % 2 == 0:
                user_data.update(
                    {'Name': name, 'Age': age, 'BodyweightKg': weight / float(2.2), 'Best3SquatKg': squat,
                     'Best3BenchKg': bench,
                     'Best3DeadliftKg': deadlift})
            else:
                user_data.update(
                    {'Name': name, 'Age': age, 'BodyweightKg': weight, 'Best3SquatKg': squat, 'Best3BenchKg': bench,
                     'Best3DeadliftKg': deadlift})

            if tested % 2 == 0:
                print('has both tested and non-tested lifters')

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

                print(closest_age_class)

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

                estimated_comp_class.update({'ageclass': closest_age_class, 'weightclass': closest_lower_weight_class})

            df_grouped = filtered_df.groupby('Name').agg(squat=('Best3SquatKg', 'max'),
                                                         bench=('Best3BenchKg', 'max'),
                                                         deadlift=('Best3DeadliftKg', 'max'),
                                                         wilks=('Wilks', 'max')
                                                         ).reset_index()

            squat_perc, bench_perc, deadlift_perc = None, None, None
            if squat:
                if lbs_n_clicks and lbs_n_clicks % 2 == 0:
                    df_grouped['squat'] = df_grouped['squat'].fillna(0)
                    squat_perc = percentileofscore(df_grouped['squat'], user_data['Best3SquatKg'] / float(2.2))
                    squat_perc_val = squat_perc
                    user_data_perc.update({'squat_perc': squat_perc_val})
                else:
                    df_grouped['squat'] = df_grouped['squat'].fillna(0)
                    squat_perc = percentileofscore(df_grouped['squat'], user_data['Best3SquatKg'])
                    squat_perc_val = squat_perc
                    user_data_perc.update({'squat_perc': squat_perc_val})

            if bench:
                if lbs_n_clicks and lbs_n_clicks % 2 == 0:
                    df_grouped['bench'] = df_grouped['bench'].fillna(0)
                    bench_perc = percentileofscore(df_grouped['bench'], user_data['Best3BenchKg'] / float(2.2))
                    bench_perc_val = bench_perc
                    user_data_perc.update({'bench_perc': bench_perc_val})
                else:
                    df_grouped['bench'] = df_grouped['bench'].fillna(0)
                    bench_perc = percentileofscore(df_grouped['bench'], user_data['Best3BenchKg'])
                    bench_perc_val = bench_perc
                    user_data_perc.update({'bench_perc': bench_perc_val})

            if deadlift:
                if lbs_n_clicks and lbs_n_clicks % 2 == 0:
                    df_grouped['deadlift'] = df_grouped['deadlift'].fillna(0)
                    deadlift_perc = percentileofscore(df_grouped['deadlift'], user_data['Best3DeadliftKg'] / float(2.2))
                    deadlift_perc_val = deadlift_perc
                    user_data_perc.update({'deadlift_perc': deadlift_perc_val})
                else:
                    df_grouped['deadlift'] = df_grouped['deadlift'].fillna(0)
                    deadlift_perc = percentileofscore(df_grouped['deadlift'], user_data['Best3DeadliftKg'])
                    deadlift_perc_val = deadlift_perc
                    user_data_perc.update({'deadlift_perc': deadlift_perc_val})

            if len(federation) == 1:
                federation = federation[0]
            else:
                federation = ', '.join(str(x) for x in federation)

            # Logic for updating 'output-container' and 'output-container-2'
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

            return squat_perc, bench_perc, deadlift_perc, output1, output2

        else:
            return "Please enter both name and age", name, age, '', ''
    return '', '', '', '', ''

# Callback to update the gauge chart
@app.callback(
    [Output('squat_indicator_chart', 'figure'),
     Output('squat_indicator_chart', 'style')],
    [Input('add-data-button', 'n_clicks')],
    [Input('squat_vals', 'children')]  # Assuming 'squat-input' is the input for the squat value
)
def update_squat_chart(n_clicks, squat_vals):
    if n_clicks is None:
        # If the button is not clicked yet, keep the chart hidden
        return go.Figure(), {'display': 'none'}

    squat_percentile = user_data_perc.get('squat_perc', 0)
    print(squat_percentile)

    if squat_percentile:
        # Update the gauge chart with the calculated value
        squat_figure = go.Figure(go.Indicator(
            mode="gauge+number",
            value=squat_percentile,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Squat", 'font': {'color': 'white'}},
            gauge=dict(
                axis=dict(range=[0, 100], tickfont={'color': 'white'}),  # Assuming percentiles from 0 to 100
                bar=dict(color="red"),
                bgcolor="rgba(0, 0, 0, 0)"  # Fully transparent background
            ),
            number={'font': {'color': 'white'}, 'suffix':"%"}
        ))

        squat_figure.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',  # Fully transparent background
            paper_bgcolor='rgba(0, 0, 0, 0)'  # Fully transparent plot area background
        )

        # Show the chart by updating the style property
        squat_style = {'display': 'block'}

        return squat_figure, squat_style

    else:
        # If squat_percentile is None or 0, you may want to handle this case
        return go.Figure(), {'display': 'none'}



@app.callback(
    [Output('bench_indicator_chart', 'figure'),
     Output('bench_indicator_chart', 'style')],
    [Input('add-data-button', 'n_clicks')],
    [Input('bench_vals', 'children')]  # Assuming 'squat-input' is the input for the squat value
)
def update_bench_chart(n_clicks, squat_vals):
    if n_clicks is None:
        # If the button is not clicked yet, keep the chart hidden
        return go.Figure(), {'display': 'none'}


    bench_percentile = user_data_perc.get('bench_perc', 0)
    print(bench_percentile)

    if bench_percentile:
        # Update the gauge chart with the calculated value
        bench_figure = go.Figure(go.Indicator(
            mode="gauge+number",
            value=bench_percentile,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Bench", 'font': {'color': 'white'}},
            gauge=dict(
                axis=dict(range=[0, 100], tickfont={'color': 'white'}),  # Assuming percentiles from 0 to 100
                bar=dict(color="red"),
                bgcolor="rgba(0, 0, 0, 0)"  # Fully transparent background
            ),
            number={'font': {'color': 'white'}, 'suffix':"%"}
        ))

        bench_figure.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',  # Fully transparent background
            paper_bgcolor='rgba(0, 0, 0, 0)'  # Fully transparent plot area background
        )

        # Show the chart by updating the style property
        bench_style = {'display': 'block'}

        return bench_figure, bench_style

    else:
        # If squat_percentile is None or 0, you may want to handle this case
        return go.Figure(), {'display': 'none'}


@app.callback(
    [Output('deadlift_indicator_chart', 'figure'),
     Output('deadlift_indicator_chart', 'style')],
    [Input('add-data-button', 'n_clicks')],
    [Input('deadlift_vals', 'children')]  # Assuming 'squat-input' is the input for the squat value
)
def update_deadlift_chart(n_clicks, squat_vals):
    if n_clicks is None:
        # If the button is not clicked yet, keep the chart hidden
        return go.Figure(), {'display': 'none'}


    deadlift_percentile = user_data_perc.get('deadlift_perc', 0)
    print(deadlift_percentile)

    if deadlift_percentile:
        # Update the gauge chart with the calculated value
        deadlift_figure = go.Figure(go.Indicator(
            mode="gauge+number",
            value=deadlift_percentile,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Deadlift", 'font': {'color': 'white'}},
            gauge=dict(
                axis=dict(range=[0, 100], tickfont={'color': 'white'}),  # Assuming percentiles from 0 to 100
                bar=dict(color="red"),
                bgcolor="rgba(0, 0, 0, 0)"  # Fully transparent background
            ),
            number={'font': {'color': 'white'}, 'suffix':"%"}
        ))

        deadlift_figure.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',  # Fully transparent background
            paper_bgcolor='rgba(0, 0, 0, 0)'  # Fully transparent plot area background
        )

        # Show the chart by updating the style property
        deadlift_style = {'display': 'block'}

        return deadlift_figure, deadlift_style

    else:
        # If squat_percentile is None or 0, you may want to handle this case
        return go.Figure(), {'display': 'none'}


if __name__ == '__main__':
    app.run_server(debug=True)