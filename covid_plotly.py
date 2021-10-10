from concurrent.futures import ThreadPoolExecutor
import dash
from dash_bootstrap_components._components.Col import Col
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from data_functions import *
import numpy as np
import time
import wget
import os, shutil
from datetime import datetime
import csv

download_time = datetime.now()
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])

app.title = 'COVID-19 Global Dashboard'

server=app.server

def remove_temp_files(file_path):
        """
        Description:
            Used to clean files and folders from directory

        :param folder_path: path to directory to be cleaned
        """
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def define_variables(df_confirmed, df_vaccinated, df_deaths):
    global df_vac
    global df_con
    global df_dea
    global df_act
    global confirmed
    global vaccinated
    global deaths
    global total_confirmed
    global total_vaccinated
    global total_deaths
    global change_confirmed
    global change_vaccinated
    global change_deaths
    global recovery_rate
    global mortality_rate
    global cases_per_million
    df_confirmed.drop(['Province/State', 'Lat', 'Long'], axis=1, inplace=True)
    df_confirmed.rename(columns={'Country/Region': 'Country'}, inplace=True)
    df_vaccinated.drop(['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Province_State',
                        'Lat', 'Long_', 'Combined_Key', 'Population'], axis=1, inplace=True)
    df_vaccinated.rename(columns={'Country_Region': 'Country'}, inplace=True)
    df_deaths.drop(['Province/State', 'Lat', 'Long'], axis=1, inplace=True)
    df_deaths.rename(columns={'Country/Region': 'Country'}, inplace=True)
    df_vac = merge_countries(df_vaccinated).sort_values(by='Country')  # .drop(['12/13/20'], axis=1)
    df_con = merge_countries(df_confirmed).sort_values(by='Country')  # .drop(['12/13/20'], axis=1)
    df_dea = merge_countries(df_deaths).sort_values(by='Country')  # .drop(['12/13/20'], axis=1)
    df_con.columns = [df_con.columns[0]] + [fix_date(x) for x in df_con.columns[1:]]
    df_dea.columns = [df_dea.columns[0]] + [fix_date(x) for x in df_dea.columns[1:]]

    confirmed = date_wise(df_con.sum(axis=0))
    vaccinated = date_wise(df_vac.sum(axis=0), flag=1)
    deaths = date_wise(df_dea.sum(axis=0))
    total_confirmed = confirmed.Value.iloc[-1]
    total_vaccinated = vaccinated.Value.iloc[-1]
    total_deaths = deaths.Value.iloc[-1]
    change_confirmed = confirmed.Value.iloc[-1] - confirmed.Value.iloc[-2]
    change_vaccinated = vaccinated.Value.iloc[-1] - vaccinated.Value.iloc[-2]
    change_deaths = deaths.Value.iloc[-1] - deaths.Value.iloc[-2]

    if change_confirmed >= 0:
        change_confirmed = f'+{change_confirmed:,}'
    else:
        change_confirmed = f'-{-change_confirmed:,}'
    if change_vaccinated >= 0:
        change_vaccinated = f'+{int(change_vaccinated):,}'
    else:
        change_vaccinated = f'-{-int(change_vaccinated):,}'
    if change_deaths >= 0:
        change_deaths = f'+{change_deaths:,}'
    else:
        change_deaths = f'-{-change_deaths:,}'
    recovery_rate = 100 * total_vaccinated / (total_confirmed)
    mortality_rate = 100 * total_deaths / (total_confirmed)
    cases_per_million = 1e6 * total_confirmed / 7796127694

# getting data periodically
def update_data(period=24):
    while True:
        print('Update triggered')
        remove_temp_files('data/time_series_covid19_confirmed_global.csv')

        wget.download('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv','./data')
        global df_confirmed
        df_confirmed = pd.read_csv('data/time_series_covid19_confirmed_global.csv')

        remove_temp_files('data/time_series_covid19_vaccine_doses_admin_global.csv')

        wget.download('https://raw.githubusercontent.com/govex/COVID-19/master/data_tables/vaccine_data/global_data/time_series_covid19_vaccine_doses_admin_global.csv','./data')
        global df_vaccinated
        df_vaccinated = pd.read_csv('data/time_series_covid19_vaccine_doses_admin_global.csv')

        remove_temp_files('data/time_series_covid19_deaths_global.csv')

        wget.download('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv','./data')
        global df_deaths
        df_deaths = pd.read_csv('data/time_series_covid19_deaths_global.csv')

        send_to_twilio()
        
        
        time.sleep(period*3600)
        
        define_variables(df_confirmed, df_vaccinated, df_deaths)


