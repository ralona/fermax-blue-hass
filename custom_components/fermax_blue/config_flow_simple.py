"""Simple config flow for Fermax Blue integration."""
import logging
import ssl
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import aiohttp

_LOGGER = logging.getLogger(__name__)

DOMAIN = "fermax_blue"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fermax Blue."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Simple validation - just check if email and password are provided
                if not user_input.get(CONF_EMAIL) or not user_input.get(CONF_PASSWORD):
                    errors["base"] = "invalid_auth"
                else:
                    # Create a unique ID based on email
                    await self.async_set_unique_id(user_input[CONF_EMAIL])
                    self._abort_if_unique_id_configured()
                    
                    # Always create entry with fixed title
                    return self.async_create_entry(
                        title="Fermax Blue Home",
                        data=user_input,
                    )
            except Exception as e:
                _LOGGER.exception(f"Error in config flow: {e}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""