"""The Fermax Blue integration."""
import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .fermax_api import FermaxBlueAPI, FermaxBlueAPIError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fermax Blue from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create API instance
    session = async_get_clientsession(hass)
    api = FermaxBlueAPI(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )
    
    # Create coordinator
    coordinator = FermaxBlueCoordinator(hass, api)
    
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

    def __init__(self, hass: HomeAssistant, api: FermaxBlueAPI) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=30),
        )
        self.api = api
        self._home_device_info: DeviceInfo | None = None

    async def _async_update_data(self):
        """Update data via library."""
        try:
            await self.api.get_devices()
            return self.api.devices
        except FermaxBlueAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    @property
    def home_device_info(self) -> DeviceInfo:
        """Return home device info."""
        if self._home_device_info is None:
            home_info = self.api.get_home_info()
            self._home_device_info = DeviceInfo(
                identifiers={(DOMAIN, home_info.get("id", "unknown"))},
                name=home_info.get("name", "Fermax Blue Home"),
                manufacturer="Fermax",
                model="Blue Intercom System",
                sw_version="1.0",
            )
        return self._home_device_info