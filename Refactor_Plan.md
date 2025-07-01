# WattBox 800 Series Integration Refactor Plan

## Current Codebase Analysis

### File Structure Overview

#### Core Integration Files
- **`__init__.py`** - Main component setup### Priority 1 (Core Functionality)
1. ✅ Convert API documentation to markdown
2. ✅ Create new API library (basic functionality) 
3. Implement config flow
4. Update coordinator pattern
5. Basic outlet switches and power sensors
- **`const.py`** - Constants, sensor/binary sensor definitions, device classes 
- **`entity.py`** - Base entity class with dispatcher pattern for updates
- **`manifest.json`** - Integration metadata, currently depends on pywattbox>=0.4.0,<0.7.0

#### Platform Files
- **`binary_sensor.py`** - Binary sensors for status indicators (power_lost, battery_health, etc.)
- **`sensor.py`** - Numeric sensors (voltage, current, power, battery levels)
- **`switch.py`** - Outlet controls and master switch functionality

#### Configuration
- **`.devcontainer/configuration.yaml`** - Development config (YAML-based configuration)
- Currently requires manual YAML configuration, no config flow

### Current Limitations
1. **Legacy API**: Uses older pywattbox library that may not support 800 series
2. **No Config Flow**: Requires manual YAML configuration
3. **Fixed Sensor Set**: Hardcoded sensor types, not dynamic based on device capabilities
4. **Limited Device Discovery**: Doesn't use API to determine outlet count or capabilities
5. **No Device Grouping**: Individual entities, no device organization

## Refactor Plan

### Phase 1: New API Library Development

#### 1.1 Convert API Documentation
- **Input**: `docs/SnapAV_Wattbox_API_V2.4.pdf`
- **Output**: `docs/wattbox_api_v2.4.md`
- **Content**: Convert PDF to structured markdown with:
  - Endpoint documentation
  - Parameter specifications
  - Response schemas
  - Error codes
  - Authentication methods

#### 1.2 Create New API Library
- **Location**: `pywattbox_api_v2_4/` (separate package for potential standalone publishing)
- **Structure**:
  ```
  pywattbox_api_v2_4/
  ├── __init__.py
  ├── client.py          # Main API client
  ├── models.py          # Data models/schemas
  ├── exceptions.py      # Custom exceptions
  ├── endpoints.py       # Endpoint definitions
  └── utils.py          # Helper utilities
  ```

#### 1.3 Key API Functions to Implement
Based on 800 series needs:
- **Device Discovery**: `GET /control` (device info, outlet count)
- **Outlet Management**: 
  - `GET /control?OutletCount` - Get number of outlets
  - `GET /control?OutletName=X` - Get outlet names
  - `GET /control?OutletStatus=X` - Get outlet status
  - `POST /control` - Control outlets
- **Monitoring**:
  - `GET /control?Voltage` - Voltage readings  
  - `GET /control?Current` - Current readings
  - `GET /control?Power` - Power readings
  - `GET /control?SafeVoltageStatus` - Safety status
- **System Info**:
  - `GET /control?SystemInfo` - Device information
  - `GET /control?UPSInfo` - UPS status (if applicable)

### Phase 2: Configuration Flow Implementation

#### 2.1 Add Config Flow Support
- **New File**: `config_flow.py`
- **Features**:
  - Auto-discovery via network scanning
  - Manual IP entry
  - Authentication validation
  - Device capability detection
  - Multiple device support

#### 2.2 Update Manifest
- Remove pywattbox dependency
- Add config_flow: true
- Update version and requirements

#### 2.3 Options Flow
- Scan interval configuration
- Resource selection (which sensors to enable)
- Advanced settings (timeouts, etc.)

### Phase 3: Enhanced Entity Architecture

#### 3.1 Device-Based Organization
Create device entities for each WattBox unit with:
- Device info (model, firmware, serial)
- Grouped entities (outlets, sensors, switches)
- Device-level diagnostics

#### 3.2 Dynamic Entity Creation
- Use `?OutletCount` to determine number of outlets
- Create entities per outlet:
  - **Switch**: Outlet control
  - **Sensor**: Power consumption
  - **Sensor**: Voltage reading  
  - **Binary Sensor**: Safe voltage status
  - **Sensor**: Current reading
  - **Text Sensor**: Outlet name

