import dash_table
import pandas as pd
import dash_ag_grid as dag


KEY_COLUMNS = [
    "Symbol",
    "Name",
    "Exchange",
    "Country",
    "Sector",
    "Industry",
    "MarketCapitalization",
    "RevenueTTM",
    "RevenuePerShareTTM",
    "ProfitMargin",
    "OperatingMarginTTM",
    "EBITDA",
    "AnalystTargetPrice",
    "AnalystRatingStrongBuy",
    "AnalystRatingBuy",
    "AnalystRatingHold",
    "AnalystRatingSell",
    "AnalystRatingStrongSell",
]


def build_overview_grid(overview_df: pd.DataFrame):
    # Keep only desired columns
    display_cols = [c for c in KEY_COLUMNS if c in overview_df.columns]
    df = overview_df[display_cols].copy()

    # Ensure numeric types for formatting in the grid (strings from API -> numbers)
    num_cols = [
        "MarketCapitalization",
        "RevenueTTM",
        "RevenuePerShareTTM",
        "ProfitMargin",
        "OperatingMarginTTM",
        "EBITDA",
        "AnalystTargetPrice",
    ]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Column definitions with formatters and filter/sort
    column_defs = []
    for c in display_cols:
        col_def = {
            "headerName": c,
            "field": c,
            "sortable": True,
            "filter": True,
            "resizable": True,
        }
        if c in [
            "MarketCapitalization",
            "RevenueTTM",
            "EBITDA",
            "AnalystTargetPrice",
            "RevenuePerShareTTM",
        ]:
            # Format as USD; implemented in assets/dashAgGridFunctions.js
            col_def["type"] = "numericColumn"
            col_def["valueFormatter"] = {"function": "USD(params.value)"}
        if c in ["ProfitMargin", "OperatingMarginTTM"]:
            col_def["type"] = "numericColumn"
            col_def["valueFormatter"] = {"function": "PCT(params.value)"}
        if c == "RevenueTTM":
            # Flag low revenue
            col_def["cellClassRules"] = {
                "low-rev": "params.value != null && Number(params.value) < 1e9"  # < $1B
            }
        column_defs.append(col_def)

    default_col_def = {
        "flex": 1,
        "minWidth": 140,
        "suppressMenu": False,
        "wrapText": False,
    }

    return dag.AgGrid(
        id="overview-grid",
        className="ag-theme-quartz-dark",
        rowData=df.fillna("N/A").to_dict("records"),
        columnDefs=column_defs,
        defaultColDef=default_col_def,
        dashGridOptions={
            "animateRows": True,
            "rowSelection": "single",
        },
        style={"height": "320px", "width": "100%"},
    )
