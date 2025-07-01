"""
Simple test script for the WattBox A    # Test client instantiation
    try:
        client = WattBoxClient(
            host="192.168.1.100",
         r        else:
            print("❌ Cannot connect to 192.168.1.203:23")ult = test_socket.connect_ex(("192.168.1.203", 23))
        test_socket.close()
        
        if result == 0:
            print("✅ Basic connectivity to 192.168.1.203:23 successful")      port=23,
            username="wattbox",
            password="wattbox",
            timeout=10.0
        )y.

This script demonstrates basic usage of the pywattbox_api_v2_4 library.
"""

import sys
import os

# Add the library path to sys.path for testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import with the correct module name (replacing dots with underscores)
import pywattbox_api_v2_4 as wattbox_api


def test_api_library():
    """Test basic functionality of the API library."""
    print("Testing WattBox API Library v2.4")
    print("-" * 40)
    
    # Test basic imports
    try:
        from pywattbox_api_v2_4 import (
            WattBoxClient,
            WattBoxDevice,
            OutletInfo,
            PowerStatus,
            UPSStatus,
            SystemInfo,
            WattBoxError,
            WattBoxConnectionError,
            WattBoxAuthenticationError,
            WattBoxCommandError,
            WattBoxTimeoutError,
        )
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test client instantiation
    try:
        client = WattBoxClient(
            host="192.168.1.100",  # Example IP
            port=23,
            username="wattbox",
            password="wattbox",
            timeout=10.0
        )
        print("✅ Client instantiation successful")
    except Exception as e:
        print(f"❌ Client instantiation error: {e}")
        return False
    
    # Test endpoint formatting
    try:
        from pywattbox_api_v2_4.endpoints import WattBoxEndpoints
        
        # Test various endpoint methods
        outlet_cmd = WattBoxEndpoints.outlet_set(1, "ON")
        assert outlet_cmd == "!OutletSet=1,ON"
        
        power_cmd = WattBoxEndpoints.outlet_power_status(1)
        assert power_cmd == "?OutletPowerStatus=1"
        
        names_cmd = WattBoxEndpoints.outlet_name_set_all(["Outlet 1", "Outlet 2"])
        assert names_cmd == "!OutletNameSetAll={Outlet 1},{Outlet 2}"
        
        print("✅ Endpoint formatting tests passed")
    except Exception as e:
        print(f"❌ Endpoint formatting error: {e}")
        return False
    
    # Test response parsing
    try:
        from pywattbox_api_v2_4.models import (
            parse_outlet_status_response,
            parse_outlet_names_response,
            parse_outlet_power_response,
            parse_power_status_response,
            parse_ups_status_response,
        )
        
        # Test outlet status parsing
        status_resp = "?OutletStatus=1,0,1,0,1,0\n"
        statuses = parse_outlet_status_response(status_resp)
        assert statuses == [True, False, True, False, True, False]
        
        # Test outlet names parsing
        names_resp = "?OutletName={Router},{Switch},{Camera},{Light},{Fan},{Spare}\n"
        names = parse_outlet_names_response(names_resp)
        assert names == ["Router", "Switch", "Camera", "Light", "Fan", "Spare"]
        
        # Test power status parsing
        power_resp = "?PowerStatus=5.5,660.0,120.0,1\n"
        power_status = parse_power_status_response(power_resp)
        assert power_status.current_amps == 5.5
        assert power_status.power_watts == 660.0
        assert power_status.voltage_volts == 120.0
        assert power_status.safe_voltage_status == True
        
        print("✅ Response parsing tests passed")
    except Exception as e:
        print(f"❌ Response parsing error: {e}")
        return False
    
    # Test utility functions
    try:
        from pywattbox_api_v2_4.utils import (
            validate_ip_address,
            validate_port,
            validate_outlet_number,
            format_command,
            sanitize_outlet_name,
        )
        
        assert validate_ip_address("192.168.1.100") == True
        assert validate_ip_address("invalid.ip") == False
        assert validate_port(80) == True
        assert validate_port(70000) == False
        assert validate_outlet_number(5, 10) == True
        assert validate_outlet_number(15, 10) == False
        assert format_command("?Firmware") == "?Firmware\n"
        assert sanitize_outlet_name("Test{Outlet},Name") == "TestOutletName"
        
        print("✅ Utility function tests passed")
    except Exception as e:
        print(f"❌ Utility function error: {e}")
        return False
    
    print("\n🎉 All API library tests passed!")
    print("The pywattbox_api_v2_4 library is ready for use.")
    
    # Test with real device (read-only operations)
    print("\n" + "=" * 50)
    print("Testing with Real WattBox Device")
    print("=" * 50)
    
    # First test basic connectivity
    import socket
    print("\n🔌 Testing basic connectivity...")
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5.0)
        result = test_socket.connect_ex(("192.168.1.203", 22))
        test_socket.close()
        
        if result == 0:
            print("✅ Basic connectivity to 192.168.1.203:22 successful")
        else:
            print("❌ Cannot connect to 192.168.1.203:22")
            print("⚠️  Device may be offline, IP changed, or telnet disabled")
            print("⚠️  Skipping real device tests")
            return True
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        print("⚠️  Skipping real device tests")
        return True
    
    try:
        real_client = WattBoxClient(
            host="192.168.1.203",
            port=23,
            username="admin",
            password="Wireline1!",
            timeout=10.0
        )
        print("✅ Real device client created")
        
        # Test connection and authentication
        try:
            print("\n📡 Connecting to device...")
            real_client.connect()
            print("✅ Connected and authenticated successfully")
            
            # Get device information
            print("\n📋 Getting device information...")
            system_info = real_client.get_system_info()
            print(f"✅ Device Model: {system_info.model}")
            print(f"✅ Firmware: {system_info.firmware}")
            print(f"✅ Hostname: {system_info.hostname}")
            print(f"✅ Service Tag: {system_info.service_tag}")
            print(f"✅ Outlet Count: {system_info.outlet_count}")
            
            # Get outlet status
            print("\n🔌 Getting outlet status...")
            outlet_statuses = real_client.get_outlet_status()
            for i, status in enumerate(outlet_statuses, 1):
                status_text = "ON" if status else "OFF"
                print(f"   Outlet {i}: {status_text}")
            
            # Get outlet names
            print("\n🏷️  Getting outlet names...")
            outlet_names = real_client.get_outlet_names()
            for i, name in enumerate(outlet_names, 1):
                print(f"   Outlet {i}: '{name}'")
            
            # Get system power status
            print("\n⚡ Getting system power status...")
            power_status = real_client.get_power_status()
            print(f"   System Current: {power_status.current_amps} A")
            print(f"   System Power: {power_status.power_watts} W")
            print(f"   System Voltage: {power_status.voltage_volts} V")
            print(f"   Safe Voltage: {'YES' if power_status.safe_voltage_status else 'NO'}")
            
            # Get individual outlet power readings (if supported)
            print("\n🔋 Getting individual outlet power readings...")
            for outlet_num in range(1, min(system_info.outlet_count + 1, 5)):  # Test first 4 outlets
                try:
                    outlet_power = real_client.get_outlet_power_status(outlet_num)
                    print(f"   Outlet {outlet_num}: {outlet_power.power_watts:.2f}W, "
                          f"{outlet_power.current_amps:.3f}A, {outlet_power.voltage_volts:.1f}V")
                except Exception as e:
                    print(f"   Outlet {outlet_num}: Power reading not available ({e})")
            
            # Check UPS status (if available)
            print("\n🔋 Checking UPS status...")
            try:
                ups_connection = real_client.get_ups_connection_status()
                if ups_connection:
                    print("   UPS Connected: YES")
                    ups_status = real_client.get_ups_status()
                    print(f"   Battery Charge: {ups_status.battery_charge}%")
                    print(f"   Battery Load: {ups_status.battery_load}%")
                    print(f"   Battery Health: {ups_status.battery_health}")
                    print(f"   Power Lost: {'YES' if ups_status.power_lost else 'NO'}")
                    print(f"   Runtime: {ups_status.battery_runtime} minutes")
                    print(f"   Alarm Enabled: {'YES' if ups_status.alarm_enabled else 'NO'}")
                    print(f"   Alarm Muted: {'YES' if ups_status.alarm_muted else 'NO'}")
                else:
                    print("   UPS Connected: NO")
            except Exception as e:
                print(f"   UPS status not available: {e}")
            
            # Check auto reboot status
            print("\n🔄 Checking auto reboot status...")
            try:
                auto_reboot = real_client.get_auto_reboot_status()
                print(f"   Auto Reboot: {'ENABLED' if auto_reboot else 'DISABLED'}")
            except Exception as e:
                print(f"   Auto reboot status not available: {e}")
            
            print("\n✅ Real device testing completed successfully!")
            
        except WattBoxConnectionError as e:
            print(f"❌ Connection error: {e}")
            print("⚠️  This might be normal if the device is not accessible")
            print("   - Check that the WattBox is powered on and connected to network")
            print("   - Verify the IP address (192.168.1.203) is correct")
            print("   - Ensure telnet is enabled on the device (port 23)")
            return True  # Don't fail the test for connection issues
        except WattBoxAuthenticationError as e:
            print(f"❌ Authentication error: {e}")
            print("⚠️  Check username/password: admin/Wireline1!")
            return True  # Don't fail the test for auth issues
        except Exception as e:
            print(f"❌ Unexpected error during device testing: {e}")
            return False
        finally:
            try:
                real_client.disconnect()
                print("🔌 Disconnected from device")
            except:
                pass
                
    except Exception as e:
        print(f"❌ Error creating real device client: {e}")
        # Don't fail the entire test if real device testing fails
        print("⚠️  Real device testing skipped, but library tests passed")
    
    return True


if __name__ == "__main__":
    success = test_api_library()
    sys.exit(0 if success else 1)