#### 3.3 Updated Entity Files

**New Structure**:
```
custom_components/wattbox/
├── __init__.py           # Coordinator setup
├── config_flow.py        # Configuration flow
├── const.py              # Updated constants
├── coordinator.py        # Data update coordinator  
├── entity.py             # Base entity classes
├── device.py             # Device management
├── binary_sensor.py      # System status sensors
├── sensor.py             # Numeric sensors (per-outlet + system)
├── switch.py             # Outlet switches + master
└── text.py               # Text sensors (outlet names)
```

### Phase 4: Coordinator Pattern Implementation

#### 4.1 Replace Polling with Coordinator
- **New File**: `coordinator.py`
- **Purpose**: Centralized data fetching and caching
- **Benefits**: Reduced API calls, better error handling, coordinated updates

#### 4.2 Update Pattern
- Single coordinator per WattBox device
- All entities subscribe to coordinator updates
- Configurable update intervals
- Exponential backoff on errors

### Phase 5: Enhanced Sensor Implementation

#### 5.1 System-Level Sensors
From existing SENSOR_TYPES, keep relevant ones:
- Battery charge (if UPS model)
- Battery load (if UPS model)  
- System current
- System power
- System voltage
- Estimated runtime (if UPS model)

#### 5.2 Per-Outlet Sensors
New sensor types for each outlet:
- Power consumption (`OutletPower=X`)
- Voltage reading (`OutletVoltage=X`)
- Current reading (`OutletCurrent=X`)
- Safe voltage status (`OutletSafeVoltageStatus=X`)

#### 5.3 Outlet Naming
- Text sensor showing outlet name (`OutletName=X`)
- Configurable via WattBox web interface
- Used in entity naming for clarity

### Phase 6: Advanced Features (Future)

#### 6.1 Diagnostics
- Connection status
- API response times
- Error rates
- Device uptime

#### 6.2 Services
- Bulk outlet control
- Reboot command
- Factory reset (with confirmation)

#### 6.3 Automation Helpers
- Scene support for outlet states
- Power threshold automations
- Safe voltage monitoring

## Implementation Order

### Priority 1 (Core Functionality)
1. ✅ Convert API documentation to markdown
2. Create new API library (basic functionality)
3. Implement config flow
4. Update coordinator pattern
5. Basic outlet switches and power sensors

### Priority 2 (Enhanced Features)  
1. Per-outlet sensors (voltage, current, safe voltage)
2. Device organization and diagnostics
3. Text sensors for outlet names
4. Master switch with proper state management

### Priority 3 (Polish)
1. Advanced configuration options
2. Error handling improvements
3. Performance optimizations
4. Documentation updates

## Breaking Changes

### Configuration Migration
- **Old**: YAML-based configuration in `configuration.yaml`
- **New**: UI-based configuration via config flow
- **Migration**: Automatic detection and migration helper

### Entity ID Changes
- **Old**: `sensor.wattbox_voltage_value`
- **New**: `sensor.wattbox_device_name_system_voltage`
- **Per-outlet**: `sensor.wattbox_device_name_outlet_1_power`

### API Changes
- New dependency on custom API library
- Different update mechanisms (coordinator vs. polling)
- Enhanced error handling and retries

## Testing Strategy

### Unit Tests
- API library functionality
- Config flow validation  
- Coordinator behavior
- Entity state management

### Integration Tests
- End-to-end device communication
- Configuration migration
- Multi-device scenarios
- Error conditions

### Manual Testing
- Real hardware validation
- Performance testing
- User experience validation
- Documentation accuracy

## Documentation Updates

### User Documentation
- Installation instructions (HACS)
- Configuration guide
- Troubleshooting steps
- Feature overview

### Developer Documentation  
- API library usage
- Contributing guidelines
- Architecture overview
- Testing procedures

## Compatibility

### Home Assistant Versions
- Target: 2024.1+ (current patterns)
- Test with: 2023.12+ (backwards compatibility)

### WattBox Models
- Primary: 800 series (new API)
- Secondary: Legacy models (if API compatible)
- Fallback: Clear error messages for unsupported models

This refactor plan provides a comprehensive roadmap for modernizing the WattBox integration while maintaining backward compatibility where possible and setting up a robust foundation for future enhancements.