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
    OUTLET_SENSOR_TYPES, 
    get_outlet_device_info, 
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
    
    # UPS sensors (if available, on main WattBox device)
    if coordinator.data and coordinator.data.get("ups_connected"):
        entities.extend([
            WattBoxUPSSensor(coordinator, "battery_level", "UPS Battery Level", PERCENTAGE),
            WattBoxUPSSensor(coordinator, "runtime_remaining", "UPS Runtime Remaining"),
            WattBoxUPSSensor(coordinator, "status", "UPS Status"),
        ])
    
    # Outlet sensors (on individual outlet devices)
    if coordinator.data and coordinator.data.get("outlets"):
        outlet_count = len(coordinator.data['outlets'])
        _LOGGER.info(f"Creating sensors for {outlet_count} outlets")
        
        for outlet in coordinator.data["outlets"]:
            # Create power sensors for each outlet only if enabled
            if enable_power_sensors:
                _LOGGER.info(f"Creating power sensors for outlet {outlet.index} ({outlet.name})")
                for sensor_type, sensor_config in OUTLET_SENSOR_TYPES.items():
                    entities.append(WattBoxOutletSensor(
                        coordinator, outlet.index, outlet.name, sensor_type, 
                        sensor_config["name"], sensor_config["unit"], sensor_config["icon"]
                    ))
            else:
                _LOGGER.info(f"Power sensors disabled, skipping outlet {outlet.index}")
    
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


class WattBoxOutletSensor(CoordinatorEntity, SensorEntity):
    """Outlet-specific sensor."""

    def __init__(self, coordinator, outlet_index: int, outlet_name: str, sensor_type: str, 
                 sensor_name: str, unit: Optional[str] = None, icon: Optional[str] = None):
        """Initialize the outlet sensor."""
        super().__init__(coordinator)
        self._outlet_index = outlet_index
        self._outlet_name = outlet_name
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{coordinator.client.host}_outlet_{outlet_index}_{sensor_type}"
        self._attr_name = sensor_name  # Use the sensor name directly (e.g., "Power", "Current", "Voltage")
        if unit:
            self._attr_native_unit_of_measurement = unit
        if icon:
            self._attr_icon = icon
        
        # Cache for power data
        self._cached_power_data = None
        self._last_power_update = 0

    @property
    def device_info(self):
        """Return device information for this outlet device."""
        system_info = self.coordinator.data.get("system_info") if self.coordinator.data else None
        return get_outlet_device_info(
            self.coordinator.client.host, 
            self._outlet_index, 
            self._outlet_name,
            system_info
        )

    @property
    def device_class(self) -> Optional[SensorDeviceClass]:
        """Return the device class."""
        if self._sensor_type == "power":
            return SensorDeviceClass.POWER
        elif self._sensor_type == "current":
            return SensorDeviceClass.CURRENT
        elif self._sensor_type == "voltage":
            return SensorDeviceClass.VOLTAGE
        return None

    @property
    def suggested_display_precision(self) -> Optional[int]:
        """Return the suggested display precision for this sensor."""
        if self._sensor_type == "current":
            return 2  # 2 decimal places for current
        elif self._sensor_type in ["power", "voltage"]:
            return 0  # 0 decimal places for power and voltage
        return None

    async def async_update(self) -> None:
        """Update the sensor."""
        # Call parent update first
        await super().async_update()
        
        # For power-related sensors, try to get fresh power data periodically
        if self._sensor_type in ["power", "current", "voltage"]:
            current_time = time.time()
            # Update power data every 30 seconds to avoid excessive API calls
            if current_time - self._last_power_update > 30:
                try:
                    # Try to get individual outlet power data
                    self._cached_power_data = await self.coordinator.get_outlet_power_info(self._outlet_index)
                    self._last_power_update = current_time
                    _LOGGER.debug(f"Updated power info for outlet {self._outlet_index}: {self._cached_power_data}")
                except Exception as err:
                    _LOGGER.debug(f"Could not update power info for outlet {self._outlet_index}: {err}")
                    # Clear cached data if we can't get it
                    self._cached_power_data = None

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if not self.coordinator.data or not self.coordinator.data.get("outlets"):
            return None
        
        # For power-related sensors, first try cached power data from individual outlet queries
        if self._sensor_type in ["power", "current", "voltage"] and self._cached_power_data:
            if self._sensor_type == "power":
                value = self._cached_power_data.get("power_watts")
                if value is not None:
                    return value
            elif self._sensor_type == "current":
                value = self._cached_power_data.get("current_amps")
                if value is not None:
                    return value
            elif self._sensor_type == "voltage":
                value = self._cached_power_data.get("voltage_volts")
                if value is not None:
                    return value
        
        # Fall back to coordinator data for basic outlet info (though this will likely be None for power data)
        for outlet in self.coordinator.data["outlets"]:
            if outlet.index == self._outlet_index:
                if self._sensor_type == "power":
                    return outlet.power_watts
                elif self._sensor_type == "current":
                    return outlet.current_amps
                elif self._sensor_type == "voltage":
                    return outlet.voltage_volts
        
        # If no data is available, return None (sensor will show as unavailable)
        return None