if 'time_series_covid19_confirmed_global.csv' not in os.listdir('./data'):
    wget.download('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv', './data')
if 'time_series_covid19_vaccine_doses_admin_global.csv' not in os.listdir('./data'):
    wget.download('https://raw.githubusercontent.com/govex/COVID-19/master/data_tables/vaccine_data/global_data/time_series_covid19_vaccine_doses_admin_global.csv', './data')
if 'time_series_covid19_deaths_global.csv' not in os.listdir('./data'):
    wget.download('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv', './data')

# importing data
df_confirmed = pd.read_csv('data/time_series_covid19_confirmed_global.csv')
df_vaccinated = pd.read_csv('data/time_series_covid19_vaccine_doses_admin_global.csv')
df_deaths = pd.read_csv('data/time_series_covid19_deaths_global.csv')
define_variables(df_confirmed, df_vaccinated, df_deaths)


# cards
card_1 = dbc.Card([
        dbc.CardBody([
                html.H6("Confirmed", className='card_title'),
                html.H5(f"{change_confirmed}", className='card_changed'),
                html.H5(f"{total_confirmed:,}", className='card_value')
                ], className='card_1_body')], className='card_1')

card_2 = dbc.Card([
        dbc.CardBody([
                html.H6("Vaccinated", className='card_title'),
                html.H5(f"{change_vaccinated}", className='card_changed'),
                html.H5(f"{change_vaccinated}", className='card_value')
                ], className='card_2_body')], className='card_2')

card_3 = dbc.Card([
        dbc.CardBody([
                html.H6("Deceased", className='card_title'),
                html.H5(f"{change_deaths}", className='card_changed'),
                html.H5(f"{total_deaths:,}", className='card_value')
                ], className='card_3_body')], className='card_3')

##########################################

files = {'covid': 'data/covid_19_data.csv',
         'covid_line_list': 'data/COVID19_line_list_data.csv',
         'COVID19_open_line_list': 'data/COVID19_open_line_list.csv',
         'global_confirmed': 'data/time_series_covid_19_confirmed.csv',
         'global_deaths': 'data/time_series_covid_19_deaths.csv',
         'global_vaccinated': 'data/time_series_covid19_vaccine_doses_admin_global.csv'}

n = -1
df_top = for_map(df_con, df_vac, df_dea, flag='top')
countries = df_top['Country'].values
countries = np.append(countries, 'Global')
df_top = df_top.sort_values(by='Confirmed', ascending=False).iloc[:n]

################ world-map #################
df_map = for_map(df_con, df_vac, df_dea)
fig_map = create_map(df_map)
fig_map = html.Div(dcc.Graph(figure=fig_map, className='fig_map'), style={'padding':'1.25rem'})

################ sunburst plot #############
df_continent = pd.read_csv('https://raw.githubusercontent.com/dbouquin/IS_608/master/NanosatDB_munging/Countries-Continents.csv')
df_continent.replace('Burkina', 'Burkina Faso', inplace=True)
df_continent.replace('Burma (Myanmar)', 'Burma', inplace=True)
df_continent.replace('Congo', 'Congo (Brazzaville)', inplace=True)
df_continent.replace('Congo, Democratic Republic of', 'Congo (Kinshasa)', inplace=True)
df_continent.replace('Russian Federation', 'Russia', inplace=True)

new = pd.DataFrame([['Africa', 'Congo (Brazzaville)'],
                    ['Africa', 'Congo (Kinshasa)'],
                    ['Europe', 'Czechia'],
                    ['Asia', 'Taiwan*'],
                    ['Africa', 'Western Sahara']], columns=df_continent.columns)
df_continent = df_continent.append(new)
df_sunburst = for_map(df_con, df_vac, df_dea, flag='top')
df_sunburst = pd.merge(df_continent, df_sunburst, on='Country')
df_sunburst.replace(0, np.nan, inplace=True)
df_sunburst.dropna(inplace=True)
fig_sunburst_confirmed = create_sunburst(df_sunburst, 'Confirmed')
fig_sunburst_vaccinated = create_sunburst(df_sunburst, 'Vaccinated')
fig_sunburst_deaths = create_sunburst(df_sunburst, 'Deaths')

fig_sunburst_confirmed = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(figure=fig_sunburst_confirmed))),
                                             className='figure_confirmed'), className='figure_rows'))

fig_sunburst_vaccinated = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(figure=fig_sunburst_vaccinated))),
                                             className='figure_recovered'), className='figure_rows'))

