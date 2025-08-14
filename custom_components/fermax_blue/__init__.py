"""The Fermax Blue integration."""
import asyncio
import logging
from datetime import timedelta, datetime, timezone
import json
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.storage import Store

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .fermax_integration import FermaxBlueIntegration

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fermax Blue from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create integration instance
    session = async_get_clientsession(hass)
    
    integration = FermaxBlueIntegration(
        username=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )
    
    # Create coordinator with storage
    coordinator = FermaxBlueCoordinator(hass, integration, entry.entry_id)
    
    # Load stored tokens before first refresh
    await coordinator.load_tokens()
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


class FermaxBlueCoordinator(DataUpdateCoordinator):
    """Fermax Blue data coordinator."""

    def __init__(self, hass: HomeAssistant, integration: FermaxBlueIntegration, entry_id: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=15),  # Reduced from 30 to 15 minutes
        )
        self.integration = integration
        self._home_device_info: DeviceInfo | None = None
        self.entry_id = entry_id
        self._store = Store(hass, 1, f"{DOMAIN}.{entry_id}.tokens")

    async def load_tokens(self) -> None:
        """Load stored tokens."""
        try:
            data = await self._store.async_load()
            if data:
                self.integration.access_token = data.get("access_token")
                self.integration.refresh_token = data.get("refresh_token")
                
                # Parse token expiration
                expires_at_str = data.get("token_expires_at")
                if expires_at_str:
                    self.integration.token_expires_at = datetime.fromisoformat(expires_at_str)
                    _LOGGER.debug(f"Loaded stored tokens, expires at {self.integration.token_expires_at}")
                    
                    # Check if token is still valid
                    if self.integration._needs_refresh():
                        _LOGGER.info("Stored token expired or expiring soon, will refresh")
                else:
                    _LOGGER.debug("No token expiration in stored data")
        except Exception as err:
            _LOGGER.error(f"Error loading stored tokens: {err}")

    async def save_tokens(self) -> None:
        """Save tokens to storage."""
        try:
            data = {
                "access_token": self.integration.access_token,
                "refresh_token": self.integration.refresh_token,
                "token_expires_at": self.integration.token_expires_at.isoformat() if self.integration.token_expires_at else None,
            }
            await self._store.async_save(data)
            _LOGGER.debug("Tokens saved to storage")
        except Exception as err:
            _LOGGER.error(f"Error saving tokens: {err}")

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Ensure authentication is current before updating
            if self.integration._needs_refresh():
                _LOGGER.info("Token needs refresh during coordinator update")
                if not await self.integration.authenticate():
                    raise UpdateFailed("Failed to authenticate")
                # Save new tokens after successful auth
                await self.save_tokens()
            
            # Update pairings data
            await self.integration.update_data()
            
            # Save tokens after successful update (in case they were refreshed)
            await self.save_tokens()
            
            return self.integration.pairings
        except Exception as err:
            _LOGGER.error(f"Coordinator update error: {err}")
            raise UpdateFailed(f"Error communicating with API: {err}")

    @property
    def home_device_info(self) -> DeviceInfo:
        """Return home device info."""
        if self._home_device_info is None:
            home_info = self.integration.get_home_info()
            self._home_device_info = DeviceInfo(
                identifiers={(DOMAIN, home_info.get("id", "unknown"))},
                name=home_info.get("name", "Fermax Blue Home"),
                manufacturer="Fermax",
                model="Blue Intercom System",
                sw_version="1.0",
            )
        return self._home_device_info