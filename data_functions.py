import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import csv
from twilio_module import send_twilio_message

color_dict = {0:'rgba(156, 58, 255, 1)', 1:'rgba(80, 247, 138, 1)',
              2:'rgba(247, 80, 80, 1)', 3:'rgba(253, 241, 73, 1)'}


case_dict = {0:'confirmed', 1:'vaccinated', 2:'deceased'}


def hue(c, h=0.2):
    h = f'{h})'
    return c[:-2]+h


def clean(country, grp):
  cnt = grp.get_group(country)
  cnt_ = cnt.sum(axis=0)
  cnt_['Country'] = country
  return pd.DataFrame([cnt_.values], columns=cnt_.keys())


def merge_countries(df, flag=0):
  grp = df.groupby('Country')
  vc = df['Country'].value_counts()
  prov = list(vc[:list(vc>1).index(False)].keys())
  for country in prov:
    cnt = clean(country, grp)
    df = df[df['Country'] != country]
    df = pd.concat([df, cnt], ignore_index=True)
  return df


def get_alpha_iso(df):
    x = pd.read_csv('./country_to_iso.csv')[['Country', 'Alpha-3 code']]
    x['Alpha-3 code'] = x['Alpha-3 code'].apply(lambda x: x[2:-1])
    dic = {'US': 'USA', 'IRAN': 'IRN', 'Congo (Brazzaville)': 'COG', 'Congo (Kinshasa)': 'COD', "Cote d'Ivoire": 'CIV',
           'Czechia': 'CZE',
           'Holy See': 'VAT', 'Iran': 'IRN', 'Korea, South': 'KOR', 'Moldova': 'MDA', 'North Macedonia': 'MKD',
           'Taiwan*': 'TWN',
           'Tanzania': 'TZA', 'Syria': 'SYR', 'Laos': 'LAO'}

    for i, j in x.values:
        dic[i] = j

    alpha = []
    for i in df['Country'].values:
        try:
            alpha.append(dic[i])
        except:
            alpha.append('NaN')

    return alpha


def fix_date(x):
  m,d,y = x.split('/')
  return f'20{y}-{"{0:0=2d}".format(int(m))}-{"{0:0=2d}".format(int(d))}'


def date_wise(df, flag=0):
  df = pd.DataFrame(df.reset_index()).iloc[1:].rename(columns={'index':'Date', 0:'Value'})
  df['Date'] = [x for x in df.Date]
  return df


def for_map(a,b,c, flag='none'):
  last = a.columns[-1]
  a = a[['Country', last]].rename(columns={last:'Confirmed'})
  b = b[['Country', last]].rename(columns={last:'Vaccinated'})
  c = c[['Country', last]].rename(columns={last:'Deaths'})
  df = pd.merge(a, b, how='inner', on='Country')
  df = pd.merge(df, c, how='inner', on='Country')

  if flag=='top':
    return df

  for col in df.columns:
    df[col] = df[col].astype(str)

  df['text'] = 'Confirmed cases in ' + df['Country'] + '<br>' + 'vaccinated: ' + \
                  df['Vaccinated'] + '<br>' + 'Deaths: ' + df['Deaths'] + '<br>'

  df.drop(columns=['Vaccinated','Deaths'], inplace=True)

  df['iso_code'] = get_alpha_iso(df)

  return df


def create_map(df_map):
    fig_map = go.Figure(data=go.Choropleth(
        locations=df_map['iso_code'],
        z=df_map['Confirmed'].astype(float),
        colorscale='teal',
        text=df_map['text'],  # hover text
        marker_line_color='gray',  # line markers between states
        colorbar_title='number of confirmed cases',
    ), layout=go.Layout(template='plotly_white'))

    fig_map.update_geos(projection_type="orthographic")
    
    fig_map.update_layout(autosize=True, height=600)

    return fig_map


def create_sunburst(df, feature):
    title = f'Sunburst plot for Global {feature.lower()} cases'
    if feature=='Confirmed':
        cc='purple'
    elif feature=='Vaccinated':
        cc='green'
    else:
        cc='red'
    fig = px.sunburst(df, path=['Continent', 'Country'], values=feature, title=title,
                      color_continuous_scale=['black', cc], color=feature, template='plotly_white')
    return fig