fig_sunburst_deaths = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(figure=fig_sunburst_deaths))),
                                            className='figure_deceased'), className='figure_rows'))

############################################
# table card
table_card = dbc.Card([
                dbc.Table.from_dataframe(df_top.iloc[:-12], dark=True, bordered=True,
                                 hover=True, responsive=True, size='sm',
                                 className='container', style={'margin': 'auto'})], className='table_card')

############################################
#card container row
card_container_row = dbc.Row(dbc.Col(dbc.Row([
                        dbc.Col(html.Div(card_1), className='cards'),
                        dbc.Col(html.Div(card_2), className='cards'),
                        dbc.Col(html.Div(card_3), className='cards'),
                        # dbc.Col(html.Div(card_4), className='cards'),
                        ], className='cards_inside_row'), className='cards_col'),
    className='cards_row')

############################################
# tab items
dropdown_country = dbc.Card(dbc.CardBody(dbc.Row([
                                        dbc.Col(dbc.Input(placeholder="Search country...", type="text",
                                                      list='list-data', id='_cntry_name', value='India')),
                                        html.Datalist(id='list-data',
                                                      children=[html.Option(value=c) for c in countries])
                                        ]), className='tab_global'), className='tab_global')

dropdown_global = dbc.Card(dbc.CardBody(dbc.Row(dbc.Col(
                            dbc.InputGroup([
                                dbc.InputGroupAddon("Show top", addon_type="prepend", className='addon_text'),

                                dbc.Input(placeholder="10", type="number", min=1, max=180,
                                          step=1, id='_no_of_cntry', value=10),

                                dbc.InputGroupAddon("countries with", addon_type="prepend", className='addon_text'),

                                dbc.Select(id="_hgh_or_lw",
                                    options=[{"label": "lowest", "value": 'lowest'},
                                             {"label": "highest", "value": 'highest'}], value='highest'),

                                dbc.Select(id="_feature",
                                     options=[{"label": "confirmed", "value": 'Confirmed'},
                                              {"label": "vaccinated", "value": 'Vaccinated'},
                                              {"label": "deceased", "value": 'Deaths'}], value='Confirmed'),

                                dbc.InputGroupAddon("cases!", addon_type="prepend", className='addon_text'),
                                 ], className='input_group'))), className='tab_global_card'), className='tab_global_card')

#############################################
# tabs
tabs = dbc.Row(dbc.Col([
    dbc.Card(dbc.Tabs(
        [
        dbc.Tab(dropdown_global, label="Global data", className='tab_global', tab_id="tab-1"),
        dbc.Tab(dropdown_country, label="Country wise data", className='tab_country', tab_id="tab-2"),
        ], id="_tabs", active_tab="tab-1"), className='tabs_card'),
    dbc.Button("Get results", color='#AAA', size="sm", className="button", block=True, id='button'),
                        ], className='tabs_column'),
    className='figure_rows')

#############################################
# global data

fig_bar = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_bar'))),
                                  className='figure_global'), className='figure_rows'))

# cdf
fig_confirmed_cdf = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_confirmed_cdf'))),
                                            className='figure_confirmed'), className='figure_rows'))

fig_recovered_cdf = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_recovered_cdf'))),
                                            className='figure_recovered'), className='figure_rows'))

fig_deceased_cdf = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_deceased_cdf'))),
                                           className='figure_deceased'), className='figure_rows'))

# daily
fig_confirmed_daily = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_confirmed_daily'))),
                                              className='figure_confirmed'), className='figure_rows'))

fig_recovered_daily = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_recovered_daily'))),
                                              className='figure_recovered'), className='figure_rows'))

fig_deceased_daily = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_deceased_daily'))),
                                             className='figure_deceased'), className='figure_rows'))

# rate
fig_confirmed_rate = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_confirmed_rate'))),
                                             className='figure_confirmed'), className='figure_rows'))

fig_recovered_rate = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_recovered_rate'))),
                                             className='figure_recovered'), className='figure_rows'))

fig_deceased_rate = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(html.Div(dcc.Graph(id='fig_deceased_rate'))),
                                            className='figure_deceased'), className='figure_rows'))


###### default output ######
[f1,f2,f3,f4,f5,f6,f7,f8,f9,f10] = [
         create_global_bar(df_top),
         confirm_cdf(df_con, c=0), confirm_cdf(df_vac, c=1),
             confirm_cdf(df_dea, c=2),

         confirm_daily(df_con, c=0), confirm_daily(df_vac, c=1),
             confirm_daily(df_dea, c=2),

         confirm_rate(df_con, c=0), confirm_rate(df_vac, c=1),
             confirm_rate(df_dea, c=2)]

