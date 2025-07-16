"""Fermax Blue API client."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp
import async_timeout

from .const import (
    AUTH_URL,
    DEVICES_URL,
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
                async with self.session.post(
                    AUTH_URL,
                    json={"email": self.email, "password": self.password},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get("access_token")
                        _LOGGER.debug("Authentication successful")
                        return True
                    elif response.status == 401:
                        raise FermaxBlueAuthError(ERROR_INVALID_AUTH)
                    else:
                        raise FermaxBlueConnectionError(f"HTTP {response.status}")
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
                async with self.session.get(DEVICES_URL, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.devices = data.get("devices", [])
                        _LOGGER.debug(f"Found {len(self.devices)} devices")
                        return self.devices
                    elif response.status == 401:
                        # Token expired, try to re-authenticate
                        await self.authenticate()
                        return await self.get_devices()
                    else:
                        raise FermaxBlueConnectionError(f"HTTP {response.status}")
        except asyncio.TimeoutError:
            raise FermaxBlueConnectionError(ERROR_TIMEOUT)
        except aiohttp.ClientError as err:
            raise FermaxBlueConnectionError(f"{ERROR_CANNOT_CONNECT}: {err}")
        except Exception as err:
            raise FermaxBlueAPIError(f"{ERROR_UNKNOWN}: {err}")

    async def open_door(self, device_id: str, access_id: Dict[str, Any]) -> bool:
        """Open a door using device ID and access ID."""
        if not self.access_token:
            await self.authenticate()

        try:
            async with async_timeout.timeout(DEFAULT_TIMEOUT):
                headers = {"Authorization": f"Bearer {self.access_token}"}
                payload = {
                    "device_id": device_id,
                    "access_id": access_id,
                }
                async with self.session.post(
                    OPEN_DOOR_URL, headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        _LOGGER.info(f"Door opened successfully for device {device_id}")
                        return True
                    elif response.status == 401:
                        # Token expired, try to re-authenticate
                        await self.authenticate()
                        return await self.open_door(device_id, access_id)
                    else:
                        _LOGGER.error(f"Failed to open door: HTTP {response.status}")
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
            return {}

        # Extract home information from first device
        # This is a simplified approach - in reality, you might need to
        # process the device structure differently based on Fermax API response
        if self.devices:
            first_device = self.devices[0]
            return {
                "id": first_device.get("home_id", "unknown"),
                "name": first_device.get("home_name", "Fermax Blue Home"),
                "address": first_device.get("address", ""),
            }
        return {}

    def get_door_devices(self) -> List[Dict[str, Any]]:
        """Get door devices from the device list."""
        doors = []
        for device in self.devices:
            if device.get("type") == "door" or "door" in device.get("name", "").lower():
                doors.append({
                    "id": device.get("id"),
                    "name": device.get("name", f"Door {device.get('id')}"),
                    "device_id": device.get("device_id"),
                    "access_id": device.get("access_id", {}),
                    "location": device.get("location", ""),
                })
        return doors