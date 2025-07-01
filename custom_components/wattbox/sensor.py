"""Sensor platform for wattbox."""

import logging
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    PERCENTAGE,
)
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
    """Set up WattBox sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # System sensors
    entities.extend([
        WattBoxSystemSensor(coordinator, "firmware", "Firmware"),
        WattBoxSystemSensor(coordinator, "model", "Model"),
        WattBoxSystemSensor(coordinator, "hostname", "Hostname"),
        WattBoxSystemSensor(coordinator, "service_tag", "Service Tag"),
        WattBoxSystemSensor(coordinator, "outlet_count", "Outlet Count"),
    ])
    
    # Power status sensors (if available)
    if coordinator.data and coordinator.data.get("power_status"):
        entities.extend([
            WattBoxPowerSensor(coordinator, "voltage", "Voltage", UnitOfElectricPotential.VOLT),
            WattBoxPowerSensor(coordinator, "current", "Current", UnitOfElectricCurrent.AMPERE),
            WattBoxPowerSensor(coordinator, "power", "Power", UnitOfPower.WATT),
        ])
    
    # UPS sensors (if available)
    if coordinator.data and coordinator.data.get("ups_connected"):
        entities.extend([
            WattBoxUPSSensor(coordinator, "battery_level", "UPS Battery Level", PERCENTAGE),
            WattBoxUPSSensor(coordinator, "runtime_remaining", "UPS Runtime Remaining"),
            WattBoxUPSSensor(coordinator, "status", "UPS Status"),
        ])
    
    # Outlet sensors
    if coordinator.data and coordinator.data.get("outlets"):
        for outlet in coordinator.data["outlets"]:
            # Basic outlet sensors
            entities.append(WattBoxOutletSensor(coordinator, outlet.index, "status", "Status"))
            
            # Power monitoring sensors (if supported)
            if outlet.power_watts is not None:
                entities.append(WattBoxOutletSensor(coordinator, outlet.index, "power", "Power", UnitOfPower.WATT))
            if outlet.current_amps is not None:
                entities.append(WattBoxOutletSensor(coordinator, outlet.index, "current", "Current", UnitOfElectricCurrent.AMPERE))
            if outlet.voltage_volts is not None:
                entities.append(WattBoxOutletSensor(coordinator, outlet.index, "voltage", "Voltage", UnitOfElectricPotential.VOLT))
    
    async_add_entities(entities)


class WattBoxBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for WattBox sensors."""

    def __init__(self, coordinator, sensor_type: str, name: str, unit: Optional[str] = None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"WattBox {name}"
        self._attr_unique_id = f"{coordinator.client.host}_{sensor_type}"
        if unit:
            self._attr_native_unit_of_measurement = unit

    @property
    def device_info(self):
        """Return device information."""
        system_info = self.coordinator.data.get("system_info") if self.coordinator.data else None
        return {
            "identifiers": {(DOMAIN, self.coordinator.client.host)},
            "name": "WattBox",
            "manufacturer": "SnapAV",
            "model": getattr(system_info, "model", "Unknown") if system_info else "Unknown",
            "sw_version": getattr(system_info, "firmware", "Unknown") if system_info else "Unknown",
        }


class WattBoxSystemSensor(WattBoxBaseSensor):
    """System information sensor."""

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if not self.coordinator.data or not self.coordinator.data.get("system_info"):
            return None
            
        system_info = self.coordinator.data["system_info"]
        return getattr(system_info, self._sensor_type, None)


class WattBoxPowerSensor(WattBoxBaseSensor):
    """Power status sensor."""

    @property
    def device_class(self) -> Optional[SensorDeviceClass]:
        """Return the device class."""
        if self._sensor_type == "voltage":
            return SensorDeviceClass.VOLTAGE
        elif self._sensor_type == "current":
            return SensorDeviceClass.CURRENT
        elif self._sensor_type == "power":
            return SensorDeviceClass.POWER
        return None

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if not self.coordinator.data or not self.coordinator.data.get("power_status"):
            return None
            
        power_status = self.coordinator.data["power_status"]
        return getattr(power_status, f"{self._sensor_type}_value", None)


class WattBoxUPSSensor(WattBoxBaseSensor):
    """UPS status sensor."""

    @property
    def device_class(self) -> Optional[SensorDeviceClass]:
        """Return the device class."""
        if self._sensor_type == "battery_level":
            return SensorDeviceClass.BATTERY
        return None

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if not self.coordinator.data or not self.coordinator.data.get("ups_status"):
            return None
            
        ups_status = self.coordinator.data["ups_status"]
        return getattr(ups_status, self._sensor_type, None)


class WattBoxOutletSensor(WattBoxBaseSensor):
    """Outlet-specific sensor."""

    def __init__(self, coordinator, outlet_index: int, sensor_type: str, name: str, unit: Optional[str] = None):
        """Initialize the outlet sensor."""
        self._outlet_index = outlet_index
        outlet_name = self._get_outlet_name()
        super().__init__(coordinator, f"outlet_{outlet_index}_{sensor_type}", f"{outlet_name} {name}", unit)

    def _get_outlet_name(self) -> str:
        """Get the outlet name."""
        if self.coordinator.data and self.coordinator.data.get("outlets"):
            for outlet in self.coordinator.data["outlets"]:
                if outlet.index == self._outlet_index:
                    return outlet.name
        return f"Outlet {self._outlet_index}"

    @property
    def device_class(self) -> Optional[SensorDeviceClass]:
        """Return the device class."""
        if self._sensor_type.endswith("_power"):
            return SensorDeviceClass.POWER
        elif self._sensor_type.endswith("_current"):
            return SensorDeviceClass.CURRENT
        elif self._sensor_type.endswith("_voltage"):
            return SensorDeviceClass.VOLTAGE
        return None

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if not self.coordinator.data or not self.coordinator.data.get("outlets"):
            return None
            
        for outlet in self.coordinator.data["outlets"]:
            if outlet.index == self._outlet_index:
                if self._sensor_type.endswith("_status"):
                    return "on" if outlet.status else "off"
                elif self._sensor_type.endswith("_power"):
                    return outlet.power_watts
                elif self._sensor_type.endswith("_current"):
                    return outlet.current_amps
                elif self._sensor_type.endswith("_voltage"):
                    return outlet.voltage_volts
        return None
