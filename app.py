import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
from components.tables import build_overview_grid
from components.charts import (
    create_bar_chart,
    create_bubble_chart,
    CHART_TARGET_OPTIONS,
)
from client import get_company_overview, get_income_statement, MOCK_OVERVIEW

SYMBOLS = ["TEL", "ST", "DD", "CE", "LYB"]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.title = "WindBorne Vendor Dashboard"

# Mock data or real API calls

overview_df = pd.DataFrame(MOCK_OVERVIEW)
overview_table = build_overview_grid(overview_df)

# Initial charts with default target
bar_chart_default = "MarketCapitalization"
bubble_chart_x_default = 'ProfitMargin'
bubble_chart_y_default = "RevenueTTM"
initial_bar_chart = create_bar_chart(overview_df, bar_chart_default)
initial_bubble_chart = create_bubble_chart(
    overview_df, bubble_chart_x_default, bubble_chart_y_default
)

app.layout = dbc.Container(
    [
        dbc.Row(
            [dbc.Col(html.H1("WindBorne Vendor Dashboard"), width=12)], justify="center"
        ),
        dbc.Row([dbc.Col(overview_table, id="overview-table-section")]),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Bar Chart"),
                        html.Label(
                            "Select Metric:",
                            style={"color": "#BDC3C7", "marginBottom": "0.5rem"},
                        ),
                        dcc.Dropdown(
                            id="bar-chart-dropdown",
                            options=CHART_TARGET_OPTIONS,
                            value=bar_chart_default,
                            clearable=False,
                            style={"marginBottom": "1rem", "color": "#000"},
                        ),
                        html.Div(id="bar-chart-container"),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        html.H5("Bubble Chart"),
                        html.Label(
                            "Select Metrics:",
                            style={"color": "#BDC3C7", "marginBottom": "0.5rem"},
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="bubble-chart-x-dropdown",
                                        options=CHART_TARGET_OPTIONS,
                                        value=bubble_chart_x_default,
                                        clearable=False,
                                        style={"marginBottom": "1rem", "color": "#000"},
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="bubble-chart-y-dropdown",
                                        options=CHART_TARGET_OPTIONS,
                                        value=bubble_chart_y_default,
                                        clearable=False,
                                        style={"marginBottom": "1rem", "color": "#000"},
                                    ),
                                    width=6,
                                ),
                            ],
                            className="g-2",
                        ),
                        html.Div(id="bubble-chart-container"),
                    ],
                    width=6,
                ),
            ]
        ),
    ],
    fluid=True,
)


# Callback to update charts based on dropdown selection
@callback(
    Output("bar-chart-container", "children"), Input("bar-chart-dropdown", "value")
)
def update_bar_chart(selected_target):
    bar_chart = create_bar_chart(overview_df, selected_target)
    return bar_chart


@callback(
    Output("bubble-chart-container", "children"),
    Input("bubble-chart-x-dropdown", "value"),
    Input("bubble-chart-y-dropdown", "value"),
)
def bubble_bar_chart(selected_target_x, selected_target_y):
    bubble_chart = create_bubble_chart(
        overview_df, selected_target_x, selected_target_y
    )
    return bubble_chart


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
