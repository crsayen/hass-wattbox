"""
Component to integrate with wattbox.

For more details about this component, please refer to
https://github.com/bballdavis/hass-wattbox/
"""
import asyncio
import logging
import time
from datetime import timedelta
from typing import Any, Dict, List, Optional

from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME  # type: ignore
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.exceptions import ConfigEntryNotReady  # type: ignore
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed  # type: ignore

from .const import DOMAIN

# Import API library components directly
from .pywattbox_api_v2_4.client import WattBoxClient
from .pywattbox_api_v2_4.exceptions import WattBoxConnectionError, WattBoxError

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
        # Cache for outlet power info to avoid excessive API calls
        self._power_cache = {}
        self._power_cache_expire = 10  # Cache for 10 seconds

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from WattBox."""
        try:
            _LOGGER.debug("Fetching device info from WattBox")
            # Run the blocking calls in the executor
            device_info = await self.hass.async_add_executor_job(
                self.client.get_device_info, True  # Force refresh
            )
            
            outlet_count = len(device_info.outlets) if device_info.outlets else 0
            _LOGGER.info(f"Successfully updated WattBox data: {outlet_count} outlets, power_status: {device_info.power_status is not None}")
            
            return {
                "device_info": device_info,
                "outlets": device_info.outlets,
                "system_info": device_info.system_info,
                "power_status": device_info.power_status,
                "ups_status": device_info.ups_status,
                "ups_connected": device_info.ups_connected,
                "auto_reboot_enabled": device_info.auto_reboot_enabled,
            }
        except Exception as err:
            # Catch all other errors
            _LOGGER.error(f"Unexpected error updating WattBox data: {err}")
            raise UpdateFailed(f"Unexpected error updating WattBox data: {err}")

    def get_master_switch_state(self) -> Optional[bool]:
        """Get the current state of the master switch based on outlet states."""
        if not self.data or not self.data.get("outlets"):
            return None
            
        # Return True if any outlet is on
        for outlet in self.data["outlets"]:
            if outlet.status:
                return True
        return False
    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WattBox from a config entry."""
    _LOGGER.info("=== WattBox Integration: Starting setup ===")
    
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, 23)
    username = entry.data.get(CONF_USERNAME, "wattbox")
    password = entry.data.get(CONF_PASSWORD, "wattbox")

    _LOGGER.info(f"WattBox Integration: Connecting to {host}:{port}")

    # Create the client
    client = WattBoxClient(
        host=host,
        port=port,
        username=username,
        password=password,
        timeout=10.0
    )

    # Create the coordinator
    coordinator = WattBoxUpdateCoordinator(hass, client)

    # Fetch initial data
    _LOGGER.info("Fetching initial device data from WattBox")
    await coordinator.async_config_entry_first_refresh()
    
    # Log some basic info about the device
    if coordinator.data and coordinator.data.get("system_info"):
        system_info = coordinator.data["system_info"]
        outlet_count = len(coordinator.data.get("outlets", []))
        _LOGGER.info("WattBox device initialized: Model=%s, Firmware=%s, Outlets=%d", 
                    system_info.model, system_info.firmware, outlet_count)

    # Store the coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok
