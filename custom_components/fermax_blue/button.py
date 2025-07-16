"""Button platform for Fermax Blue integration."""
import logging
from typing import Any, Dict

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, ENTITY_OPEN_DOOR
from .fermax_api import FermaxBlueAPI, FermaxBlueAPIError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fermax Blue button entities based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    api: FermaxBlueAPI = coordinator.api
    
    entities = []
    
    # Get door devices and create button entities
    door_devices = api.get_door_devices()
    home_info = api.get_home_info()
    
    for door in door_devices:
        entities.append(
            FermaxBlueDoorButton(
                api=api,
                door_data=door,
                home_info=home_info,
                config_entry=config_entry,
            )
        )
    
    async_add_entities(entities)


class FermaxBlueDoorButton(ButtonEntity):
    """Fermax Blue door button entity."""

    def __init__(
        self,
        api: FermaxBlueAPI,
        door_data: Dict[str, Any],
        home_info: Dict[str, Any],
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button entity."""
        self._api = api
        self._door_data = door_data
        self._home_info = home_info
        self._config_entry = config_entry
        
        # Entity attributes
        self._attr_name = f"{door_data['name']} {ENTITY_OPEN_DOOR}"
        self._attr_unique_id = f"{config_entry.entry_id}_{door_data['id']}_open"
        self._attr_icon = "mdi:door-open"
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, door_data["id"])},
            name=door_data["name"],
            manufacturer="Fermax",
            model="Blue Intercom Door",
            via_device=(DOMAIN, home_info.get("id", "unknown")),
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            success = await self._api.open_door(
                device_id=self._door_data["device_id"],
                access_id=self._door_data["access_id"],
            )
            
            if success:
                _LOGGER.info(f"Door {self._door_data['name']} opened successfully")
            else:
                _LOGGER.error(f"Failed to open door {self._door_data['name']}")
                raise HomeAssistantError(f"Failed to open door {self._door_data['name']}")
                
        except FermaxBlueAPIError as err:
            _LOGGER.error(f"API error opening door {self._door_data['name']}: {err}")
            raise HomeAssistantError(f"API error: {err}")
        except Exception as err:
            _LOGGER.error(f"Unexpected error opening door {self._door_data['name']}: {err}")
            raise HomeAssistantError(f"Unexpected error: {err}")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._api.access_token is not None