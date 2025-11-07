"""Constants for the Fermax Blue integration."""
from typing import Final

DOMAIN: Final = "fermax_blue"

# Configuration keys
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"

# API endpoints - Updated to new Fermax DuoxMe infrastructure (2025)
OAUTH_URL: Final = "https://oauth-pro-duoxme.fermax.io/oauth/token"
BASE_URL: Final = "https://pro-duoxme.fermax.io"
USER_INFO_URL: Final = f"{BASE_URL}/user/api/v1/users/me"
PAIRINGS_URL: Final = f"{BASE_URL}/pairing/api/v3/pairings/me"
DEVICE_INFO_URL: Final = f"{BASE_URL}/deviceaction/api/v1/device"
OPEN_DOOR_URL: Final = f"{BASE_URL}/deviceaction/api/v1/device"

# OAuth credentials (from app)
OAUTH_CLIENT_AUTH: Final = "Basic ZHB2N2lxejZlZTVtYXptMWlxOWR3MWQ0MnNseXV0NDhrajBtcDVmdm81OGo1aWg6Yzd5bGtxcHVqd2FoODV5aG5wcnYwd2R2eXp1dGxjbmt3NHN6OTBidWxkYnVsazE="

# Common headers
APP_VERSION: Final = "3.2.1"
APP_BUILD: Final = "3"
PHONE_OS: Final = "16.4"
PHONE_MODEL: Final = "iPad14,5"
USER_AGENT: Final = f"Blue/{APP_VERSION} (com.fermax.bluefermax; build:{APP_BUILD}; iOS {PHONE_OS}) Alamofire/{APP_VERSION}"

# Device classes
DEVICE_CLASS_DOOR: Final = "door"

# Entity names
ENTITY_OPEN_DOOR: Final = "Open Door"

# Default values
DEFAULT_TIMEOUT: Final = 30
TOKEN_CACHE_FILE: Final = "fermax_blue_token.json"

# Error messages
ERROR_INVALID_AUTH: Final = "Invalid authentication credentials"
ERROR_CANNOT_CONNECT: Final = "Cannot connect to Fermax Blue API"
ERROR_TIMEOUT: Final = "Request timed out"
ERROR_UNKNOWN: Final = "Unknown error occurred"