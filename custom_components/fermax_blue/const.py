"""Constants for the Fermax Blue integration."""
from typing import Final

DOMAIN: Final = "fermax_blue"

# Configuration keys
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"

# API endpoints
BASE_URL: Final = "https://api.fermax.com"
AUTH_URL: Final = f"{BASE_URL}/auth/login"
DEVICES_URL: Final = f"{BASE_URL}/devices"
OPEN_DOOR_URL: Final = f"{BASE_URL}/access/open"

# Device classes
DEVICE_CLASS_DOOR: Final = "door"

# Entity names
ENTITY_OPEN_DOOR: Final = "Open Door"

# Default values
DEFAULT_TIMEOUT: Final = 10
TOKEN_CACHE_FILE: Final = "fermax_blue_token.json"

# Error messages
ERROR_INVALID_AUTH: Final = "Invalid authentication credentials"
ERROR_CANNOT_CONNECT: Final = "Cannot connect to Fermax Blue API"
ERROR_TIMEOUT: Final = "Request timed out"
ERROR_UNKNOWN: Final = "Unknown error occurred"