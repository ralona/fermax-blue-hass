"""Fermax Blue API client."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout

from .const import (
    AUTH_URL,
    USER_INFO_URL,
    DEVICES_URL,
    PAIRINGS_URL,
    OPEN_DOOR_URL,
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


class FermaxBlueAPI:
    """Fermax Blue API client."""

    def __init__(self, email: str, password: str, session: aiohttp.ClientSession):
        """Initialize the API client."""
        self.email = email
        self.password = password
        self.session = session
        self.access_token: Optional[str] = None
        self.devices: List[Dict[str, Any]] = []

    async def authenticate(self) -> bool:
        """Authenticate with Fermax Blue API."""
        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                # Use username/password format as per Fermax Blue API
                auth_data = {
                    "username": self.email,
                    "password": self.password
                }
                
                async with self.session.post(
                    AUTH_URL,
                    json=auth_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Fermax Blue returns token in different possible formats
                        self.access_token = data.get("token") or data.get("access_token") or data.get("auth_token")
                        if self.access_token:
                            _LOGGER.debug("Authentication successful")
                            return True
                        else:
                            raise FermaxBlueAuthError("No token received from API")
                    elif response.status == 401:
                        raise FermaxBlueAuthError(ERROR_INVALID_AUTH)
                    else:
                        error_text = await response.text()
                        raise FermaxBlueConnectionError(f"HTTP {response.status}: {error_text}")
        except asyncio.TimeoutError:
            raise FermaxBlueConnectionError(ERROR_TIMEOUT)
        except aiohttp.ClientError as err:
            raise FermaxBlueConnectionError(f"{ERROR_CANNOT_CONNECT}: {err}")
        except Exception as err:
            raise FermaxBlueAPIError(f"{ERROR_UNKNOWN}: {err}")

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of devices from Fermax Blue API."""
        if not self.access_token:
            await self.authenticate()

        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                headers = {"Authorization": f"Bearer {self.access_token}"}
                
                # Try to get pairings first (devices you can control)
                async with self.session.get(PAIRINGS_URL, headers=headers) as response:
                    if response.status == 200:
                        pairings_data = await response.json()
                        # Extract pairings which contain door access information
                        pairings = pairings_data.get("pairings", [])
                        
                        # Also get general device info
                        async with self.session.get(DEVICES_URL, headers=headers) as dev_response:
                            if dev_response.status == 200:
                                devices_data = await dev_response.json()
                                devices = devices_data.get("devices", [])
                                
                                # Combine pairings and devices data
                                self.devices = self._combine_device_data(pairings, devices)
                                _LOGGER.debug(f"Found {len(self.devices)} devices")
                                return self.devices
                            else:
                                # Fallback to just pairings
                                self.devices = pairings
                                _LOGGER.debug(f"Found {len(self.devices)} devices (pairings only)")
                                return self.devices
                    elif response.status == 401:
                        # Token expired, try to re-authenticate
                        await self.authenticate()
                        return await self.get_devices()
                    else:
                        error_text = await response.text()
                        raise FermaxBlueConnectionError(f"HTTP {response.status}: {error_text}")
        except asyncio.TimeoutError:
            raise FermaxBlueConnectionError(ERROR_TIMEOUT)
        except aiohttp.ClientError as err:
            raise FermaxBlueConnectionError(f"{ERROR_CANNOT_CONNECT}: {err}")
        except Exception as err:
            raise FermaxBlueAPIError(f"{ERROR_UNKNOWN}: {err}")

    def _combine_device_data(self, pairings: List[Dict[str, Any]], devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine pairings and device data."""
        combined = []
        
        for pairing in pairings:
            # Each pairing represents a door/access point
            device_info = {
                "id": pairing.get("id"),
                "name": pairing.get("name", "Door"),
                "type": "door",
                "device_id": pairing.get("deviceId"),
                "access_id": pairing.get("accessId", {}),
                "location": pairing.get("location", ""),
                "home_id": pairing.get("homeId"),
                "home_name": pairing.get("homeName", "Home"),
            }
            combined.append(device_info)
        
        return combined

    async def open_door(self, device_id: str, access_id: Dict[str, Any]) -> bool:
        """Open a door using device ID and access ID."""
        if not self.access_token:
            await self.authenticate()

        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                # Format payload as expected by Fermax Blue API
                payload = {
                    "deviceId": device_id,
                    "accessId": access_id,
                }
                
                _LOGGER.debug(f"Opening door with deviceId: {device_id}, accessId: {access_id}")
                
                async with self.session.post(
                    OPEN_DOOR_URL, headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        _LOGGER.info(f"Door opened successfully for device {device_id}")
                        return True
                    elif response.status == 401:
                        # Token expired, try to re-authenticate
                        _LOGGER.debug("Token expired, re-authenticating")
                        await self.authenticate()
                        return await self.open_door(device_id, access_id)
                    else:
                        error_text = await response.text()
                        _LOGGER.error(f"Failed to open door: HTTP {response.status}: {error_text}")
                        return False
        except asyncio.TimeoutError:
            raise FermaxBlueConnectionError(ERROR_TIMEOUT)
        except aiohttp.ClientError as err:
            raise FermaxBlueConnectionError(f"{ERROR_CANNOT_CONNECT}: {err}")
        except Exception as err:
            raise FermaxBlueAPIError(f"{ERROR_UNKNOWN}: {err}")

    async def test_connection(self) -> bool:
        """Test connection to Fermax Blue API."""
        try:
            await self.authenticate()
            await self.get_devices()
            return True
        except Exception as err:
            _LOGGER.error(f"Connection test failed: {err}")
            return False

    def get_home_info(self) -> Dict[str, Any]:
        """Get home information from devices."""
        if not self.devices:
            return {
                "id": "unknown",
                "name": "Fermax Blue Home",
                "address": "",
            }

        # Extract home information from first device
        first_device = self.devices[0]
        return {
            "id": first_device.get("home_id", "unknown"),
            "name": first_device.get("home_name", "Fermax Blue Home"),
            "address": first_device.get("address", ""),
        }

    def get_door_devices(self) -> List[Dict[str, Any]]:
        """Get door devices from the device list."""
        doors = []
        for device in self.devices:
            # All devices in our list should be doors/access points
            if device.get("type") == "door":
                doors.append({
                    "id": device.get("id"),
                    "name": device.get("name", f"Door {device.get('id')}"),
                    "device_id": device.get("device_id"),
                    "access_id": device.get("access_id", {}),
                    "location": device.get("location", ""),
                })
        return doors