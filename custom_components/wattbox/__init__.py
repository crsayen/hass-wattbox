"""
Component to integrate with wattbox.

For more details about this component, please refer to
https://github.com/bballdavis/hass-wattbox/
"""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .pywattbox_api_v2_4 import WattBoxClient, WattBoxConnectionError, WattBoxError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: List[str] = ["sensor", "switch", "binary_sensor"]


class WattBoxUpdateCoordinator(DataUpdateCoordinator):
    """WattBox data update coordinator."""

    def __init__(self, hass: HomeAssistant, client: WattBoxClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self.device_info = None

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from WattBox."""
        try:
            # Run the blocking calls in the executor
            device_info = await self.hass.async_add_executor_job(
                self.client.get_device_info, True  # Force refresh
            )
            
            return {
                "device_info": device_info,
                "outlets": device_info.outlets,
                "system_info": device_info.system_info,
                "power_status": device_info.power_status,
                "ups_status": device_info.ups_status,
                "ups_connected": device_info.ups_connected,
                "auto_reboot_enabled": device_info.auto_reboot_enabled,
            }
            
        except WattBoxConnectionError as err:
            raise UpdateFailed(f"Error communicating with WattBox: {err}")
        except WattBoxError as err:
            raise UpdateFailed(f"Error updating WattBox data: {err}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WattBox from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 23)
    username = entry.data.get(CONF_USERNAME, "wattbox")
    password = entry.data.get(CONF_PASSWORD, "wattbox")

    # Create the client
    client = WattBoxClient(
        host=host,
        port=port,
        username=username,
        password=password,
        timeout=10.0
    )

    # Test the connection
    try:
        await hass.async_add_executor_job(client.connect)
        await hass.async_add_executor_job(client.ping)
        await hass.async_add_executor_job(client.disconnect)
    except WattBoxError as err:
        _LOGGER.error("Failed to connect to WattBox at %s: %s", host, err)
        raise ConfigEntryNotReady from err

    # Create the coordinator
    coordinator = WattBoxUpdateCoordinator(hass, client)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Disconnect the client
        try:
            await hass.async_add_executor_job(coordinator.client.disconnect)
        except Exception as err:
            _LOGGER.debug("Error disconnecting from WattBox: %s", err)

    return unload_ok
