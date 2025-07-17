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
from .fermax_integration import FermaxBlueIntegration

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fermax Blue button entities based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    integration: FermaxBlueIntegration = coordinator.integration
    
    entities = []
    
    # Get door devices and create button entities
    door_devices = integration.get_door_devices()
    home_info = integration.get_home_info()
    
    for door in door_devices:
        entities.append(
            FermaxBlueDoorButton(
                integration=integration,
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
        integration: FermaxBlueIntegration,
        door_data: Dict[str, Any],
        home_info: Dict[str, Any],
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the button entity."""
        self._integration = integration
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
            # Access ID is already an AccessId object in door_data
            access_id = self._door_data["access_id"]
            
            success = await self._integration.open_door(
                device_id=self._door_data["device_id"],
                access_id=access_id,
            )
            
            if success:
                _LOGGER.info(f"Door {self._door_data['name']} opened successfully")
            else:
                _LOGGER.error(f"Failed to open door {self._door_data['name']}")
                raise HomeAssistantError(f"Failed to open door {self._door_data['name']}")
                
        except Exception as err:
            _LOGGER.error(f"Error opening door {self._door_data['name']}: {err}")
            raise HomeAssistantError(f"Error: {err}")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._integration.access_token is not None