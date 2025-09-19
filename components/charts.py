from dash import dcc
import plotly.graph_objs as go
import pandas as pd

def format_intraday_data(time_series_json):
    """
    Convert Alpha Vantage time series JSON to a DataFrame.
    """
    df = pd.DataFrame.from_dict(time_series_json, orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns=lambda s: s.split('. ')[1])  # Remove numeric prefixes if needed
    return df

def build_vendor_chart(symbol_data_dict):
    """
    Build a Plotly line chart comparing closing prices over time for all vendors.
    symbol_data_dict: {symbol: time_series_dict}
    """
    fig = go.Figure()
    for symbol, series in symbol_data_dict.items():
        df = format_intraday_data(series)
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["close"].astype(float),
            mode="lines",
            name=symbol
        ))

    fig.update_layout(
        template="plotly_dark",
        title="Vendor Closing Price (Intraday)",
        xaxis_title="Time",
        yaxis_title="Close Price",
        legend_title="Vendor"
    )

    return dcc.Graph(figure=fig)
