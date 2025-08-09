"""Sensor platform for wattbox."""

import logging
import time
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass  # type: ignore
from homeassistant.config_entries import ConfigEntry  # type: ignore
from homeassistant.const import (  # type: ignore
    UnitOfPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant  # type: ignore
from homeassistant.helpers.entity_platform import AddEntitiesCallback  # type: ignore
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # type: ignore

from .const import (
    DOMAIN, 
    get_wattbox_device_info,
    CONF_ENABLE_POWER_SENSORS,
    DEFAULT_ENABLE_POWER_SENSORS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WattBox sensor platform."""
    _LOGGER.info("=== WattBox Sensor Platform: Starting setup ===")
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Check if power monitoring is enabled in config
    enable_power_sensors = entry.data.get(CONF_ENABLE_POWER_SENSORS, DEFAULT_ENABLE_POWER_SENSORS)
    _LOGGER.info(f"Setting up WattBox sensors (power monitoring: {'enabled' if enable_power_sensors else 'disabled'})")
    _LOGGER.debug(f"Power sensors enabled: {enable_power_sensors}")
    
    entities = []
    
    # System sensors (on main WattBox device)
    entities.extend([
        WattBoxSystemSensor(coordinator, "firmware", "Firmware"),
        WattBoxSystemSensor(coordinator, "model", "Model"),
        WattBoxSystemSensor(coordinator, "hostname", "Hostname"),
        WattBoxSystemSensor(coordinator, "service_tag", "Service Tag"),
        WattBoxSystemSensor(coordinator, "outlet_count", "Outlet Count"),
    ])
    
    # Power status sensors (if available and enabled, on main WattBox device)
    if enable_power_sensors and coordinator.data and coordinator.data.get("power_status"):
        entities.extend([
            WattBoxPowerSensor(coordinator, "voltage", "Voltage", UnitOfElectricPotential.VOLT),
            WattBoxPowerSensor(coordinator, "current", "Current", UnitOfElectricCurrent.AMPERE),
            WattBoxPowerSensor(coordinator, "power", "Power", UnitOfPower.WATT),
        ])
    
    _LOGGER.info(f"Successfully created {len(entities)} WattBox sensors")
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
        """Return device information for main WattBox device."""
        system_info = self.coordinator.data.get("system_info") if self.coordinator.data else None
        return get_wattbox_device_info(self.coordinator.client.host, system_info)


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
    def suggested_display_precision(self) -> Optional[int]:
        """Return the suggested display precision for this sensor."""
        if self._sensor_type == "current":
            return 2  # 2 decimal places for current
        elif self._sensor_type in ["power", "voltage"]:
            return 0  # 0 decimal places for power and voltage
        return None

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if not self.coordinator.data or not self.coordinator.data.get("power_status"):
            return None
            
        power_status = self.coordinator.data["power_status"]
        
        # Return raw values without rounding - let Home Assistant handle display precision
        if self._sensor_type == "current":
            return power_status.current_amps
        elif self._sensor_type == "power":
            return power_status.power_watts
        elif self._sensor_type == "voltage":
            return power_status.voltage_volts
        
        return None
