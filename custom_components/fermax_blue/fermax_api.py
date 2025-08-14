"""Fermax Blue API client."""
import asyncio
import json
import logging
import ssl
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout
from aiohttp import ClientConnectorError

from .const import (
    OAUTH_URL,
    BASE_URL,
    USER_INFO_URL,
    PAIRINGS_URL,
    DEVICE_INFO_URL,
    OPEN_DOOR_URL,
    OAUTH_CLIENT_AUTH,
    APP_VERSION,
    APP_BUILD,
    PHONE_OS,
    PHONE_MODEL,
    USER_AGENT,
    DEFAULT_TIMEOUT,
    ERROR_INVALID_AUTH,
    ERROR_CANNOT_CONNECT,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)


class FermaxBlueAPIError(Exception):
    """Base exception for Fermax Blue API errors."""


class FermaxBlueAuthError(FermaxBlueAPIError):
    """Authentication error."""


class FermaxBlueConnectionError(FermaxBlueAPIError):
    """Connection error."""


class AccessId:
    """Access ID for door control."""
    
    def __init__(self, block: int, subblock: int, number: int):
        self.block = block
        self.subblock = subblock
        self.number = number
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for API calls."""
        return {
            "block": self.block,
            "subblock": self.subblock,
            "number": self.number
        }


class FermaxBlueAPI:
    """Fermax Blue API client."""

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self.username = username
        self.password = password
        self.session = session
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.pairings: List[Dict[str, Any]] = []
        self._common_headers = {
            "app-version": APP_VERSION,
            "accept-language": "en-ES;q=1.0, es-ES;q=0.9",
            "phone-os": PHONE_OS,
            "user-agent": USER_AGENT,
            "phone-model": PHONE_MODEL,
            "app-build": APP_BUILD,
        }

    def _needs_refresh(self) -> bool:
        """Check if token needs refresh."""
        if not self.access_token or not self.token_expires_at:
            return True
        # Refresh 5 minutes before expiration to avoid edge cases
        buffer_time = timedelta(minutes=5)
        return datetime.now(tz=timezone.utc) >= (self.token_expires_at - buffer_time)

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers for OAuth requests."""
        return {
            "Authorization": OAUTH_CLIENT_AUTH,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def _get_api_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            **self._common_headers
        }

    async def authenticate(self) -> bool:
        """Authenticate with Fermax Blue OAuth."""
        try:
            _LOGGER.debug(f"Authenticating with OAuth URL: {OAUTH_URL}")
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                data = {
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                }
                
                _LOGGER.debug("Sending OAuth authentication request...")
                _LOGGER.debug(f"Request data: grant_type=password, username={self.username}")
                
                async with self.session.post(
                    OAUTH_URL,
                    headers=self._get_auth_headers(),
                    data=data
                ) as response:
                    _LOGGER.debug(f"OAuth response status: {response.status}")
                    
                    if response.status == 200:
                        oauth_data = await response.json()
                        self.access_token = oauth_data.get("access_token")
                        self.refresh_token = oauth_data.get("refresh_token")
                        expires_in = oauth_data.get("expires_in", 3600)
                        
                        if self.access_token:
                            self.token_expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
                            _LOGGER.debug("Authentication successful")
                            return True
                        else:
                            raise FermaxBlueAuthError("No access token received")
                    elif response.status == 400 or response.status == 401:
                        error_data = await response.json()
                        error_desc = error_data.get("error_description", ERROR_INVALID_AUTH)
                        raise FermaxBlueAuthError(error_desc)
                    else:
                        error_text = await response.text()
                        _LOGGER.error(f"Unexpected HTTP status {response.status}: {error_text}")
                        raise FermaxBlueConnectionError(f"HTTP {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            _LOGGER.error(f"Authentication timeout after {DEFAULT_TIMEOUT} seconds")
            raise FermaxBlueConnectionError(ERROR_TIMEOUT)
        except ClientConnectorError as err:
            _LOGGER.error(f"Connection error: {err}")
            raise FermaxBlueConnectionError(f"Connection failed: {err}")
        except aiohttp.ClientError as err:
            _LOGGER.error(f"HTTP client error: {err}")
            raise FermaxBlueConnectionError(f"{ERROR_CANNOT_CONNECT}: {err}")
        except FermaxBlueAPIError:
            raise
        except Exception as err:
            _LOGGER.error(f"Unexpected error during authentication: {type(err).__name__}: {err}")
            raise FermaxBlueAPIError(f"{ERROR_UNKNOWN}: {err}")

    async def refresh_auth(self) -> bool:
        """Refresh authentication token."""
        if not self.refresh_token:
            _LOGGER.warning("No refresh token available, performing full authentication")
            return await self.authenticate()
            
        try:
            _LOGGER.debug("Attempting to refresh authentication token")
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                }
                
                async with self.session.post(
                    OAUTH_URL,
                    headers=self._get_auth_headers(),
                    data=data
                ) as response:
                    if response.status == 200:
                        oauth_data = await response.json()
                        self.access_token = oauth_data.get("access_token")
                        new_refresh_token = oauth_data.get("refresh_token")
                        if new_refresh_token:
                            self.refresh_token = new_refresh_token
                        expires_in = oauth_data.get("expires_in", 3600)
                        self.token_expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
                        _LOGGER.debug(f"Token refreshed successfully, expires in {expires_in} seconds")
                        return True
                    else:
                        error_text = await response.text()
                        _LOGGER.warning(f"Token refresh failed with status {response.status}: {error_text}")
                        # Refresh failed, try full auth
                        return await self.authenticate()
                        
        except Exception as err:
            _LOGGER.error(f"Exception during token refresh: {err}")
            # If refresh fails, try full authentication
            return await self.authenticate()

    async def _ensure_auth(self) -> bool:
        """Ensure we have a valid auth token."""
        if self._needs_refresh():
            _LOGGER.debug("Token needs refresh")
            if self.refresh_token:
                if not await self.refresh_auth():
                    _LOGGER.error("Failed to refresh authentication")
                    raise FermaxBlueAuthError("Failed to refresh authentication")
            else:
                if not await self.authenticate():
                    _LOGGER.error("Failed to authenticate")
                    raise FermaxBlueAuthError("Failed to authenticate")
        return True

    async def get_pairings(self) -> List[Dict[str, Any]]:
        """Get list of paired devices."""
        await self._ensure_auth()
        
        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                async with self.session.get(
                    PAIRINGS_URL,
                    headers=self._get_api_headers()
                ) as response:
                    if response.status == 200:
                        self.pairings = await response.json()
                        _LOGGER.debug(f"Found {len(self.pairings)} pairings")
                        return self.pairings
                    elif response.status == 401:
                        _LOGGER.warning("Authentication expired while getting pairings, refreshing...")
                        # Token expired, refresh and retry
                        if await self.refresh_auth():
                            return await self.get_pairings()
                        else:
                            raise FermaxBlueAuthError("Failed to refresh authentication")
                    else:
                        error_text = await response.text()
                        _LOGGER.error(f"Failed to get pairings: HTTP {response.status}: {error_text}")
                        raise FermaxBlueConnectionError(f"HTTP {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            _LOGGER.error(f"Get pairings timeout after {DEFAULT_TIMEOUT} seconds")
            raise FermaxBlueConnectionError(ERROR_TIMEOUT)
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error getting pairings: {err}")
            raise FermaxBlueConnectionError(f"{ERROR_CANNOT_CONNECT}: {err}")
        except FermaxBlueAPIError:
            raise
        except Exception as err:
            _LOGGER.error(f"Unexpected error getting pairings: {type(err).__name__}: {err}")
            raise FermaxBlueAPIError(f"{ERROR_UNKNOWN}: {err}")

    async def open_door(self, device_id: str, access_id: AccessId) -> bool:
        """Open a door using device ID and access ID."""
        await self._ensure_auth()
        
        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                url = f"{OPEN_DOOR_URL}/{device_id}/directed-opendoor"
                data = json.dumps(access_id.to_dict())
                
                _LOGGER.debug(f"Opening door: device_id={device_id}, access_id={access_id.to_dict()}")
                
                async with self.session.post(
                    url,
                    headers=self._get_api_headers(),
                    data=data
                ) as response:
                    result_text = await response.text()
                    _LOGGER.debug(f"Door open response: status={response.status}, body={result_text}")
                    
                    if response.status == 200:
                        # Check if response contains success indicator
                        result_lower = result_text.lower()
                        success_indicators = ["ok", "success", "open", "abierta", "abierto", "puerta abierta"]
                        if any(indicator in result_lower for indicator in success_indicators):
                            _LOGGER.info(f"Door opened successfully: {result_text}")
                            return True
                        else:
                            _LOGGER.warning(f"Door command sent but unclear response: {result_text}")
                            # Still return True if we got 200 status but log the unusual response
                            return True
                    elif response.status == 401:
                        _LOGGER.warning("Authentication expired during door open, refreshing...")
                        if await self.refresh_auth():
                            return await self.open_door(device_id, access_id)
                        else:
                            _LOGGER.error("Failed to refresh authentication for door open")
                            raise FermaxBlueAuthError("Authentication failed")
                    else:
                        _LOGGER.error(f"Failed to open door: HTTP {response.status}: {result_text}")
                        raise FermaxBlueAPIError(f"Door open failed with status {response.status}: {result_text}")
                        
        except asyncio.TimeoutError:
            _LOGGER.error(f"Door open timeout after {DEFAULT_TIMEOUT} seconds")
            raise FermaxBlueConnectionError(ERROR_TIMEOUT)
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Network error during door open: {err}")
            raise FermaxBlueConnectionError(f"{ERROR_CANNOT_CONNECT}: {err}")
        except FermaxBlueAPIError:
            raise
        except Exception as err:
            _LOGGER.error(f"Unexpected error during door open: {type(err).__name__}: {err}")
            raise FermaxBlueAPIError(f"{ERROR_UNKNOWN}: {err}")

    async def test_connection(self) -> bool:
        """Test connection to Fermax Blue API."""
        try:
            _LOGGER.info(f"Testing connection for user: {self.username}")
            await self.authenticate()
            _LOGGER.info("Authentication successful, getting pairings...")
            await self.get_pairings()
            _LOGGER.info(f"Connection test successful, found {len(self.pairings)} pairings")
            return True
        except Exception as err:
            _LOGGER.error(f"Connection test failed: {err}")
            _LOGGER.exception("Full traceback:")
            return False

    def get_home_info(self) -> Dict[str, Any]:
        """Get home information from pairings."""
        if not self.pairings:
            return {
                "id": "unknown",
                "name": "Fermax Blue Home",
                "address": "",
            }

        # Get info from first pairing
        first_pairing = self.pairings[0]
        return {
            "id": first_pairing.get("id", "unknown"),
            "name": first_pairing.get("home", "Fermax Blue Home"),
            "address": first_pairing.get("address", ""),
        }

    def get_door_devices(self) -> List[Dict[str, Any]]:
        """Get door devices from pairings."""
        doors = []
        
        for pairing in self.pairings:
            device_id = pairing.get("deviceId")
            access_door_map = pairing.get("accessDoorMap", {})
            
            # Each access door in the map is a door we can control
            for door_key, door_data in access_door_map.items():
                if door_data.get("visible", True):
                    access_id_data = door_data.get("accessId", {})
                    access_id = AccessId(
                        block=access_id_data.get("block", 0),
                        subblock=access_id_data.get("subblock", 0),
                        number=access_id_data.get("number", 0)
                    )
                    
                    doors.append({
                        "id": f"{device_id}_{door_key}",
                        "name": door_data.get("title", f"Door {door_key}"),
                        "device_id": device_id,
                        "access_id": access_id,
                        "pairing_tag": pairing.get("tag", ""),
                        "home": pairing.get("home", ""),
                    })
        
        return doors