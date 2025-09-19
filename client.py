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
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DB = CACHE_DIR / "vendor_cache.sqlite"
TTL_BY_FUNCTION = {
    "OVERVIEW": 24 * 3600,           # 24h
    "INCOME_STATEMENT": 24 * 3600,   # 24h
}

def _get_conn():
    return sqlite3.connect(str(CACHE_DB), check_same_thread=False)

def _init_cache():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_cache (
                function TEXT,
                symbol   TEXT,
                params_hash TEXT,
                response TEXT,
                timestamp INTEGER,
                PRIMARY KEY (function, symbol, params_hash)
            )
        """)
_init_cache()

def _params_hash(params: dict) -> str:
    items = sorted(params.items())
    return "|".join(f"{k}={v}" for k, v in items) if items else "_"

def cache_get(function: str, symbol: str, params_extra: dict | None) -> dict | None:
    ph = _params_hash(params_extra or {})
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT response, timestamp FROM api_cache WHERE function=? AND symbol=? AND params_hash=?",
            (function, symbol, ph)
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
            (function, symbol, ph, json.dumps(payload), int(time.time()))
        )

def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,                   # 1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

SESSION = _build_session()

def _is_limit_or_error(payload: dict) -> bool:
    # Handles Limit errors
    return any(k in payload for k in ["Information", "Note", "Error Message"])

def _cached_api_call(function: str, symbol: str, params_extra: dict | None = None, allow_stale_on_limit: bool = True):
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
        raise RuntimeError(data.get("Information") or data.get("Note") or data.get("Error Message") or "Unknown API error")

    cache_set(function, symbol, params_extra, data)
    return data

SAMPLE_RETURN = {
    "Symbol": "IBM",
    "AssetType": "Common Stock",
    "Name": "International Business Machines",
    "Description": "International Business Machines Corporation (IBM) is a leading American multinational technology company based in Armonk, New York, with a presence in over 170 countries. Founded in 1911, IBM has evolved into a powerhouse of innovation, offering a wide array of hardware, software, and consulting services, along with a strong focus on artificial intelligence, quantum computing, and cloud solutions. The company is renowned for its robust research capabilities, holding the record for the most annual U.S. patents for 28 consecutive years, demonstrating its commitment to technological advancement. Notable inventions, including the ATM and relational database, underline IBM’s pivotal role in shaping modern computing. As IBM continues to adapt its strategies to meet the dynamic demands of the digital era, it remains a key player in driving technological progress across multiple industries.",
    "CIK": "51143",
    "Exchange": "NYSE",
    "Currency": "USD",
    "Country": "USA",
    "Sector": "TECHNOLOGY",
    "Industry": "INFORMATION TECHNOLOGY SERVICES",
    "Address": "ONE NEW ORCHARD ROAD, ARMONK, NY, UNITED STATES, 10504",
    "OfficialSite": "https://www.ibm.com",
    "FiscalYearEnd": "December",
    "LatestQuarter": "2025-06-30",
    "MarketCapitalization": "246852600000",
    "EBITDA": "14183000000",
    "PERatio": "42.74",
    "PEGRatio": "1.601",
    "BookValue": "29.53",
    "DividendPerShare": "6.69",
    "DividendYield": "0.0258",
    "EPS": "6.2",
    "RevenuePerShareTTM": "69.07",
    "ProfitMargin": "0.0911",
    "OperatingMarginTTM": "0.183",
    "ReturnOnAssetsTTM": "0.0481",
    "ReturnOnEquityTTM": "0.227",
    "RevenueTTM": "64040002000",
    "GrossProfitTTM": "36868002000",
    "DilutedEPSTTM": "6.2",
    "QuarterlyEarningsGrowthYOY": "0.177",
    "QuarterlyRevenueGrowthYOY": "0.077",
    "AnalystTargetPrice": "281.25",
    "AnalystRatingStrongBuy": "1",
    "AnalystRatingBuy": "7",
    "AnalystRatingHold": "9",
    "AnalystRatingSell": "2",
    "AnalystRatingStrongSell": "1",
    "TrailingPE": "42.74",
    "ForwardPE": "22.08",
    "PriceToSalesRatioTTM": "3.855",
    "PriceToBookRatio": "8.77",
    "EVToRevenue": "4.585",
    "EVToEBITDA": "22.76",
    "Beta": "0.697",
    "52WeekHigh": "294.17",
    "52WeekLow": "197.92",
    "50DayMovingAverage": "256.06",
    "200DayMovingAverage": "251.01",
    "SharesOutstanding": "931519000",
    "SharesFloat": "929395000",
    "PercentInsiders": "0.122",
    "PercentInstitutions": "65.148",
    "DividendDate": "2025-09-10",
    "ExDividendDate": "2025-08-08"
}


def get_company_overview(symbol: str) -> dict:
    """Alpha Vantage Fundamental Data: Company Overview (returns raw JSON)."""
    #return _cached_api_call("OVERVIEW", symbol)
    return SAMPLE_RETURN

def get_income_statement(symbol: str) -> dict:
    """Alpha Vantage Fundamental Data: Income Statement (returns raw JSON)."""
    return _cached_api_call("INCOME_STATEMENT", symbol)


