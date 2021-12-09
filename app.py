import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
import krakenex
from datetime import datetime
import time
import pandas as pd
import json


def get_pairs_available():
    posibles_valores = k.query_public('AssetPairs', data="info=info")['result']
    human_name_list = []
    api_name_list = []
    for i in posibles_valores:
        human_name_list.append(posibles_valores[i]['wsname'])
        api_name_list.append(i)

    data = {'label': human_name_list, 'value': api_name_list}
    return pd.DataFrame(data)


def get_df_ohlc(pair="XXBTZUSD", interval=21600, start_time=''):
    r_ohlc = k.query_public('OHLC', data="pair="+pair +
                            "&interval="+str(interval)
                            + "&since="+str(start_time))
    if r_ohlc['error'] != []:
        print(r_ohlc['error'])
    try:
        data_ohlc = r_ohlc['result'][pair]
        create_df_ohlc = pd.DataFrame(data=data_ohlc,
                                      columns=["time", "open",
                                               "high", "low",
                                               'close', 'vwap',
                                               'volume', 'count'])
        cols = create_df_ohlc.columns[create_df_ohlc.dtypes.eq('object')]
        create_df_ohlc[cols] = create_df_ohlc[cols].apply(pd.to_numeric)
        create_df_ohlc['human_time'] = create_df_ohlc.time.apply(
            lambda x: datetime.utcfromtimestamp(x)
            .strftime('%Y-%m-%d %H:%M:%S'))
    except Exception:
        data = {'time': [], 'open': [],
                'high': [], 'low': [],
                'close': [], 'vwap': [],
                'volume': [], 'count': []}
        return pd.DataFrame(data)

    return create_df_ohlc


def get_df_trade(pair="XXBTZUSD", start_time=''):
    r_trade = k.query_public('Trades', data="pair=" +
                             pair+"&since="+str(start_time))
    if r_trade['error'] != []:
        print(r_trade['error'])
    try:
        data_trade = r_trade['result'][pair]
        create_df_trade = pd.DataFrame(data=data_trade, columns=[
                                       "price", "volume",
                                       "time", "buy_sell",
                                       'market_limit', 'miscellaneous'])
        time_min = create_df_trade.time.min()
        time_max = create_df_trade.time.max()
        create_df_trade["price"] = pd.to_numeric(create_df_trade["price"])
        create_df_trade["volume"] = pd.to_numeric(create_df_trade["volume"])

        create_df_trade['v_p'] = create_df_trade.apply(
            lambda row: row.price*row.volume, axis=1)
        step = (time_max-time_min)/30
        human_time = []
        open_list = []
        close_list = []
        high_list = []
        low_list = []
        vwap_list = []
        for i in range(30):
            create_df_trade_temp = create_df_trade[(
                (create_df_trade.time) > (time_min+(i)*step))
                & ((create_df_trade.time) < (time_min+(i+1)*step))]
            if create_df_trade_temp.shape[0] != 0:
                human_time.append(datetime.utcfromtimestamp(
                    time_min+(i)*step).strftime('%Y-%m-%d %H:%M:%S'))
                open_list.append(create_df_trade_temp.iloc[0].price)
                close_list.append(create_df_trade_temp.iloc[-1].price)
                high_list.append(create_df_trade_temp.price.max())
                low_list.append(create_df_trade_temp.price.min())
                if(create_df_trade_temp.volume.sum() > 0):
                    vwap_list.append(create_df_trade_temp.v_p.sum(
                    )/create_df_trade_temp.volume.sum())
                else:
                    vwap_list.append(0)
        data = {'human_time': human_time, 'open': open_list,
                'close': close_list, 'high': high_list,
                'low': low_list, 'vwap': vwap_list}
        return pd.DataFrame(data)

    except Exception:
        data = {'human_time': [], 'open': [],
                'close': [], 'high': [],
                'low': [], 'vwap': []}
        return pd.DataFrame(data)
    return create_df_trade


