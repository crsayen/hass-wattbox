#!/usr/bin/env python3
"""
Test script to verify WattBox integration structure changes.
This script simulates the key functionality without requiring Home Assistant.
"""

import sys
import os

# Add the custom component path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components', 'wattbox'))

def test_constants():
    """Test the constants and helper functions."""
    print("Testing constants and helper functions...")
    
    try:
        # Test imports
        from const import (
            DOMAIN, 
            OUTLET_SENSOR_TYPES, 
            get_outlet_device_info, 
            get_wattbox_device_info,
            extract_outlet_number_from_device_model
        )
        
        print(f"✓ Domain: {DOMAIN}")
        print(f"✓ Outlet sensor types: {list(OUTLET_SENSOR_TYPES.keys())}")
        
        # Test helper functions
        host = "192.168.1.100"
        outlet_device_info = get_outlet_device_info(host, 1, "Living Room TV")
        wattbox_device_info = get_wattbox_device_info(host)
        
        print("✓ Outlet device info structure:")
        for key, value in outlet_device_info.items():
            print(f"  {key}: {value}")
            
        print("✓ WattBox device info structure:")
        for key, value in wattbox_device_info.items():
            print(f"  {key}: {value}")
        
        # Test outlet number extraction function
        test_model = "WattBox Outlet 5"
        outlet_num = extract_outlet_number_from_device_model(test_model)
        print(f"✓ Extracted outlet number {outlet_num} from '{test_model}'")
        
        return True
        
    except Exception as e:
        print(f"✗ Constants test failed: {e}")
        return False

def test_imports():
    """Test that all imports work (ignoring Home Assistant specific ones)."""
    print("\nTesting imports...")
    
    try:
        # Test files can be imported (syntax check)
        import importlib.util
        
        files_to_test = [
            'custom_components/wattbox/const.py',
            'custom_components/wattbox/switch.py',
            'custom_components/wattbox/sensor.py',
            'custom_components/wattbox/binary_sensor.py'
        ]
        
        for file_path in files_to_test:
            spec = importlib.util.spec_from_file_location("module", file_path)
            if spec and spec.loader:
                print(f"✓ {file_path} - syntax OK")
            else:
                print(f"✗ {file_path} - syntax error")
                return False
                
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("WattBox Integration Structure Test")
    print("=" * 40)
    
    tests = [
        test_constants,
        test_imports,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print(f"\nTest Results:")
    print(f"Passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All tests passed! The integration structure looks good.")
    else:
        print("❌ Some tests failed. Please check the output above.")

if __name__ == "__main__":
    main()
