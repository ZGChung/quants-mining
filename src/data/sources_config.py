"""
Data Sources Configuration
"""

# API Keys storage (user can set these in Streamlit secrets)
API_KEYS = {
    "alpha_vantage": None,  # Set via streamlit secrets
    "finnhub": None,
    "polygon": None,
}

# Data source priorities
DATA_SOURCES = {
    "yahoo": {
        "name": "Yahoo Finance",
        "free": True,
        "rate_limit": "2000/day",
        "requires_key": False,
    },
    "alpha_vantage": {
        "name": "Alpha Vantage",
        "free": True,
        "rate_limit": "25/day (free), 75/min (premium)",
        "requires_key": True,
    },
    "finnhub": {
        "name": "Finnhub",
        "free": True,
        "rate_limit": "60 calls/min",
        "requires_key": True,
    },
    "polygon": {
        "name": "Polygon.io",
        "free": True,
        "rate_limit": "5 calls/min (free)",
        "requires_key": True,
    },
}


def get_available_sources():
    """Get list of available data sources"""
    available = ["yahoo"]  # Yahoo is always available
    for source, config in DATA_SOURCES.items():
        if config["requires_key"] and API_KEYS.get(source):
            available.append(source)
    return available
