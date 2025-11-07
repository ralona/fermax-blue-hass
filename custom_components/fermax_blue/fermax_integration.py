"""Fermax Blue integration logic - independent of Home Assistant."""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import aiohttp

_LOGGER = logging.getLogger(__name__)

# API endpoints - Updated to new Fermax DuoxMe infrastructure (2025)
OAUTH_URL = "https://oauth-pro-duoxme.fermax.io/oauth/token"
BASE_URL = "https://pro-duoxme.fermax.io"
PAIRINGS_URL = f"{BASE_URL}/pairing/api/v3/pairings/me"
OPEN_DOOR_URL = f"{BASE_URL}/deviceaction/api/v1/device"
OAUTH_CLIENT_AUTH = "Basic ZHB2N2lxejZlZTVtYXptMWlxOWR3MWQ0MnNseXV0NDhrajBtcDVmdm81OGo1aWg6Yzd5bGtxcHVqd2FoODV5aG5wcnYwd2R2eXp1dGxjbmt3NHN6OTBidWxkYnVsazE="

# Headers
APP_VERSION = "3.2.1"
APP_BUILD = "3"
PHONE_OS = "16.4"
PHONE_MODEL = "iPad14,5"
USER_AGENT = f"Blue/{APP_VERSION} (com.fermax.bluefermax; build:{APP_BUILD}; iOS {PHONE_OS}) Alamofire/{APP_VERSION}"

DEFAULT_TIMEOUT = 30


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


