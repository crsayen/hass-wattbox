"""Switch platform for wattbox."""

import logging
from typing import Any, Optional

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WattBox switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Master switch
    entities.append(WattBoxMasterSwitch(coordinator))
    
    # Individual outlet switches
    if coordinator.data and coordinator.data.get("outlets"):
        for outlet in coordinator.data["outlets"]:
            entities.append(WattBoxOutletSwitch(coordinator, outlet.index, outlet.name))
    
    async_add_entities(entities)


class WattBoxBaseSwitch(CoordinatorEntity, SwitchEntity):
    """Base class for WattBox switches."""

    def __init__(self, coordinator, unique_id: str, name: str):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.host}_{unique_id}"
        self._attr_name = f"WattBox {name}"
        self._attr_device_class = SwitchDeviceClass.OUTLET

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.client.host)},
            "name": "WattBox",
            "manufacturer": "SnapAV",
            "model": self.coordinator.data.get("system_info", {}).get("model", "Unknown"),
            "sw_version": self.coordinator.data.get("system_info", {}).get("firmware", "Unknown"),
        }


class WattBoxOutletSwitch(WattBoxBaseSwitch):
    """WattBox outlet switch."""

    def __init__(self, coordinator, outlet_index: int, outlet_name: str):
        """Initialize the outlet switch."""
        self._outlet_index = outlet_index
        self._outlet_name = outlet_name
        super().__init__(coordinator, f"outlet_{outlet_index}", outlet_name)

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if outlet is on."""
        if not self.coordinator.data or not self.coordinator.data.get("outlets"):
            return None
            
        for outlet in self.coordinator.data["outlets"]:
            if outlet.index == self._outlet_index:
                return outlet.status
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("outlets"):
            return {}
            
        for outlet in self.coordinator.data["outlets"]:
            if outlet.index == self._outlet_index:
                attrs = {
                    "outlet_index": outlet.index,
                    "outlet_name": outlet.name,
                }
                if outlet.power_watts is not None:
                    attrs["power_watts"] = outlet.power_watts
                if outlet.current_amps is not None:
                    attrs["current_amps"] = outlet.current_amps
                if outlet.voltage_volts is not None:
                    attrs["voltage_volts"] = outlet.voltage_volts
                return attrs
        return {}

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the outlet on."""
        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.client.turn_on_outlet, self._outlet_index
            )
            if success:
                _LOGGER.debug("Successfully turned on outlet %s", self._outlet_index)
                # Refresh data after successful action
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to turn on outlet %s", self._outlet_index)
        except Exception as err:
            _LOGGER.error("Error turning on outlet %s: %s", self._outlet_index, err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the outlet off."""
        try:
            success = await self.hass.async_add_executor_job(
                self.coordinator.client.turn_off_outlet, self._outlet_index
            )
            if success:
                _LOGGER.debug("Successfully turned off outlet %s", self._outlet_index)
                # Refresh data after successful action
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to turn off outlet %s", self._outlet_index)
        except Exception as err:
            _LOGGER.error("Error turning off outlet %s: %s", self._outlet_index, err)


class WattBoxMasterSwitch(WattBoxBaseSwitch):
    """WattBox master switch (controls all outlets)."""

    def __init__(self, coordinator):
        """Initialize the master switch."""
        super().__init__(coordinator, "master", "Master Switch")

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if any outlet is on."""
        if not self.coordinator.data or not self.coordinator.data.get("outlets"):
            return None
            
        # Return True if any outlet is on
        for outlet in self.coordinator.data["outlets"]:
            if outlet.status:
                return True
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data or not self.coordinator.data.get("outlets"):
            return {}
            
        total_outlets = len(self.coordinator.data["outlets"])
        on_outlets = sum(1 for outlet in self.coordinator.data["outlets"] if outlet.status)
        
        return {
            "total_outlets": total_outlets,
            "outlets_on": on_outlets,
            "outlets_off": total_outlets - on_outlets,
        }

    async def async_turn_on(self, **kwargs) -> None:
        """Turn all outlets on."""
        try:
            # Turn on all outlets individually
            if self.coordinator.data and self.coordinator.data.get("outlets"):
                for outlet in self.coordinator.data["outlets"]:
                    if not outlet.status:  # Only turn on if currently off
                        await self.hass.async_add_executor_job(
                            self.coordinator.client.turn_on_outlet, outlet.index
                        )
                
                _LOGGER.debug("Successfully turned on all outlets")
                # Refresh data after successful action
                await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Error turning on all outlets: %s", err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn all outlets off."""
        try:
            # Use the reset all outlets command (outlet 0)
            success = await self.hass.async_add_executor_job(
                self.coordinator.client.turn_off_outlet, 0  # 0 = all outlets
            )
            if success:
                _LOGGER.debug("Successfully turned off all outlets")
                # Refresh data after successful action
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to turn off all outlets")
        except Exception as err:
            _LOGGER.error("Error turning off all outlets: %s", err)
