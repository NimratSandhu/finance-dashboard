import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from components.tables import build_vendor_table, build_overview_table
from components.charts import build_vendor_chart
from client import get_company_overview, get_income_statement


SYMBOLS = ['TEL', 'ST', 'DD', 'CE', 'LYB']

app = dash.Dash(
    __name__,
)
app.title = "WindBorne Vendor Dashboard"

overview = [get_company_overview(s) for s in SYMBOLS]
overview_df = pd.DataFrame([get_company_overview(s) for s in SYMBOLS])
overview_table = build_overview_table(overview_df)

print(overview_df)
print(overview_df.columns)

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("WindBorne Vendor Dashboard"), width=12)
    ]),
    dbc.Row([
        dbc.Col(overview_table, width=12)
    ]),
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True)
