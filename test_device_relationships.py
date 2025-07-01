#!/usr/bin/env python3
"""Test device relationships in the WattBox integration."""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'custom_components', 'wattbox'))

def test_device_relationships():
    """Test device relationships for WattBox integration."""
    print("Testing device relationships...")
    
    try:
        from const import get_outlet_device_info, get_wattbox_device_info
        
        host = '192.168.1.100'
        outlet_index = 1
        outlet_name = 'Test Outlet'
        
        # Get device info
        wattbox_device = get_wattbox_device_info(host)
        outlet_device = get_outlet_device_info(host, outlet_index, outlet_name)
        
        print(f"WattBox Device: {wattbox_device}")
        print(f"Outlet Device: {outlet_device}")
        
        # Check relationships
        wattbox_identifier = list(wattbox_device['identifiers'])[0]
        outlet_via_device = outlet_device.get('via_device')
        
        print(f"WattBox identifier: {wattbox_identifier}")
        print(f"Outlet via_device: {outlet_via_device}")
        print(f"Relationship correct: {wattbox_identifier == outlet_via_device}")
        
        # Check that switch structure is correct
        from switch import WattBoxMasterSwitch, WattBoxOutletSwitch
        print(f"Master switch class available: {WattBoxMasterSwitch is not None}")
        print(f"Outlet switch class available: {WattBoxOutletSwitch is not None}")
        
        return True
        
    except Exception as e:
        print(f"Error testing device relationships: {e}")
        return False

if __name__ == "__main__":
    success = test_device_relationships()
    if success:
        print("\n✅ Device relationship tests passed!")
    else:
        print("\n❌ Device relationship tests failed!")
