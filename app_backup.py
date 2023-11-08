import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
from data_retrieval import retrieve_and_process_csv
from data_cleaning import remove_special_chars, convert_kg_to_lbs, apply_business_rules


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
            placeholder='Select weight class...',
            style={'width': '49%', 'margin': '0 10px 10px 0', 'background-color': 'transparent'}
        ),
        dcc.Dropdown(
            id='ageclass-filter',
            options=[{'label': ageClass, 'value': ageClass} for ageClass in df['AgeClass'].unique() if
                     ageClass is not None],
            multi=True,
            placeholder='Select age class...',
            style={'width': '49%', 'margin': '0 10px 10px 0', 'background-color': 'transparent'}
        ),
        dcc.RadioItems(
            id='sex-filter',
            options=[{'label': 'Male', 'value': 'M'}, {'label': 'Female', 'value': 'F'},
                     {'label': 'Mx', 'value': 'Mx'}],
            labelStyle={'display': 'inline', 'margin-right': '10px'},
            style={'background-color': 'transparent', 'margin-bottom': '10px'}
        ),
        html.Button('Load Data', id='load-data-button'),
        dcc.Loading(id="loading", type="default", children=[html.Div(id='data-table-container')]),
    ])


def render_user_stats():
    return html.Div([
        html.H3('Model Overview', style={'color': text_color}),
        html.P('This tab provides an explanation of the predictive model and its methodology.',
               style={'color': text_color})

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
        return dash_table.DataTable(filtered_df.to_dict('records'), [{"name": i, "id": i} for i in filtered_df.columns])

    # Initially, return an empty div
    return html.Div()


if __name__ == '__main__':
    app.run_server(debug=True)