k = krakenex.API()
df = get_df_ohlc()
df_pairs = get_pairs_available()
result = df_pairs.to_json(orient="records")
parsed = json.loads(result)

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Analisis criptomonedas"
server = app.server

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(
                    children="Cotización criptomonedas",
                    className="header-title"
                ),
                html.P(
                    children="Grafico con la cotización de un par de \
                    monedas elegidas. Es posible ver la grafica de llamar al \
                    metodo OHLC o Trades de Kraken",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            id='menu-opciones-calculo',
            children=[
                html.Div(
                    children=[
                        html.Div(children="Tipo calculo",
                                 className="menu-title"),
                        dcc.RadioItems(
                            id='show-table',
                            options=[{'label': 'Metodo OHLC', 'value': 'OHLC'},
                                     {'label': 'Metodo Trade',
                                      'value': 'Trade'}
                                     ],
                            value='OHLC',
                            labelStyle={'display': 'inline-block'}
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            id='menu-opciones-OHLC',
            children=[
                html.Div(
                    children=[
                        html.Div(children="Region", className="menu-title"),
                        dcc.Dropdown(
                            id='choose-pair',
                            options=parsed,
                            value='XBTUSDC',
                            clearable=False,
                            className="dropdown",
                        )
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Agrupacion",
                                 className="menu-title"),
                        dcc.Dropdown(
                            id='choose-grouptime',
                            options=[
                                {'label': '1 minuto', 'value': 1},
                                {'label': '5 minutos', 'value': 5},
                                {'label': '15 minutos', 'value': 15},
                                {'label': '30 minutos', 'value': 30},
                                {'label': '1 hora', 'value': 60},
                                {'label': '4 hora', 'value': 240},
                                {'label': '1 dia', 'value': 1440},
                                {'label': '1 semana', 'value': 10080},
                                {'label': '15 dias', 'value': 21600},
                            ],
                            value=21600,
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
            ],
            className="menu",
        ),
        html.Div(
            id='menu-opciones-Trade',
            children=[
                html.Div(
                    children=[
                        html.Div(children="Region", className="menu-title"),
                        dcc.Dropdown(
                            id='choose-pair-trade',
                            options=parsed,
                            value='XBTUSDC',
                            clearable=False,
                            className="dropdown",
                        )
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="chart_ohlc", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="chart_trade", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(
    [Output('menu-opciones-OHLC', 'style'),
     Output('menu-opciones-Trade', 'style'),
     Output('chart_ohlc', 'style'),
     Output('chart_trade', 'style')],
    [Input('show-table', 'value')])
def toggle_container(toggle_value):
    if toggle_value == 'OHLC' or toggle_value is None:
        return ({'display': 'flex'}, {'display': 'none'},
                {'display': 'flex'}, {'display': 'none'})
    else:
        return ({'display': 'none'}, {'display': 'flex'},
                {'display': 'none'}, {'display': 'flex'})


@app.callback(
    Output("chart_ohlc", "figure"),
    [Input("choose-pair", "value"), Input("choose-grouptime", "value")])
def update_line_chart(pair_to_call, interval_to_call):
    fig = go.Figure()
    if interval_to_call is None:
        interval_to_call = 21600
    if pair_to_call not is None:
        df = get_df_ohlc(pair=pair_to_call, interval=interval_to_call)
        velas = go.Candlestick(x=df.human_time,
                               open=df.open,
                               high=df.high,
                               low=df.low,
                               close=df.close,
                               xaxis="x",
                               yaxis="y",
                               name='cotizacion',
                               visible=True)
        linea = go.Scatter(x=df.human_time, y=df.vwap,
                           mode='lines', name='vwap')
        fig.add_trace(velas)
        fig.add_trace(linea)
        fig.update(layout_xaxis_rangeslider_visible=False)
    return fig


@app.callback(
    Output("chart_trade", "figure"),
    [Input("choose-pair-trade", "value")])
def update_line_chart_calculate(pair_to_call):
    fig = go.Figure()
    if pair_to_call is not None:
        df = get_df_trade(pair=pair_to_call)
        velas = go.Candlestick(x=df.human_time,
                               open=df.open,
                               high=df.high,
                               low=df.low,
                               close=df.close,
                               xaxis="x",
                               yaxis="y",
                               name='cotizacion',
                               visible=True)
        linea = go.Scatter(x=df.human_time, y=df.vwap,
                           mode='lines', name='vwap')
        fig.add_trace(velas)
        fig.add_trace(linea)
        fig.update(layout_xaxis_rangeslider_visible=False)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