# https://community.plotly.com/t/is-there-a-way-to-only-update-on-a-button-press-for-apps-where-updates-are-slow/4679/7

@app.callback([
    Output("fig_bar", "figure"),
    Output("fig_confirmed_cdf", "figure"), Output("fig_recovered_cdf", "figure"),
        Output("fig_deceased_cdf", "figure"),
    Output("fig_confirmed_daily", "figure"), Output("fig_recovered_daily", "figure"),
        Output("fig_deceased_daily", "figure"),
    Output("fig_confirmed_rate", "figure"), Output("fig_recovered_rate", "figure"),
        Output("fig_deceased_rate", "figure")],
    [Input('button', 'n_clicks')],
    state = [State("_no_of_cntry", "value"), State("_hgh_or_lw", "value"), State("_feature", "value"),
     State("_cntry_name", "value"), State("_tabs", "active_tab")])

def output_text(n_clicks, _no_of_cntry, _hgh_or_lw, _feature, _cntry_name, _tabs):

    if _tabs == 'tab-1':
        _cntry_name = '#'

    output = [f1, f2, f3, f4, f5,
              f6, f7, f8, f9, f10]

    if n_clicks:
        output = [create_global_bar(df_top, _no_of_cntry, _feature, _hgh_or_lw, _cntry_name),
                  confirm_cdf(df_con, c=0, cntry_name=_cntry_name),
                  confirm_cdf(df_vac, c=1, cntry_name=_cntry_name),
                  confirm_cdf(df_dea, c=2, cntry_name=_cntry_name),

                  confirm_daily(df_con, c=0, cntry_name=_cntry_name),
                  confirm_daily(df_vac, c=1, cntry_name=_cntry_name),
                  confirm_daily(df_dea, c=2, cntry_name=_cntry_name),

                  confirm_rate(df_con, c=0, cntry_name=_cntry_name),
                  confirm_rate(df_vac, c=1, cntry_name=_cntry_name),
                  confirm_rate(df_dea, c=2, cntry_name=_cntry_name)]

        return output

    elif n_clicks==None:
        return output


##########################
# app
github = html.A(dbc.CardImg(src="assets/images/github.svg", top=True, className='image_link'), href='https://github.com/Extroverted-introvert', target="_blank", className='image_1')
linkedin = html.A(dbc.CardImg(src="assets/images/linkedin.svg", top=True, className='image_link'), href='https://www.linkedin.com/in/parthtripathi17/', target="_blank")
website = html.A(dbc.CardImg(src="assets/images/website.svg", top=True, className='image_link'), href='https://parthtripathi.netlify.app', target="_blank")
info = html.P("Made by Parth Tripathi with ♥")

profile_links_top = dbc.Row([dbc.Col(width=2, className='link_col'),
                            dbc.Col(website, width=2, className='link_col'),
                            dbc.Col(github, width=2, className='link_col'),
                            dbc.Col(linkedin, width=2, className='link_col'),
                            ], className='link_icons')

profile_links = dbc.Row([dbc.Col(info, width =4, className='link_col'),
                        dbc.Col(website, width =2, className='link_col'),
                        dbc.Col(github, width=2, className='link_col'),
                        dbc.Col(linkedin, width=2, className='link_col'),
                         ], className='link_icons')


heading = html.Div(dbc.Row([dbc.Col(html.H3("Covid-19 Global Dashboard (served via Plotly)", className='page_title'), width=6, className='header_col1'),
                            dbc.Col(profile_links_top, width=6, className='header_col2')],
                            className='header_container'))

text_1 = dcc.Markdown('''Johns Hopkins University has made an excellent [dashboard](https://gisanddata.maps.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6) using the affected cases data. Data is extracted from the google sheets associated and made available [here](https://github.com/CSSEGISandData/COVID-19).''')
text_2 = dcc.Markdown('''From [World Health Organization](https://www.who.int/emergencies/diseases/novel-coronavirus-2019) - On 31 December 2019, WHO was alerted to several cases of pneumonia in Wuhan City, Hubei Province of China. The virus did not match any other known virus. This raised concern because when a virus is new, we do not know how it affects people.
So daily level information on the affected people can give some interesting insights when it is made available to the broader data science community.
The purpose of this dashboard is to spread awareness and provide some useful insights on COVID-19 by the means of data.''')
text_3 = dcc.Markdown('''Just a novice Data Scinetist who loves to tinker with impactful tools a create fun applications''')

