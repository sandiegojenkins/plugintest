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
}

# Default Values
DEFAULT_BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_BACKOFF = 1
