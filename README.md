[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

# Home Assistant Wattbox Integration

_A comprehensive Home Assistant integration for [WattBox][wattbox] power management devices._

This integration provides full control and monitoring of WattBox devices through Home Assistant, featuring individual outlet control, power monitoring, and device status sensors.  **This integration was built around the Wattbox API v2.4, and has only been tested with the 800 series power strips.**

**✨ Key Features:**
- 🔌 Individual outlet control and monitoring
- ⚡ Real-time power consumption tracking per outlet
- 📊 Comprehensive device sensors (voltage, current, battery status, etc.)
- 🖥️ Easy setup through Home Assistant's UI (Config Flow)
- 🔄 Automatic device discovery and configuration
- 📱 Modern API integration with improved reliability

## Installation

### HACS Installation (Recommended)

1. **Add Custom Repository:**
   - Open HACS in Home Assistant
   - Go to "Integrations"
   - Click the three dots menu (⋮) in the top right
   - Select "Custom repositories"
   - Add `https://github.com/bballdavis/hass-wattbox` as repository
   - Set category to "Integration"
   - Click "Add"

2. **Install the Integration:**
   - Search for "WattBox" in HACS
   - Click "Download"
   - Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/bballdavis/hass-wattbox/releases)
2. Extract the `custom_components/wattbox` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Adding WattBox Devices

1. **Via UI (Recommended):**
   - Go to Settings → Devices & Services
   - Click "Add Integration"
   - Search for "WattBox"
   - Enter your WattBox device details:
     - Host IP address
     - Port (default: 23)
     - Username (default: wattbox, latest firmwares for you to change this)
     - Password (default: wattbox, latest firmwares for you to change this)
     - Device name (optional)
   - Click "Submit"

### Configuration Options

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `host` | Yes | - | IP address of your WattBox device |
| `port` | No | 80 | HTTP port for the WattBox web interface |
| `username` | No | wattbox | Authentication username |
| `password` | No | wattbox | Authentication password |
| `name` | No | wattbox | Friendly name for the device |

## Available Entities

Once configured, the integration will automatically create entities for your WattBox device:

### Switches
- **Individual Outlets:** Control each outlet independently (`switch.wattbox_outlet_1`, `switch.wattbox_outlet_2`, etc.)
- **Master Control:** Controls all outlets configured for master control on the device

### Sensors

#### Power Monitoring (Per Outlet)
- **Power Consumption:** Real-time power usage in watts (`sensor.wattbox_outlet_1_power`)
- **Current:** Current draw in amps (`sensor.wattbox_outlet_1_current`)
- **Voltage:** Voltage measurement (`sensor.wattbox_outlet_1_voltage`)

#### Device Status
- **Total Power:** Overall device power consumption
- **Total Current:** Total current draw across all outlets
- **Input Voltage:** Main input voltage to the device


### Binary Sensors
- **Auto Reboot:** Status of auto-reboot being enabled
- **Firmware Version:** Current firmware version
- **Service Tag:** Easy reference for your service tag #
- **UPS Connected:** Status of connection to the UPS

## Usage

### Outlet Control
- Use the individual outlet switches to control specific devices
- The master switch controls all outlets configured for master control
- Outlet status is updated in real-time

### Power Monitoring
- Monitor individual outlet power consumption
- Track total device power usage
- Set up automations based on power thresholds

### Safety Features
- Monitor voltage quality with safe voltage status

⚠️ **Important:** Be careful when controlling outlets that power networking equipment. Turning off the wrong outlet could disable remote access to your WattBox device.

## Troubleshooting

### Common Issues

**Device Not Found:**
- Verify the IP address and port are correct
- Ensure the WattBox is powered on and accessible on the network
- Check that the username and password are correct

**Connection Timeout:**
- Verify network connectivity between Home Assistant and the WattBox
- Check if a firewall is blocking the connection
- Try increasing the scan interval

**Missing Entities:**
- Restart Home Assistant after installation
- Check the Home Assistant logs for any error messages
- Verify the WattBox firmware supports the required API endpoints

### Getting Help

- [Report Issues](https://github.com/bballdavis/hass-wattbox/issues)
- [Community Discussion](https://community.home-assistant.io/)
- [Discord Support](https://discord.gg/Qa5fW2R)

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## Changelog

### Recent Updates
- ✅ Added Config Flow for easy UI-based setup
- ✅ Individual power monitoring per outlet
- ✅ Enhanced API integration with improved reliability
- ✅ Better error handling and connection management
- ✅ Comprehensive entity coverage for all WattBox features

## Acknowledgments

This project is a comprehensive rewrite and enhancement of the original [hass-wattbox integration](https://github.com/eseglem/hass-wattbox) by [@eseglem](https://github.com/eseglem). We extend our sincere gratitude for the foundation and inspiration provided by the original work.

Key improvements in this version:
- Complete Config Flow implementation
- Individual outlet power monitoring
- Enhanced API client with modern architecture
- Improved reliability and error handling
- Comprehensive test coverage

Based on [custom-components/integration_blueprint][blueprint]

<!---->

***

[wattbox]: https://www.snapav.com/shop/en/snapav/wattbox
[hacs]: https://hacs.xyz/
[blueprint]: https://github.com/custom-components/integration_blueprint
[buymecoffee]: https://www.buymeacoffee.com/bballdavis
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow
[commits-shield]: https://img.shields.io/github/last-commit/bballdavis/hass-wattbox
[commits]: https://github.com/bballdavis/hass-wattbox/commits/master
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/bballdavis/hass-wattbox
[maintenance-shield]: https://img.shields.io/badge/Maintainer-Philip%20Davis-blue
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange
