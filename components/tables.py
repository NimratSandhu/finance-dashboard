import dash_table
import pandas as pd

def format_intraday_data(time_series_json):
    """
    Convert Alpha Vantage time series JSON to a DataFrame.
    """
    df = pd.DataFrame.from_dict(time_series_json, orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns=lambda s: s.split('. ')[1])  # Remove numeric prefixes if needed
    return df

def build_vendor_table(symbol_data_dict):
    """
    Build a Dash DataTable for all vendors.
    symbol_data_dict: {symbol: time_series_dict}
    """
    # Collect latest record for each symbol
    latest_records = []
    for symbol, series in symbol_data_dict.items():
        df = format_intraday_data(series)
        latest_row = df.iloc[0]  # First row is most recent
        row_dict = latest_row.to_dict()
        row_dict["Symbol"] = symbol
        latest_records.append(row_dict)

    # Columns to show
    columns = [{"name": col, "id": col} for col in ["Symbol", "open", "high", "low", "close", "volume"]]

    return dash_table.DataTable(
        data=latest_records,
        columns=columns,
        style_table={"backgroundColor": "#333"},
        style_cell={"color": "#fff", "backgroundColor": "#222"},
        style_header={"backgroundColor": "#1a1a1a", "color": "#fff"},
        page_size=5
    )


KEY_COLUMNS = [
    'Symbol', 'Name', 'Exchange', 'Country', 'Sector', 'Industry',
    'MarketCapitalization', 'RevenueTTM', 'RevenuePerShareTTM',
    'ProfitMargin', 'OperatingMarginTTM', 'EBITDA',
    'AnalystTargetPrice', 'AnalystRatingStrongBuy', 'AnalystRatingBuy',
    'AnalystRatingHold', 'AnalystRatingSell', 'AnalystRatingStrongSell'
]


def build_overview_table(overview_df):
    # Filter columns to show only the most important ones
    display_columns = [col for col in KEY_COLUMNS if col in overview_df.columns]
    # Fill missing values for cleaner table
    df_display = overview_df[display_columns].fillna('N/A')
    # Format numbers for readability
    def prettify(x):
        if isinstance(x, (int, float)):
            return f"{x:,.2f}"
        return x
    df_display = df_display.applymap(prettify)
    return dash_table.DataTable(
        data=df_display.to_dict('records'),
        columns=[{"name": col, "id": col} for col in display_columns],
        style_table={"backgroundColor": "#333"},
        style_cell={"color": "#fff", "backgroundColor": "#222"},
        style_header={"backgroundColor": "#1a1a1a", "color": "#fff"},
        style_as_list_view=True,
        page_size=5
    )