class FermaxBlueIntegration:
    """Main integration class - can be tested independently."""

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession):
        """Initialize the integration."""
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
        # Refresh 5 minutes before expiration
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
            
            timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            data = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            }
            
            async with self.session.post(
                OAUTH_URL,
                headers=self._get_auth_headers(),
                data=data,
                timeout=timeout
            ) as response:
                if response.status == 200:
                    oauth_data = await response.json()
                    self.access_token = oauth_data.get("access_token")
                    self.refresh_token = oauth_data.get("refresh_token")
                    expires_in = oauth_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
                    _LOGGER.info(f"Authentication successful, token expires in {expires_in} seconds")
                    return True
                else:
                    error_text = await response.text()
                    _LOGGER.error(f"Authentication failed: {response.status} - {error_text}")
                    return False
                    
        except Exception as err:
            _LOGGER.error(f"Authentication error: {err}")
            return False

    async def get_pairings(self) -> List[Dict[str, Any]]:
        """Get list of paired devices."""
        if not self.access_token or self._needs_refresh():
            if not await self.authenticate():
                _LOGGER.error("Failed to authenticate for getting pairings")
                return []
            
        try:
            timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            async with self.session.get(
                PAIRINGS_URL,
                headers=self._get_api_headers(),
                timeout=timeout
            ) as response:
                if response.status == 200:
                    self.pairings = await response.json()
                    _LOGGER.debug(f"Found {len(self.pairings)} pairings")
                    return self.pairings
                elif response.status == 401:
                    _LOGGER.warning("Token expired, re-authenticating...")
                    if await self.authenticate():
                        return await self.get_pairings()
                    else:
                        _LOGGER.error("Re-authentication failed")
                        return []
                else:
                    error_text = await response.text()
                    _LOGGER.error(f"Failed to get pairings: {response.status} - {error_text}")
                    return []
                    
        except Exception as err:
            _LOGGER.error(f"Error getting pairings: {err}")
            return []

    async def open_door(self, device_id: str, access_id: AccessId) -> bool:
        """Open a door."""
        if not self.access_token or self._needs_refresh():
            if not await self.authenticate():
                _LOGGER.error("Failed to authenticate for door open")
                return False
            
        try:
            url = f"{OPEN_DOOR_URL}/{device_id}/directed-opendoor"
            data = json.dumps(access_id.to_dict())
            
            timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            async with self.session.post(
                url,
                headers=self._get_api_headers(),
                data=data,
                timeout=timeout
            ) as response:
                result_text = await response.text()
                _LOGGER.debug(f"Door open response: status={response.status}, body={result_text}")
                
                if response.status == 200:
                    # Check if response contains success indicator
                    result_lower = result_text.lower()
                    success_indicators = ["ok", "success", "open", "abierta", "abierto", "puerta abierta"]
                    error_indicators = ["ko", "error", "fail", "cerrada", "bloqueada"]
                    
                    if any(indicator in result_lower for indicator in success_indicators):
                        _LOGGER.info(f"Door opened successfully: {result_text}")
                        return True
                    elif any(indicator in result_lower for indicator in error_indicators):
                        _LOGGER.error(f"Door open failed per response: {result_text}")
                        return False
                    else:
                        _LOGGER.warning(f"Unclear door response, assuming success: {result_text}")
                        return True
                elif response.status == 401:
                    _LOGGER.warning("Token expired during door open, re-authenticating...")
                    if await self.authenticate():
                        return await self.open_door(device_id, access_id)
                    else:
                        _LOGGER.error("Re-authentication failed for door open")
                        return False
                else:
                    _LOGGER.error(f"Failed to open door: {response.status} - {result_text}")
                    return False
                    
        except Exception as err:
            _LOGGER.error(f"Error opening door: {err}")
            return False

    def get_home_info(self) -> Dict[str, Any]:
        """Get home information."""
        if not self.pairings:
            return {
                "id": "unknown",
                "name": "Fermax Blue Home",
                "address": "",
            }

        first_pairing = self.pairings[0]
        return {
            "id": first_pairing.get("id", "unknown"),
            "name": first_pairing.get("home", "Fermax Blue Home"),
            "address": first_pairing.get("address", ""),
        }

    def get_door_devices(self) -> List[Dict[str, Any]]:
        """Get door devices."""
        doors = []
        
        for pairing in self.pairings:
            device_id = pairing.get("deviceId")
            access_door_map = pairing.get("accessDoorMap", {})
            device_name = pairing.get("tag", "Telefonillo")  # Nombre del dispositivo/telefonillo
            
            for door_key, door_data in access_door_map.items():
                if door_data.get("visible", True):
                    access_id_data = door_data.get("accessId", {})
                    access_id = AccessId(
                        block=access_id_data.get("block", 0),
                        subblock=access_id_data.get("subblock", 0),
                        number=access_id_data.get("number", 0)
                    )
                    
                    door_name = door_data.get("title", f"Door {door_key}")
                    # Combinar nombre del dispositivo + nombre de la puerta
                    full_name = f"{device_name} {door_name}"
                    
                    doors.append({
                        "id": f"{device_id}_{door_key}",
                        "name": full_name,
                        "device_id": device_id,
                        "access_id": access_id,
                        "pairing_tag": pairing.get("tag", ""),
                        "home": pairing.get("home", ""),
                        "device_name": device_name,
                        "door_name": door_name,
                    })
        
        return doors

    async def setup_integration(self) -> bool:
        """Setup the integration - like __init__.py does."""
        try:
            _LOGGER.info("Setting up Fermax Blue integration...")
            
            # Authenticate
            if not await self.authenticate():
                _LOGGER.error("Authentication failed during setup")
                return False
                
            # Get pairings (like coordinator first refresh)
            await self.get_pairings()
            
            # Get home info
            home_info = self.get_home_info()
            _LOGGER.info(f"Home: {home_info}")
            
            # Get doors
            doors = self.get_door_devices()
            _LOGGER.info(f"Found {len(doors)} doors")
            
            for door in doors:
                _LOGGER.info(f"  - {door['name']} (ID: {door['id']})")
            
            _LOGGER.info("Integration setup completed successfully")
            return True
            
        except Exception as err:
            _LOGGER.error(f"Integration setup failed: {err}")
            return False

    async def update_data(self) -> bool:
        """Update data - like coordinator does."""
        try:
            await self.get_pairings()
            return True
        except Exception as err:
            _LOGGER.error(f"Update failed: {err}")
            return False