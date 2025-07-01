"""Binary sensor platform for wattbox."""

import logging
from typing import Optional

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
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
    """Set up WattBox binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Auto reboot status
    entities.append(WattBoxAutoRebootSensor(coordinator))
    
    # UPS connected status
    entities.append(WattBoxUPSConnectedSensor(coordinator))
    
    # UPS on battery status (if UPS is connected)
    if coordinator.data and coordinator.data.get("ups_connected"):
        entities.append(WattBoxUPSOnBatterySensor(coordinator))
    
    # Individual outlet status sensors
    if coordinator.data and coordinator.data.get("outlets"):
        for outlet in coordinator.data["outlets"]:
            entities.append(WattBoxOutletStatusSensor(coordinator, outlet.index, outlet.name))
    
    async_add_entities(entities)


class WattBoxBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for WattBox binary sensors."""

    def __init__(self, coordinator, sensor_type: str, name: str, device_class: Optional[BinarySensorDeviceClass] = None):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"WattBox {name}"
        self._attr_unique_id = f"{coordinator.client.host}_{sensor_type}"
        if device_class:
            self._attr_device_class = device_class

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


class WattBoxAutoRebootSensor(WattBoxBaseBinarySensor):
    """Auto reboot status sensor."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "auto_reboot", "Auto Reboot Enabled")

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if auto reboot is enabled."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("auto_reboot_enabled", False)


class WattBoxUPSConnectedSensor(WattBoxBaseBinarySensor):
    """UPS connected status sensor."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "ups_connected", "UPS Connected", BinarySensorDeviceClass.CONNECTIVITY)

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if UPS is connected."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("ups_connected", False)


class WattBoxUPSOnBatterySensor(WattBoxBaseBinarySensor):
    """UPS on battery status sensor."""

    def __init__(self, coordinator):
        super().__init__(coordinator, "ups_on_battery", "UPS On Battery", BinarySensorDeviceClass.BATTERY)

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if UPS is on battery."""
        if not self.coordinator.data or not self.coordinator.data.get("ups_status"):
            return None
        ups_status = self.coordinator.data["ups_status"]
        return getattr(ups_status, "on_battery", False)


class WattBoxOutletStatusSensor(WattBoxBaseBinarySensor):
    """Outlet status binary sensor."""

    def __init__(self, coordinator, outlet_index: int, outlet_name: str):
        """Initialize the outlet status sensor."""
        self._outlet_index = outlet_index
        self._outlet_name = outlet_name
        super().__init__(coordinator, f"outlet_{outlet_index}_status", f"{outlet_name} Status", BinarySensorDeviceClass.POWER)

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if outlet is on."""
        if not self.coordinator.data or not self.coordinator.data.get("outlets"):
            return None
            
        for outlet in self.coordinator.data["outlets"]:
            if outlet.index == self._outlet_index:
                return outlet.status
        return None
