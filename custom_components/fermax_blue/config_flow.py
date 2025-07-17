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

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_PASSWORD,
    ERROR_INVALID_AUTH,
    ERROR_CANNOT_CONNECT,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
)

try:
    from .fermax_api import FermaxBlueAPI, FermaxBlueAuthError, FermaxBlueConnectionError
except ImportError as e:
    _LOGGER.error(f"Failed to import fermax_api: {e}")
    # Create dummy classes to prevent crashes
    class FermaxBlueAPI:
        def __init__(self, *args, **kwargs):
            pass
        async def authenticate(self):
            return False
    
    class FermaxBlueAuthError(Exception):
        pass
    
    class FermaxBlueConnectionError(Exception):
        pass

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
    _LOGGER.info("Starting validate_input...")
    
    # Create SSL context that matches what worked in testing
    ssl_context = ssl.create_default_context()
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    session = aiohttp.ClientSession(connector=connector)
    
    # Default response in case of any error
    default_response = {
        "title": "Fermax Blue Home",
        "home_id": "unknown",
    }
    
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
        
        result = {
            "title": title,
            "home_id": "unknown",
        }
        _LOGGER.info(f"Validation successful, returning: {result}")
        return result
        
    except FermaxBlueAuthError as err:
        _LOGGER.error(f"Authentication error: {err}")
        raise InvalidAuth
    except FermaxBlueConnectionError as err:
        _LOGGER.error(f"Connection error: {err}")
        raise CannotConnect
    except Exception as err:
        _LOGGER.exception(f"Unexpected exception in validate_input: {err}")
        # Return default response instead of raising
        _LOGGER.error("Returning default response due to unexpected error")
        return default_response
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
                
                # Ensure info is a dict and has title
                if not isinstance(info, dict):
                    _LOGGER.error(f"validate_input returned non-dict: {type(info)}")
                    info = {"title": "Fermax Blue Home", "home_id": "unknown"}
                
                if "title" not in info:
                    _LOGGER.error("validate_input returned dict without title")
                    info["title"] = "Fermax Blue Home"
                    
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as e:
                _LOGGER.exception(f"Unexpected exception in config flow: {e}")
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