summary = dbc.Row(dbc.Col(dbc.Card(dbc.CardBody([
                                    html.Div('About the COVID-19 Global Dashboard:', className='ques'),
                                    html.Div(text_2, className='ans'),
                                    html.Div('Source of the COVID-19 data:', className='ques'),
                                    html.Div(text_1, className='ans'),
                                    html.Div('About me:', className='ques'),
                                    html.Div(text_3, className='ans')
                                    ]), className='figure_summary'), className='figure_rows'))

# time_diff = datetime.now() - download_time
# print()
# print(time_diff)
# last_update = f'The data was last updated {divmod(time_diff.total_seconds(), 3600)[0]} hours ago.'
last_update = f"The data was last updated at {datetime.now().strftime('%Y-%m-%d')}"
data_update = dbc.Row(dbc.Col(html.H6(last_update), className='last_update_1'),
                      className='last_update')

footer = html.Div(dbc.Row([dbc.Col([profile_links])], className='header_container'))


username_input = dbc.FormGroup(
    [
        dbc.Label("Username", html_for="username"),
        dbc.Input(type="text", id="username", placeholder="Enter username"),
        dbc.FormText(
            "Enter Username that service refers to",
            color="secondary",
        ),
    ]
)

email_input = dbc.FormGroup(
    [
        dbc.Label("Email", html_for="example-email"),
        dbc.Input(type="email", id="example-email", placeholder="Enter email"),
        dbc.FormText(
            "Enter your Email Address",
            color="secondary",
        ),
    ]
)

