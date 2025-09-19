import os
import json
import time
import sqlite3
import requests
from pathlib import Path
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()
API_KEY = os.getenv("ALPHAVANTAGE_KEY")
BASE_URL = "https://www.alphavantage.co/query"
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/vendor_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DB = CACHE_DIR / "vendor_cache.sqlite"
TTL_BY_FUNCTION = {
    "OVERVIEW": 24 * 3600,  # 24h
    "INCOME_STATEMENT": 24 * 3600,  # 24h
}


def _get_conn():
    return sqlite3.connect(str(CACHE_DB), check_same_thread=False)


def _init_cache():
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_cache (
                function TEXT,
                symbol   TEXT,
                params_hash TEXT,
                response TEXT,
                timestamp INTEGER,
                PRIMARY KEY (function, symbol, params_hash)
            )
        """
        )


_init_cache()


def _params_hash(params: dict) -> str:
    items = sorted(params.items())
    return "|".join(f"{k}={v}" for k, v in items) if items else "_"


def cache_get(function: str, symbol: str, params_extra: dict | None) -> dict | None:
    ph = _params_hash(params_extra or {})
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT response, timestamp FROM api_cache WHERE function=? AND symbol=? AND params_hash=?",
            (function, symbol, ph),
        ).fetchone()
    if not row:
        return None
    response_text, ts = row
    try:
        return {"data": json.loads(response_text), "ts": ts}
    except json.JSONDecodeError:
        return None


def cache_set(function: str, symbol: str, params_extra: dict | None, payload: dict):
    ph = _params_hash(params_extra or {})
    with _get_conn() as conn:
        conn.execute(
            "REPLACE INTO api_cache (function, symbol, params_hash, response, timestamp) VALUES (?, ?, ?, ?, ?)",
            (function, symbol, ph, json.dumps(payload), int(time.time())),
        )


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,  # 1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = _build_session()


def _is_limit_or_error(payload: dict) -> bool:
    # Handles Limit errors
    return any(k in payload for k in ["Information", "Note", "Error Message"])


def _cached_api_call(
    function: str,
    symbol: str,
    params_extra: dict | None = None,
    allow_stale_on_limit: bool = True,
):
    params_extra = params_extra or {}
    ttl = TTL_BY_FUNCTION.get(function, 24 * 3600)
    cached = cache_get(function, symbol, params_extra)

    # Serve fresh cache if within TTL
    now = int(time.time())
    if cached and (now - cached["ts"] < ttl):
        return cached["data"]

    # Make API call
    params = {"function": function, "symbol": symbol, "apikey": API_KEY, **params_extra}
    resp = SESSION.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # If rate-limited or other informational response
    if _is_limit_or_error(data):
        if cached and allow_stale_on_limit:
            return cached["data"]
        raise RuntimeError(
            data.get("Information")
            or data.get("Note")
            or data.get("Error Message")
            or "Unknown API error"
        )

    cache_set(function, symbol, params_extra, data)
    return data


MOCK_OVERVIEW = [
    {
        "Symbol": "TEL",
        "AssetType": "Common Stock",
        "Name": "TE Connectivity Ltd.",
        "Description": "Global technology leader in connectors and sensors for harsh environments.",
        "CIK": "1385157",
        "Exchange": "NYSE",
        "Currency": "USD",
        "Country": "USA",
        "Sector": "Industrials",
        "Industry": "Electronic Components",
        "Address": "1050 Westlakes Dr, Berwyn, PA 19312",
        "OfficialSite": "https://www.te.com",
        "FiscalYearEnd": "September",
        "LatestQuarter": "2025-06-30",
        "MarketCapitalization": "42000000000",
        "EBITDA": "3800000000",
        "PERatio": "25.30",
        "PEGRatio": "1.80",
        "BookValue": "29.50",
        "DividendPerShare": "2.40",
        "DividendYield": "0.0170",
        "EPS": "6.20",
        "RevenuePerShareTTM": "72.50",
        "ProfitMargin": "0.120",
        "OperatingMarginTTM": "0.160",
        "ReturnOnAssetsTTM": "0.090",
        "ReturnOnEquityTTM": "0.220",
        "RevenueTTM": "23500000000",
        "GrossProfitTTM": "8400000000",
        "DilutedEPSTTM": "6.10",
        "QuarterlyEarningsGrowthYOY": "0.080",
        "QuarterlyRevenueGrowthYOY": "0.030",
        "AnalystTargetPrice": "170.00",
        "AnalystRatingStrongBuy": "5",
        "AnalystRatingBuy": "9",
        "AnalystRatingHold": "10",
        "AnalystRatingSell": "1",
        "AnalystRatingStrongSell": "0",
        "TrailingPE": "26.10",
        "ForwardPE": "22.40",
        "PriceToSalesRatioTTM": "2.10",
        "PriceToBookRatio": "5.80",
        "EVToRevenue": "2.20",
        "EVToEBITDA": "13.50",
        "Beta": "1.05",
        "52WeekHigh": "174.20",
        "52WeekLow": "121.80",
        "50DayMovingAverage": "162.40",
        "200DayMovingAverage": "154.20",
        "SharesOutstanding": "314000000",
        "SharesFloat": "312000000",
        "PercentInsiders": "0.50",
        "PercentInstitutions": "91.20",
        "DividendDate": "2025-09-10",
        "ExDividendDate": "2025-08-16",
    },
    {
        "Symbol": "ST",
        "AssetType": "Common Stock",
        "Name": "Sensata Technologies Holding plc",
        "Description": "Provider of sensor-rich solutions enabling electrification, efficiency, and safety.",
        "CIK": "1477294",
        "Exchange": "NYSE",
        "Currency": "USD",
        "Country": "USA",
        "Sector": "Industrials",
        "Industry": "Electronic Components",
        "Address": "529 Pleasant St, Attleboro, MA 02703",
        "OfficialSite": "https://www.sensata.com",
        "FiscalYearEnd": "December",
        "LatestQuarter": "2025-06-30",
        "MarketCapitalization": "6900000000",
        "EBITDA": "980000000",
        "PERatio": "17.50",
        "PEGRatio": "1.40",
        "BookValue": "25.10",
        "DividendPerShare": "0.48",
        "DividendYield": "0.0130",
        "EPS": "2.85",
        "RevenuePerShareTTM": "32.40",
        "ProfitMargin": "0.085",
        "OperatingMarginTTM": "0.140",
        "ReturnOnAssetsTTM": "0.060",
        "ReturnOnEquityTTM": "0.110",
        "RevenueTTM": "5150000000",
        "GrossProfitTTM": "1680000000",
        "DilutedEPSTTM": "2.75",
        "QuarterlyEarningsGrowthYOY": "0.050",
        "QuarterlyRevenueGrowthYOY": "0.020",
        "AnalystTargetPrice": "48.00",
        "AnalystRatingStrongBuy": "3",
        "AnalystRatingBuy": "7",
        "AnalystRatingHold": "11",
        "AnalystRatingSell": "1",
        "AnalystRatingStrongSell": "0",
        "TrailingPE": "18.10",
        "ForwardPE": "14.90",
        "PriceToSalesRatioTTM": "1.30",
        "PriceToBookRatio": "2.10",
        "EVToRevenue": "1.60",
        "EVToEBITDA": "8.40",
        "Beta": "1.32",
        "52WeekHigh": "52.60",
        "52WeekLow": "32.10",
        "50DayMovingAverage": "44.80",
        "200DayMovingAverage": "41.10",
        "SharesOutstanding": "153000000",
        "SharesFloat": "150000000",
        "PercentInsiders": "1.10",
        "PercentInstitutions": "98.00",
        "DividendDate": "2025-08-22",
        "ExDividendDate": "2025-08-07",
    },
    {
        "Symbol": "DD",
        "AssetType": "Common Stock",
        "Name": "DuPont de Nemours, Inc.",
        "Description": "Innovation-driven specialty materials and electronics company.",
        "CIK": "1666700",
        "Exchange": "NYSE",
        "Currency": "USD",
        "Country": "USA",
        "Sector": "Materials",
        "Industry": "Specialty Chemicals",
        "Address": "974 Centre Rd, Wilmington, DE 19805",
        "OfficialSite": "https://www.dupont.com",
        "FiscalYearEnd": "December",
        "LatestQuarter": "2025-06-30",
        "MarketCapitalization": "33000000000",
        "EBITDA": "4100000000",
        "PERatio": "22.10",
        "PEGRatio": "2.00",
        "BookValue": "39.70",
        "DividendPerShare": "1.44",
        "DividendYield": "0.0190",
        "EPS": "3.30",
        "RevenuePerShareTTM": "28.10",
        "ProfitMargin": "0.160",
        "OperatingMarginTTM": "0.210",
        "ReturnOnAssetsTTM": "0.070",
        "ReturnOnEquityTTM": "0.130",
        "RevenueTTM": "14200000000",
        "GrossProfitTTM": "5800000000",
        "DilutedEPSTTM": "3.25",
        "QuarterlyEarningsGrowthYOY": "0.120",
        "QuarterlyRevenueGrowthYOY": "0.040",
        "AnalystTargetPrice": "92.00",
        "AnalystRatingStrongBuy": "4",
        "AnalystRatingBuy": "10",
        "AnalystRatingHold": "9",
        "AnalystRatingSell": "1",
        "AnalystRatingStrongSell": "0",
        "TrailingPE": "23.00",
        "ForwardPE": "18.40",
        "PriceToSalesRatioTTM": "2.30",
        "PriceToBookRatio": "2.60",
        "EVToRevenue": "2.80",
        "EVToEBITDA": "9.70",
        "Beta": "1.06",
        "52WeekHigh": "89.50",
        "52WeekLow": "63.70",
        "50DayMovingAverage": "82.10",
        "200DayMovingAverage": "78.40",
        "SharesOutstanding": "425000000",
        "SharesFloat": "420000000",
        "PercentInsiders": "0.30",
        "PercentInstitutions": "79.40",
        "DividendDate": "2025-09-15",
        "ExDividendDate": "2025-08-29",
    },
    {
        "Symbol": "CE",
        "AssetType": "Common Stock",
        "Name": "Celanese Corporation",
        "Description": "Global chemical and specialty materials company serving diverse end markets.",
        "CIK": "1306830",
        "Exchange": "NYSE",
        "Currency": "USD",
        "Country": "USA",
        "Sector": "Materials",
        "Industry": "Specialty Chemicals",
        "Address": "222 W Las Colinas Blvd, Irving, TX 75039",
        "OfficialSite": "https://www.celanese.com",
        "FiscalYearEnd": "December",
        "LatestQuarter": "2025-06-30",
        "MarketCapitalization": "15500000000",
        "EBITDA": "2400000000",
        "PERatio": "13.90",
        "PEGRatio": "1.20",
        "BookValue": "74.30",
        "DividendPerShare": "2.80",
        "DividendYield": "0.0240",
        "EPS": "8.15",
        "RevenuePerShareTTM": "88.40",
        "ProfitMargin": "0.110",
        "OperatingMarginTTM": "0.170",
        "ReturnOnAssetsTTM": "0.055",
        "ReturnOnEquityTTM": "0.110",
        "RevenueTTM": "10500000000",
        "GrossProfitTTM": "3000000000",
        "DilutedEPSTTM": "8.05",
        "QuarterlyEarningsGrowthYOY": "0.090",
        "QuarterlyRevenueGrowthYOY": "0.050",
        "AnalystTargetPrice": "170.00",
        "AnalystRatingStrongBuy": "6",
        "AnalystRatingBuy": "8",
        "AnalystRatingHold": "7",
        "AnalystRatingSell": "1",
        "AnalystRatingStrongSell": "0",
        "TrailingPE": "14.30",
        "ForwardPE": "12.20",
        "PriceToSalesRatioTTM": "1.40",
        "PriceToBookRatio": "2.10",
        "EVToRevenue": "1.90",
        "EVToEBITDA": "8.10",
        "Beta": "1.20",
        "52WeekHigh": "177.40",
        "52WeekLow": "121.30",
        "50DayMovingAverage": "158.20",
        "200DayMovingAverage": "149.90",
        "SharesOutstanding": "109000000",
        "SharesFloat": "108000000",
        "PercentInsiders": "0.80",
        "PercentInstitutions": "95.10",
        "DividendDate": "2025-09-12",
        "ExDividendDate": "2025-08-23",
    },
    {
        "Symbol": "LYB",
        "AssetType": "Common Stock",
        "Name": "LyondellBasell Industries N.V.",
        "Description": "Leading global producer of plastics, chemicals, and refining products.",
        "CIK": "1489393",
        "Exchange": "NYSE",
        "Currency": "USD",
        "Country": "Netherlands",
        "Sector": "Materials",
        "Industry": "Commodity Chemicals",
        "Address": "Rotterdam, The Netherlands",
        "OfficialSite": "https://www.lyondellbasell.com",
        "FiscalYearEnd": "December",
        "LatestQuarter": "2025-06-30",
        "MarketCapitalization": "30000000000",
        "EBITDA": "5200000000",
        "PERatio": "12.60",
        "PEGRatio": "1.10",
        "BookValue": "41.20",
        "DividendPerShare": "4.80",
        "DividendYield": "0.0520",
        "EPS": "8.70",
        "RevenuePerShareTTM": "115.30",
        "ProfitMargin": "0.095",
        "OperatingMarginTTM": "0.130",
        "ReturnOnAssetsTTM": "0.070",
        "ReturnOnEquityTTM": "0.210",
        "RevenueTTM": "36000000000",
        "GrossProfitTTM": "8200000000",
        "DilutedEPSTTM": "8.55",
        "QuarterlyEarningsGrowthYOY": "0.060",
        "QuarterlyRevenueGrowthYOY": "0.030",
        "AnalystTargetPrice": "110.00",
        "AnalystRatingStrongBuy": "4",
        "AnalystRatingBuy": "9",
        "AnalystRatingHold": "12",
        "AnalystRatingSell": "1",
        "AnalystRatingStrongSell": "0",
        "TrailingPE": "12.90",
        "ForwardPE": "11.00",
        "PriceToSalesRatioTTM": "0.95",
        "PriceToBookRatio": "2.60",
        "EVToRevenue": "1.10",
        "EVToEBITDA": "6.80",
        "Beta": "1.27",
        "52WeekHigh": "109.80",
        "52WeekLow": "85.40",
        "50DayMovingAverage": "102.70",
        "200DayMovingAverage": "98.90",
        "SharesOutstanding": "325000000",
        "SharesFloat": "322000000",
        "PercentInsiders": "0.40",
        "PercentInstitutions": "76.50",
        "DividendDate": "2025-09-05",
        "ExDividendDate": "2025-08-12",
    },
]


def get_company_overview(symbol: str) -> dict:
    """Alpha Vantage Fundamental Data: Company Overview (returns raw JSON)."""
    # return _cached_api_call("OVERVIEW", symbol)
    return MOCK_OVERVIEW


def get_income_statement(symbol: str) -> dict:
    """Alpha Vantage Fundamental Data: Income Statement (returns raw JSON)."""
    return _cached_api_call("INCOME_STATEMENT", symbol)
