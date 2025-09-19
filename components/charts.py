from dash import dcc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd

# Pastel color palette
PASTEL_COLORS = [
    '#A8D8EA',  # Light blue
    '#FFB7B7',  # Light pink
    '#C7CEDB',  # Light purple
    '#FFEAA7',  # Light yellow
    '#DDA0DD',  # Plum
    '#98D8C8',  # Mint
    '#F7DC6F',  # Light gold
    '#AED6F1'   # Sky blue
]

def create_bar_chart(df: pd.DataFrame, target_field: str):
    """Create a bar chart for the target field across all symbols."""
    df_chart = df.copy()
    if target_field in df_chart.columns:
        df_chart[target_field] = pd.to_numeric(df_chart[target_field], errors='coerce')
    
    fig = go.Figure(data=[
        go.Bar(
            x=df_chart['Symbol'],
            y=df_chart[target_field],
            name=target_field,
            marker_color=PASTEL_COLORS[:len(df_chart)],
            marker_line=dict(width=1, color='rgba(255,255,255,0.3)')
        )
    ])
    
    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text=f"{target_field} by Vendor",
            font=dict(size=16, color='#E8E8E8'),
            x=0.5
        ),
        xaxis_title="Vendor Symbol",
        yaxis_title=target_field,
        showlegend=False,
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor='rgba(42, 42, 42, 0.8)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E8E8E8', size=12)
    )
    
    return dcc.Graph(figure=fig, id="bar-chart")

def create_bubble_chart(df: pd.DataFrame, target_field_x: str, target_field_y: str):
    """Create a bubble chart with MarketCap as x-axis, target as y-axis, Revenue as bubble size."""
    df_chart = df.copy()
    
    # Convert fields to numeric
    numeric_fields = [target_field_x, target_field_y, 'RevenueTTM']
    for field in numeric_fields:
        if field in df_chart.columns:
            df_chart[field] = pd.to_numeric(df_chart[field], errors='coerce')
    
    # Create bubble chart with pastel colors
    fig = px.scatter(
        df_chart,
        x=target_field_x,
        y=target_field_y,
        size='RevenueTTM',
        color='Symbol',
        hover_name='Symbol',
        hover_data=['Name', 'Sector'],
        title=f"{target_field_x} vs {target_field_y}",
        template="plotly_dark",
        size_max=50,
        color_discrete_sequence=PASTEL_COLORS
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_title=target_field_x,
        yaxis_title=target_field_y,
        title=dict(
            text=f"{target_field_y} vs {target_field_x} (Revenue as bubble size)",
            font=dict(size=16, color='#E8E8E8'),
            x=0.5
        ),
        plot_bgcolor='rgba(42, 42, 42, 0.8)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E8E8E8', size=12),
        legend=dict(
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='rgba(255,255,255,0.2)',
            borderwidth=1
        )
    )
    
    # Update traces for better bubble appearance
    fig.update_traces(
        marker=dict(
            line=dict(width=1, color='rgba(255,255,255,0.4)'),
            opacity=0.8
        )
    )
    
    return dcc.Graph(figure=fig, id="bubble-chart")

# Available target fields for the dropdowns
CHART_TARGET_OPTIONS = [
    {'label': 'Market Capitalization', 'value': 'MarketCapitalization'},
    {'label': 'Revenue TTM', 'value': 'RevenueTTM'},
    {'label': 'EBITDA', 'value': 'EBITDA'},
    {'label': 'P/E Ratio', 'value': 'PERatio'},
    {'label': 'Profit Margin', 'value': 'ProfitMargin'},
    {'label': 'Operating Margin TTM', 'value': 'OperatingMarginTTM'},
    {'label': 'ROA TTM', 'value': 'ReturnOnAssetsTTM'},
    {'label': 'ROE TTM', 'value': 'ReturnOnEquityTTM'},
    {'label': 'EPS', 'value': 'EPS'},
    {'label': 'Book Value', 'value': 'BookValue'},
    {'label': 'Beta', 'value': 'Beta'},
    {'label': 'Dividend Yield', 'value': 'DividendYield'}
]