country_code_input = dbc.FormGroup(
    [
        dbc.Label("Country Code", html_for="country-code"),
        dbc.Select(
            id="country-code",
            options=[
                { "label" : "Algeria (+213)", "value" : 213 },
                { "label" : "Andorra (+376)", "value" : 376 },
                { "label" : "Angola (+244)", "value" : 244 },
                { "label" : "Anguilla (+1264)", "value" : 1264 },
                { "label" : "Antigua &amp; Barbuda (+1268)", "value" : 1268 },
                { "label" : "Argentina (+54)", "value" : 54 },
                { "label" : "Armenia (+374)", "value" : 374 },
                { "label" : "Aruba (+297)", "value" : 297 },
                { "label" : "Australia (+61)", "value" : 61 },
                { "label" : "Austria (+43)", "value" : 43 },
                { "label" : "Azerbaijan (+994)", "value" : 994 },
                { "label" : "Bahamas (+1242)", "value" : 1242 },
                { "label" : "Bahrain (+973)", "value" : 973 },
                { "label" : "Bangladesh (+880)", "value" : 880 },
                { "label" : "Barbados (+1246)", "value" : 1246 },
                { "label" : "Belarus (+375)", "value" : 375 },
                { "label" : "Belgium (+32)", "value" : 32 },
                { "label" : "Belize (+501)", "value" : 501 },
                { "label" : "Benin (+229)", "value" : 229 },
                { "label" : "Bermuda (+1441)", "value" : 1441 },
                { "label" : "Bhutan (+975)", "value" : 975 },
                { "label" : "Bolivia (+591)", "value" : 591 },
                { "label" : "Bosnia Herzegovina (+387)", "value" : 387 },
                { "label" : "Botswana (+267)", "value" : 267 },
                { "label" : "Brazil (+55)", "value" : 55 },
                { "label" : "Brunei (+673)", "value" : 673 },
                { "label" : "Bulgaria (+359)", "value" : 359 },
                { "label" : "Burkina Faso (+226)", "value" : 226 },
                { "label" : "Burundi (+257)", "value" : 257 },
                { "label" : "Cambodia (+855)", "value" : 855 },
                { "label" : "Cameroon (+237)", "value" : 237 },
                { "label" : "Canada (+1)", "value" : 1 },
                { "label" : "Cape Verde Islands (+238)", "value" : 238 },
                { "label" : "Cayman Islands (+1345)", "value" : 1345 },
                { "label" : "Central African Republic (+236)", "value" : 236 },
                { "label" : "Chile (+56)", "value" : 56 },
                { "label" : "China (+86)", "value" : 86 },
                { "label" : "Colombia (+57)", "value" : 57 },
                { "label" : "Comoros (+269)", "value" : 269 },
                { "label" : "Congo (+242)", "value" : 242 },
                { "label" : "Cook Islands (+682)", "value" : 682 },
                { "label" : "Costa Rica (+506)", "value" : 506 },
                { "label" : "Croatia (+385)", "value" : 385 },
                { "label" : "Cuba (+53)", "value" : 53 },
                { "label" : "Cyprus North (+90392)", "value" : 90392 },
                { "label" : "Cyprus South (+357)", "value" : 357 },
                { "label" : "Czech Republic (+42)", "value" : 42 },
                { "label" : "Denmark (+45)", "value" : 45 },
                { "label" : "Djibouti (+253)", "value" : 253 },
                { "label" : "Dominica (+1809)", "value" : 1809 },
                { "label" : "Dominican Republic (+1809)", "value" : 1809 },
                { "label" : "Ecuador (+593)", "value" : 593 },
                { "label" : "Egypt (+20)", "value" : 20 },
                { "label" : "El Salvador (+503)", "value" : 503 },
                { "label" : "Equatorial Guinea (+240)", "value" : 240 },
                { "label" : "Eritrea (+291)", "value" : 291 },
                { "label" : "Estonia (+372)", "value" : 372 },
                { "label" : "Ethiopia (+251)", "value" : 251 },
                { "label" : "Falkland Islands (+500)", "value" : 500 },
                { "label" : "Faroe Islands (+298)", "value" : 298 },
                { "label" : "Fiji (+679)", "value" : 679 },
                { "label" : "Finland (+358)", "value" : 358 },
                { "label" : "France (+33)", "value" : 33 },
                { "label" : "French Guiana (+594)", "value" : 594 },
                { "label" : "French Polynesia (+689)", "value" : 689 },
                { "label" : "Gabon (+241)", "value" : 241 },
                { "label" : "Gambia (+220)", "value" : 220 },
                { "label" : "Georgia (+7880)", "value" : 7880 },
                { "label" : "Germany (+49)", "value" : 49 },
                { "label" : "Ghana (+233)", "value" : 233 },
                { "label" : "Gibraltar (+350)", "value" : 350 },
                { "label" : "Greece (+30)", "value" : 30 },
                { "label" : "Greenland (+299)", "value" : 299 },
                { "label" : "Grenada (+1473)", "value" : 1473 },
                { "label" : "Guadeloupe (+590)", "value" : 590 },
                { "label" : "Guam (+671)", "value" : 671 },
                { "label" : "Guatemala (+502)", "value" : 502 },
                { "label" : "Guinea (+224)", "value" : 224 },
                { "label" : "Guinea - Bissau (+245)", "value" : 245 },
                { "label" : "Guyana (+592)", "value" : 592 },
                { "label" : "Haiti (+509)", "value" : 509 },
                { "label" : "Honduras (+504)", "value" : 504 },
                { "label" : "Hong Kong (+852)", "value" : 852 },
                { "label" : "Hungary (+36)", "value" : 36 },
                { "label" : "Iceland (+354)", "value" : 354 },
                { "label" : "India (+91)", "value" : 91 },
                { "label" : "Indonesia (+62)", "value" : 62 },
                { "label" : "Iran (+98)", "value" : 98 },
                { "label" : "Iraq (+964)", "value" : 964 },
                { "label" : "Ireland (+353)", "value" : 353 },
                { "label" : "Israel (+972)", "value" : 972 },
                { "label" : "Italy (+39)", "value" : 39 },
                { "label" : "Jamaica (+1876)", "value" : 1876 },
                { "label" : "Japan (+81)", "value" : 81 },
                { "label" : "Jordan (+962)", "value" : 962 },
                { "label" : "Kazakhstan (+7)", "value" : 7 },
                { "label" : "Kenya (+254)", "value" : 254 },
                { "label" : "Kiribati (+686)", "value" : 686 },
                { "label" : "Korea North (+850)", "value" : 850 },
                { "label" : "Korea South (+82)", "value" : 82 },
                { "label" : "Kuwait (+965)", "value" : 965 },
                { "label" : "Kyrgyzstan (+996)", "value" : 996 },
                { "label" : "Laos (+856)", "value" : 856 },
                { "label" : "Latvia (+371)", "value" : 371 },
                { "label" : "Lebanon (+961)", "value" : 961 },
                { "label" : "Lesotho (+266)", "value" : 266 },
                { "label" : "Liberia (+231)", "value" : 231 },
                { "label" : "Libya (+218)", "value" : 218 },
                { "label" : "Liechtenstein (+417)", "value" : 417 },
                { "label" : "Lithuania (+370)", "value" : 370 },
                { "label" : "Luxembourg (+352)", "value" : 352 },
                { "label" : "Macao (+853)", "value" : 853 },
                { "label" : "Macedonia (+389)", "value" : 389 },
                { "label" : "Madagascar (+261)", "value" : 261 },
                { "label" : "Malawi (+265)", "value" : 265 },
                { "label" : "Malaysia (+60)", "value" : 60 },
                { "label" : "Maldives (+960)", "value" : 960 },
                { "label" : "Mali (+223)", "value" : 223 },
                { "label" : "Malta (+356)", "value" : 356 },
                { "label" : "Marshall Islands (+692)", "value" : 692 },
                { "label" : "Martinique (+596)", "value" : 596 },
                { "label" : "Mauritania (+222)", "value" : 222 },
                { "label" : "Mayotte (+269)", "value" : 269 },
                { "label" : "Mexico (+52)", "value" : 52 },
                { "label" : "Micronesia (+691)", "value" : 691 },
                { "label" : "Moldova (+373)", "value" : 373 },
                { "label" : "Monaco (+377)", "value" : 377 },
                { "label" : "Mongolia (+976)", "value" : 976 },
                { "label" : "Montserrat (+1664)", "value" : 1664 },
                { "label" : "Morocco (+212)", "value" : 212 },
                { "label" : "Mozambique (+258)", "value" : 258 },
                { "label" : "Myanmar (+95)", "value" : 95 },
                { "label" : "Namibia (+264)", "value" : 264 },
                { "label" : "Nauru (+674)", "value" : 674 },
                { "label" : "Nepal (+977)", "value" : 977 },
                { "label" : "Netherlands (+31)", "value" : 31 },
                { "label" : "New Caledonia (+687)", "value" : 687 },
                { "label" : "New Zealand (+64)", "value" : 64 },
                { "label" : "Nicaragua (+505)", "value" : 505 },
                { "label" : "Niger (+227)", "value" : 227 },
                { "label" : "Nigeria (+234)", "value" : 234 },
                { "label" : "Niue (+683)", "value" : 683 },
                { "label" : "Norfolk Islands (+672)", "value" : 672 },
                { "label" : "Northern Marianas (+670)", "value" : 670 },
                { "label" : "Norway (+47)", "value" : 47 },
                { "label" : "Oman (+968)", "value" : 968 },
                { "label" : "Palau (+680)", "value" : 680 },
                { "label" : "Panama (+507)", "value" : 507 },
                { "label" : "Papua New Guinea (+675)", "value" : 675 },
                { "label" : "Paraguay (+595)", "value" : 595 },
                { "label" : "Peru (+51)", "value" : 51 },
                { "label" : "Philippines (+63)", "value" : 63 },
                { "label" : "Poland (+48)", "value" : 48 },
                { "label" : "Portugal (+351)", "value" : 351 },
                { "label" : "Puerto Rico (+1787)", "value" : 1787 },
                { "label" : "Qatar (+974)", "value" : 974 },
                { "label" : "Reunion (+262)", "value" : 262 },
                { "label" : "Romania (+40)", "value" : 40 },
                { "label" : "Russia (+7)", "value" : 7 },
                { "label" : "Rwanda (+250)", "value" : 250 },
                { "label" : "San Marino (+378)", "value" : 378 },
                { "label" : "Sao Tome &amp; Principe (+239)", "value" : 239 },
                { "label" : "Saudi Arabia (+966)", "value" : 966 },
                { "label" : "Senegal (+221)", "value" : 221 },
                { "label" : "Serbia (+381)", "value" : 381 },
                { "label" : "Seychelles (+248)", "value" : 248 },
                { "label" : "Sierra Leone (+232)", "value" : 232 },
                { "label" : "Singapore (+65)", "value" : 65 },
                { "label" : "Slovak Republic (+421)", "value" : 421 },
                { "label" : "Slovenia (+386)", "value" : 386 },
                { "label" : "Solomon Islands (+677)", "value" : 677 },
                { "label" : "Somalia (+252)", "value" : 252 },
                { "label" : "South Africa (+27)", "value" : 27 },
                { "label" : "Spain (+34)", "value" : 34 },
                { "label" : "Sri Lanka (+94)", "value" : 94 },
                { "label" : "St. Helena (+290)", "value" : 290 },
                { "label" : "St. Kitts (+1869)", "value" : 1869 },
                { "label" : "St. Lucia (+1758)", "value" : 1758 },
                { "label" : "Sudan (+249)", "value" : 249 },
                { "label" : "Suriname (+597)", "value" : 597 },
                { "label" : "Swaziland (+268)", "value" : 268 },
                { "label" : "Sweden (+46)", "value" : 46 },
                { "label" : "Switzerland (+41)", "value" : 41 },
                { "label" : "Syria (+963)", "value" : 963 },
                { "label" : "Taiwan (+886)", "value" : 886 },
                { "label" : "Tajikstan (+7)", "value" : 7 },
                { "label" : "Thailand (+66)", "value" : 66 },
                { "label" : "Togo (+228)", "value" : 228 },
                { "label" : "Tonga (+676)", "value" : 676 },
                { "label" : "Trinidad &amp; Tobago (+1868)", "value" : 1868 },
                { "label" : "Tunisia (+216)", "value" : 216 },
                { "label" : "Turkey (+90)", "value" : 90 },
                { "label" : "Turkmenistan (+7)", "value" : 7 },
                { "label" : "Turkmenistan (+993)", "value" : 993 },
                { "label" : "Turks &amp; Caicos Islands (+1649)", "value" : 1649 },
                { "label" : "Tuvalu (+688)", "value" : 688 },
                { "label" : "Uganda (+256)", "value" : 256 },
                { "label" : "UK (+44)", "value" : 44 },
                { "label" : "Ukraine (+380)", "value" : 380 },
                { "label" : "United Arab Emirates (+971)", "value" : 971 },
                { "label" : "Uruguay (+598)", "value" : 598 },
                { "label" : "USA (+1)", "value" : 1 },
                { "label" : "Uzbekistan (+7)", "value" : 7 },
                { "label" : "Vanuatu (+678)", "value" : 678 },
                { "label" : "Vatican City (+379)", "value" : 379 },
                { "label" : "Venezuela (+58)", "value" : 58 },
                { "label" : "Vietnam (+84)", "value" : 84 },
                { "label" : "Virgin Islands - British (+1284)", "value" : 84 },
                { "label" : "Virgin Islands - US (+1340)", "value" : 84 },
                { "label" : "Wallis &amp; Futuna (+681)", "value" : 681 },
                { "label" : "Yemen (North)(+969)", "value" : 969 },
                { "label" : "Yemen (South)(+967)", "value" : 967 },
                { "label" : "Zambia (+260)", "value" : 260 },
                { "label" : "Zimbabwe (+263)", "value" : 263 },
            ],
    ),
        dbc.FormText(
            "Select Country Code", color="secondary"
        ),
    ]
)

