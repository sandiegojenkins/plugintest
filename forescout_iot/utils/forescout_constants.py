"""
Forescout Plugin Constants.
"""

MODULE_NAME = "IoT"
PLUGIN_NAME = "Forescout"
PLUGIN_VERSION = "1.0.0"
PLATFORM_NAME = "Forescout"

# API Endpoints
API_ENDPOINTS = {
    "hosts": "{}/api/hosts",  # Placeholder, needs verification
    "login": "{}/api/login",  # Placeholder
    "rem_assets": "{}/api/data-exchange/v3/rem-assets",
}

# Default Values
DEFAULT_BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_BACKOFF = 1
DEFAULT_LOOKBACK_MINS = 60

REM_ASSET_FIELDS = [
    "ip_addresses",
    "mac_addresses",
    "rem_category",
    "rem_vendor",
    "rem_os",
    "rem_function",
    "risk_score"
]