def create_global_bar(df_top, top=10, by='Confirmed', order='highest', cnt_name='#'):
    bool_ = True
    hovermode = 'x'
    title = 'the world'
    barmode = 'stack'
    title = f'Top {top} countries with {order} {by} cases'
    if order == 'highest':
        bool_ = False

    if cnt_name != '#':
        barmode = None
        hovermode = None
        df_top = df_top[df_top['Country'] == cnt_name]
        by = 'Confirmed'
        title = cnt_name
        if cnt_name == 'US':
            title = 'the United States'

    df_top = df_top.sort_values(by=by, ascending=bool_).iloc[:top]

    fig_global_bar = go.Figure(data=[go.Bar(x=df_top['Country'], y=df_top['Confirmed'], name='Confirmed cases', marker_color=color_dict[0]),
                      go.Bar(x=df_top['Country'], y=df_top['Vaccinated'], name='Vaccinated cases', marker_color=color_dict[1]),
                      go.Bar(x=df_top['Country'], y=df_top['Deaths'], name='Deaths', marker_color=color_dict[2])
                      ], layout=go.Layout(template='plotly_white'))

    fig_global_bar.update_layout(title_text=f"{title}", barmode=barmode, hovermode=hovermode,
                      updatemenus=[dict(buttons=list([dict(label="Linear",
                                                       method="relayout",
                                                       args=[{"yaxis.type": "linear"}]),
                                                  dict(label="Log",
                                                        method="relayout",
                                                        args=[{"yaxis.type": "log"}]),
                                                  ]),
                                    direction="right",
                                    pad={"r": 10, "t": 10},
                                    showactive=True,
                                    x=0,
                                    xanchor="left",
                                    y=-0.7,
                                    yanchor="top",
                                    bgcolor='rgba(100,100,100,0.2)',
                                    font=dict(color='#111', size=12)
                                              )], font=dict(color='black', size=12),
                  plot_bgcolor='rgba(100,100,100,0)')
    return fig_global_bar



def confirm_cdf(confirmed, c=0, cntry_name='#'):
    # CDF
    case_type = case_dict[c]
    if cntry_name == '#':
        title = f'Cumulative {case_type} cases in the world'
        confirmed = date_wise(confirmed.sum(axis=0))
    else:
        title = f'Cumulative {case_type} cases in {cntry_name}'
        confirmed = date_wise(confirmed[confirmed['Country'] == cntry_name].sum(axis=0))

    color = color_dict[c]
    fig = go.Figure(go.Scatter(x=confirmed['Date'], y=confirmed['Value'], mode='lines+markers'),
                    layout=go.Layout(template='plotly_white'))

    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(step="all")
            ]), font=dict(color='black', size=12)))

    fig.update_traces(marker_color=color, marker_line_color=hue(color),
                      line_width=4)

    fig.update_layout(title_text=title, hovermode='y',
                      updatemenus=[dict(buttons=list([dict(label="Linear",
                                                           method="relayout",
                                                           args=[{"yaxis.type": "linear"}]),
                                                      dict(label="Log",
                                                           method="relayout",
                                                           args=[{"yaxis.type": "log"}]),
                                                      ]),
                                        direction="right",
                                        pad={"r": 10, "t": 10},
                                        showactive=True,
                                        x=0,
                                        xanchor="left",
                                        y=-0.6,
                                        yanchor="top",
                                        bgcolor='rgba(100,100,100,0.2)',
                                        font=dict(color='#111', size=12)
                                        )], font=dict(color='black', size=12),
                  plot_bgcolor='rgba(100,100,100,0)')

    return fig