phone_input = dbc.FormGroup(
    [
        dbc.Label("Phone Number", html_for="phone-number"),
        dbc.Input(
            type="tel",
            id="phone-number",
            placeholder="Enter Phone Number",
        ),
        dbc.FormText(
            "Enter your Phone Number to get updates", color="secondary"
        ),
    ]
)

location_input = dbc.FormGroup(
    [
        dbc.Label("Location", html_for="location"),
        dbc.Input(type="text", id="location", placeholder="Enter location to target"),
        dbc.FormText(
            "Enter location you want to get Covid Status for",
            color="secondary",
        ),
    ]
)

submit_button = dbc.FormGroup(
    [
        html.Button(id='submit-button-state', n_clicks=0, children='Submit'),
        dbc.Spinner(html.Div(id="loading-output")),  
    ]
) 
form = html.Div(dbc.Form([username_input, email_input, country_code_input, phone_input, location_input, submit_button]), style={'padding':'1.25rem'})

@app.callback(
            Output('loading-output', 'children'),
            Input('submit-button-state', 'n_clicks'),
            State('username', 'value'),
            State('example-email', 'value'),
            State('country-code', 'value'),
            State('phone-number', 'value'),
            State('location', 'value'))
def update_output(n_clicks, input1, input2, input3, input4, input5):
    if n_clicks > 0:
        message = save_to_csv(input1, input2, input3, input4, input5)
        time.sleep(1)
        return message
    else:
        return None    

app.layout = html.Div(children=[
    heading,
    fig_map,
    html.Div(dbc.Row([
                dbc.Col([table_card, data_update], className='table_container', width=4),
                dbc.Col([
                    card_container_row,
                    tabs,
                    fig_bar,
                    fig_confirmed_cdf,
                    fig_recovered_cdf,
                    fig_deceased_cdf,
                    fig_confirmed_daily,
                    fig_recovered_daily,
                    fig_deceased_daily,
                    fig_confirmed_rate,
                    fig_recovered_rate,
                    fig_deceased_rate,
                    fig_sunburst_confirmed,
                    fig_sunburst_vaccinated,
                    fig_sunburst_deaths,
                    summary,
                    ], width=8),
                ]), className='table_card_row'),
        form,        
        footer
        ])

executor = ThreadPoolExecutor(max_workers=1)
executor.submit(update_data)

if __name__ == '__main__':
    app.run_server(debug=True)
