"""Config flow for Fermax Blue integration."""
import logging
import ssl
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import aiohttp

from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_PASSWORD,
    ERROR_INVALID_AUTH,
    ERROR_CANNOT_CONNECT,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)
from .fermax_api import FermaxBlueAPI, FermaxBlueAuthError, FermaxBlueConnectionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Create SSL context that matches what worked in testing
    ssl_context = ssl.create_default_context()
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    session = aiohttp.ClientSession(connector=connector)
    try:
        api = FermaxBlueAPI(data[CONF_EMAIL], data[CONF_PASSWORD], session)
        
        # First try authentication only
        _LOGGER.info("Starting authentication test...")
        auth_result = await api.authenticate()
        if not auth_result:
            _LOGGER.error("Authentication failed")
            raise InvalidAuth
        
        _LOGGER.info("Authentication successful, testing pairings...")
        
        # If auth works, try to get pairings
        try:
            await api.get_pairings()
            home_info = api.get_home_info()
            title = home_info.get("name", "Fermax Blue Home")
        except Exception as e:
            _LOGGER.warning(f"Could not get pairings, using default title: {e}")
            title = "Fermax Blue Home"
        
        return {
            "title": title,
            "home_id": "unknown",
        }
    except FermaxBlueAuthError as err:
        _LOGGER.error(f"Authentication error: {err}")
        raise InvalidAuth
    except FermaxBlueConnectionError as err:
        _LOGGER.error(f"Connection error: {err}")
        raise CannotConnect
    except Exception as err:
        _LOGGER.exception(f"Unexpected exception: {err}")
        raise CannotConnect
    finally:
        await session.close()


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
                info = await validate_input(self.hass, user_input)
                _LOGGER.debug(f"Validation successful, info: {info}")
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on email
                await self.async_set_unique_id(user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()
                
                # Ensure we have a title
                title = info.get("title", "Fermax Blue Home")
                _LOGGER.debug(f"Creating entry with title: {title}")
                
                return self.async_create_entry(
                    title=title,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""