def confirm_daily(confirmed, c=0, cntry_name='#'):
    # Daily
    case_type = case_dict[c]
    if cntry_name == '#':
        title = f'Daily {case_type} cases in the world'
        confirmed = date_wise(confirmed.sum(axis=0))
    else:
        title = f'Daily {case_type} cases in {cntry_name}'
        confirmed = date_wise(confirmed[confirmed['Country'] == cntry_name].sum(axis=0))

    color = color_dict[c]
    daily_confirmed = confirmed.iloc[:-1].copy()
    daily_confirmed['Value'] = confirmed.iloc[1:].Value.values - confirmed.iloc[:-1].Value.values
    daily_confirmed = daily_confirmed[daily_confirmed['Value']>=0]

    fig = go.Figure(go.Bar(x=daily_confirmed['Date'], y=daily_confirmed['Value']),
                    layout=go.Layout(template='plotly_white'))

    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(step="all")
            ]), font=dict(color='black', size=12)
        )
    )

    fig.update_traces(marker_color=color, marker_line_color=hue(color),
                      marker_line_width=1.5)

    fig.update_layout(title_text=title,
                      updatemenus=[dict(buttons=list([dict(label="Linear",
                                                           method="relayout",
                                                           args=[{"yaxis.type": "linear"}]),
                                                      dict(label="Log",
                                                           method="relayout",
                                                           args=[{"yaxis.type": "log"}]),
                                                      ]),
                                        direction="right",
                                        pad={"r": 10, "t": 10},
                                        showactive=True,
                                        x=0,
                                        xanchor="left",
                                        y=-0.6,
                                        yanchor="top",
                                        bgcolor='rgba(100,100,100,0.2)',
                                        font=dict(color='#111', size=12)
                                        )], font=dict(color='black', size=12),
                  plot_bgcolor='rgba(100,100,100,0)')

    return fig

def confirm_rate(confirmed, c=0, cntry_name='#'):
    # CDF
    case_type = case_dict[c]
    if cntry_name == '#':
        title = f'Rate of {case_type} cases in the world'
        confirmed = date_wise(confirmed.sum(axis=0)).iloc[132:]
    else:
        title = f'Rate of {case_type} cases in {cntry_name}'
        confirmed = date_wise(confirmed[confirmed['Country'] == cntry_name].sum(axis=0)).iloc[132:]

    color = color_dict[c]
    daily_confirmed = confirmed.iloc[:-1].copy()

    den = confirmed.iloc[:-1].Value.values
    den = np.where(den == 0, 1, den)
    daily_confirmed['Value'] = 100 * (
                confirmed.iloc[1:].Value.values - confirmed.iloc[:-1].Value.values) / den

    fig = go.Figure(
        go.Scatter(x=daily_confirmed['Date'], y=daily_confirmed['Value'], line_color=color, mode='lines+markers'),
        layout=go.Layout(template='plotly_white'))

    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(step="all")
            ]), font=dict(color='black', size=12)
        )
    )

    fig.update_traces(marker_color=color, marker_line_color=hue(color),
                      marker_line_width=1.5)

    fig.update_layout(title_text=title,
                      updatemenus=[dict(buttons=list([dict(label="Linear",
                                                           method="relayout",
                                                           args=[{"yaxis.type": "linear"}]),
                                                      dict(label="Log",
                                                           method="relayout",
                                                           args=[{"yaxis.type": "log"}]),
                                                      ]),
                                        direction="right",
                                        pad={"r": 10, "t": 10},
                                        showactive=True,
                                        x=0,
                                        xanchor="left",
                                        y=-0.6,
                                        yanchor="top",
                                        bgcolor='rgba(100,100,100,0.2)',
                                        font=dict(color='#111', size=12)
                                        )], font=dict(color='black', size=12),
                  plot_bgcolor='rgba(100,100,100,0)')

    return fig

def save_to_csv(username, email, country_code, phone_number, location):
    with open('user_list.csv', 'a', newline='') as csvfile:
        filewriter = csv.writer(csvfile)
        filewriter.writerow([username, email, country_code, phone_number, location])
    return '''Username :{},
                 Email :{},
                 Mobile :{},
                 Location :{},
                Successfully Subscribed !!'''.format(username, email, str(country_code) + str(phone_number), location)    


def send_to_twilio():
    with open('user_list.csv', mode ='r')as file:
        file_reader = csv.reader(file)
        for line in file_reader:
            try:
                print(line)        
                message = send_twilio_message(line[0], line[2], line[3], line[4])
            except Exception as e:
                print(e)

                