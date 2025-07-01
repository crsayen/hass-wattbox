# WattBox Integration Restructuring - Summary

## Overview
This document summarizes the changes made to restructure the WattBox Home Assistant integration to create separate devices for each outlet, improving organization and usability.

## Key Changes

### 1. Device Structure Changes

**Before:**
- Single WattBox device containing all entities (switches, sensors, binary sensors for all outlets)
- All outlets were entities under one device

**After:**
- **Main WattBox Device**: Contains system-level entities
- **Individual Outlet Devices**: Each outlet becomes its own device with related entities

### 2. File Modifications

#### `const.py`
- **Added**: `OUTLET_SENSOR_TYPES` constant defining outlet-specific sensors
- **Added**: `get_outlet_device_info()` helper function
- **Added**: `get_wattbox_device_info()` helper function

#### `switch.py`
- **Modified**: `WattBoxOutletSwitch` now creates individual outlet devices
  - Device identifier: `(wattbox, <host>_outlet_<number>)`
  - Device name: Uses API outlet name (e.g., "Living Room TV")
  - Entity name: Simple outlet name (not prefixed with "WattBox")
- **Unchanged**: `WattBoxMasterSwitch` remains on main device

#### `sensor.py`
- **Modified**: Outlet sensors now belong to individual outlet devices
- **Added**: New `WattBoxOutletSensor` class for outlet-specific sensors
- **Created**: Power, Current, and Voltage sensors for each outlet (if supported)
- **Unchanged**: System sensors remain on main device

#### `binary_sensor.py`
- **Modified**: Outlet status sensors now belong to individual outlet devices
- **Modified**: `WattBoxOutletStatusSensor` creates entities on outlet devices
- **Unchanged**: System binary sensors remain on main device

### 3. Entity Organization

#### Main WattBox Device (`<host>`)
**Entities:**
- Switch: "WattBox Master Switch" (controls all outlets)
- Sensors: 
  - "WattBox Firmware"
  - "WattBox Model" 
  - "WattBox Hostname"
  - "WattBox Service Tag"
  - "WattBox Outlet Count"
  - Power monitoring (if available): "WattBox Voltage", "WattBox Current", "WattBox Power"
  - UPS sensors (if connected): "WattBox UPS Battery Level", etc.
- Binary Sensors:
  - "WattBox Auto Reboot Enabled"
  - "WattBox UPS Connected"
  - "WattBox UPS On Battery" (if UPS connected)

#### Individual Outlet Devices (`<host>_outlet_<number>`)
**Device Name:** API outlet name (e.g., "Living Room TV", "Kitchen Outlets")
**Entities:**
- Switch: Outlet name (e.g., "Living Room TV")
- Binary Sensor: "Status"
- Sensors (if power monitoring supported):
  - "Power"
  - "Current"
  - "Voltage"

### 4. Benefits

1. **Better Organization**: Each outlet is a logical device with related entities
2. **Cleaner Entity Names**: No "WattBox" prefix needed for outlet entities
3. **Improved Automation**: Easier to create automations for specific outlets
4. **Scalability**: Supports WattBox units with many outlets without cluttering
5. **Power Monitoring**: Individual power sensors for outlets that support it

### 5. Unique Identifiers

- **Main Device**: `(wattbox, <host>)`
- **Outlet Devices**: `(wattbox, <host>_outlet_<number>)`
- **Outlet Switch**: `<host>_outlet_<number>_switch`
- **Outlet Status**: `<host>_outlet_<number>_status`
- **Outlet Power**: `<host>_outlet_<number>_power`
- **Outlet Current**: `<host>_outlet_<number>_current`
- **Outlet Voltage**: `<host>_outlet_<number>_voltage`

### 6. Backward Compatibility

- Unique IDs have changed, so entities will be recreated on upgrade
- Users should remove the old integration and re-add it for clean migration
- Automations and scripts will need to be updated to use new entity IDs

## Testing

All Python files pass syntax validation. The integration is ready for testing in a Home Assistant environment.

## Next Steps

1. Test the integration in a live Home Assistant environment
2. Update documentation and examples
3. Consider adding configuration options for power monitoring thresholds
4. Test with different WattBox models to ensure compatibility
