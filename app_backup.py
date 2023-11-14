import pandas as pd
import dash
from dash import dcc
from dash import html
from dash import dash_table
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

def render_comp_data():
    return html.Div([
        html.H3(f'Most recent competition data as of {datetime.now().date()} ', style={'color': text_color}),
        html.P('This tab provides exploration of the most up-to-date Powerlifting data available from openpowerlifting.org',
               style={'color': text_color}),
        dcc.Markdown('**Data needs to be filtered:** Filter the data by selecting filter criteria below.'),
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

        # dcc.Dropdown(
        #     id='country-filter',
        #     options=[{'label': Country, 'value': Country} for Country in df['Country'].unique()],
        #     multi=True,
        #     placeholder='Select Country...',
        #     style={'width': '49%', 'margin': '0 10px 10px 0', 'background-color': 'transparent', 'color': 'black'}
        # ), #need to fix the countries where null values exist (maybe filter only to usa?)
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
                            squat_gauge()

                        ], width=4),
                        dbc.Col([
                            kpi_two()
                        ], width=4),
                        dbc.Col([
                            kpi_three()
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
    Output('data-table-container', 'children'),
    Input('load-data-button', 'n_clicks'),
    State('weightclass-filter', 'value'),
    State('ageclass-filter', 'value'),
    State('sex-filter', 'value')
)
def load_and_filter_data(n_clicks, selected_weightclasses, selected_ageclasses, selected_sex):
    if n_clicks:

        # Filter the data based on selections
        filtered_df = df[df['WeightClassKg'].isin(selected_weightclasses) & df['AgeClass'].isin(selected_ageclasses) & (df['Sex'] == selected_sex)]
        # Populate the filtered data in the DataTable
        return dash_table.DataTable(filtered_df.to_dict('records'), [{"name": i, "id": i} for i in filtered_df.columns], page_size= 10,
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

#Define callback to add user data to the list
@app.callback(
    Output('squat_vals', 'children'),
    Output('bench_vals', 'children'),
    Output('deadlift_vals', 'children'),
    Input('federation-filter', 'value'),
    Input('sex-filter', 'value'),
    Input('add-data-button', 'n_clicks'),
    State('name-input', 'value'),
    State('age-input', 'value'),
    State('weight-input', 'value'),
    State('squat-input', 'value'),
    State('bench-input', 'value'),
    State('deadlift-input', 'value'),
)
def add_user_data(federation, sex, n_clicks, name, age, weight, squat, bench, deadlift):
    if n_clicks:
        if name and age and weight:
            user_data.update(
                {'Name': name, 'Age': age, 'BodyweightKg': weight, 'Best3SquatKg': squat, 'Best3BenchKg': bench,
                 'Best3DeadliftKg': deadlift})

            df_weight_match = df[df['Federation'].isin(federation) & (df['Sex'] == sex)]
            closest_lower_weight_class = df_weight_match.loc[
                (df_weight_match['BodyweightKg'] - user_data['BodyweightKg']).abs().idxmin(),
                'WeightClassKg'
            ]

            filtered_df = df[df['Federation'].isin(federation) & (df['Sex'] == sex) & (
                        df['WeightClassKg'] == closest_lower_weight_class)]
            df_grouped = filtered_df.groupby('Name').agg(squat=('Best3SquatKg', 'max'),
                                                         bench=('Best3BenchKg', 'max'),
                                                         deadlift=('Best3DeadliftKg', 'max'),
                                                         wilks=('Wilks', 'max')
                                                         ).reset_index()

            if squat:
                df_grouped['squat'] = df_grouped['squat'].fillna(0)
                squat_perc = percentileofscore(df_grouped['squat'], user_data['Best3SquatKg'])


            if bench:
                df_grouped['bench'] = df_grouped['bench'].fillna(0)
                bench_perc = percentileofscore(df_grouped['bench'], user_data['Best3BenchKg'])

            if deadlift:
                df_grouped['deadlift'] = df_grouped['deadlift'].fillna(0)
                deadlift_perc = percentileofscore(df_grouped['deadlift'], user_data['Best3DeadliftKg'])


            return squat_perc, bench_perc, deadlift_perc



            #print(user_data)
            #return f"User Data: {user_data}", '', ''

        else:
            return "Please enter both name and age", name, age
    return '', '', ''



if __name__ == '__main__':
    app.run_server(debug=True)