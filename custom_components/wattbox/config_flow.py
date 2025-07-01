"""Config flow for WattBox integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DEFAULT_NAME, DEFAULT_PASSWORD, DEFAULT_PORT, DEFAULT_USER
from pywattbox_api_v2_4 import WattBoxClient
from pywattbox_api_v2_4.exceptions import (
    WattBoxConnectionError,
    WattBoxAuthenticationError,
    WattBoxError,
)

_LOGGER = logging.getLogger(__name__)

# Data schema for user input
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USER): cv.string,
        vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Create client with provided credentials
    client = WattBoxClient(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        timeout=10.0,
    )

    try:
        # Test connection and get device info
        await hass.async_add_executor_job(client.connect)
        
        # Get device information for validation and unique ID
        system_info = await hass.async_add_executor_job(client.get_system_info)
        
        # Disconnect after testing
        await hass.async_add_executor_job(client.disconnect)
        
        # Return info that you want to store in the config entry.
        return {
            "title": f"WattBox {system_info.model}",
            "model": system_info.model,
            "firmware": system_info.firmware,
            "hostname": system_info.hostname,
            "service_tag": system_info.service_tag,
            "outlet_count": system_info.outlet_count,
        }
        
    except WattBoxConnectionError as err:
        _LOGGER.error("Connection error: %s", err)
        raise CannotConnect from err
    except WattBoxAuthenticationError as err:
        _LOGGER.error("Authentication error: %s", err)
        raise InvalidAuth from err
    except WattBoxError as err:
        _LOGGER.error("WattBox error: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error: %s", err)
        raise CannotConnect from err
    finally:
        # Ensure client is disconnected
        try:
            await hass.async_add_executor_job(client.disconnect)
        except Exception:
            pass


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WattBox."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured (by service tag)
                await self.async_set_unique_id(info["service_tag"])
                self._abort_if_unique_id_configured()
                
                # Create the config entry
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                    description_placeholders={
                        "model": info["model"],
                        "firmware": info["firmware"],
                        "hostname": info["hostname"],
                        "outlet_count": str(info["outlet_count"]),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "default_username": DEFAULT_USER,
                "default_password": DEFAULT_PASSWORD,
                "default_port": str(DEFAULT_PORT),
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of an existing entry."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors = {"base": "cannot_connect"}
            except InvalidAuth:
                errors = {"base": "invalid_auth"}
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors = {"base": "unknown"}
            else:
                # Update the config entry
                return self.async_update_reload_and_abort(
                    entry, data=user_input, reason="reconfigure_successful"
                )
        else:
            # Pre-fill with existing data
            user_input = entry.data
            errors = {}

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=user_input.get(CONF_HOST)): cv.string,
                    vol.Optional(CONF_PORT, default=user_input.get(CONF_PORT, DEFAULT_PORT)): cv.port,
                    vol.Optional(CONF_USERNAME, default=user_input.get(CONF_USERNAME, DEFAULT_USER)): cv.string,
                    vol.Optional(CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, DEFAULT_PASSWORD)): cv.string,
                    vol.Optional(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)): cv.string,
                }
            ),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
