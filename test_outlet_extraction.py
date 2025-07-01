#!/usr/bin/env python3
"""
Test script specifically for our outlet number extraction function
"""

def test_outlet_extraction():
    """Test the outlet number extraction function without Home Assistant dependencies."""
    import re
    
    def extract_outlet_number_from_device_model(device_model: str) -> int:
        """Extract outlet number from our device model string.
        
        Our device models are formatted as: "WattBox Outlet <number>"
        This function extracts the outlet number for use in API commands.
        """
        # Look for "WattBox Outlet <number>" pattern
        match = re.search(r'WattBox Outlet (\d+)', device_model)
        if match:
            return int(match.group(1))
        
        # Fallback - look for any number in the string
        numbers = re.findall(r'\d+', device_model)
        if numbers:
            return int(numbers[-1])  # Take the last number found
        
        raise ValueError(f"Could not extract outlet number from device model: {device_model}")
    
    print("Testing outlet number extraction...")
    
    test_cases = [
        ("WattBox Outlet 1", 1),
        ("WattBox Outlet 5", 5),
        ("WattBox Outlet 12", 12),
    ]
    
    all_passed = True
    
    for test_model, expected in test_cases:
        try:
            result = extract_outlet_number_from_device_model(test_model)
            if result == expected:
                print(f"✓ '{test_model}' -> {result}")
            else:
                print(f"✗ '{test_model}' -> {result} (expected {expected})")
                all_passed = False
        except Exception as e:
            print(f"✗ '{test_model}' -> Error: {e}")
            all_passed = False
    
    return all_passed

def main():
    print("WattBox Outlet Extraction Test")
    print("=" * 35)
    
    if test_outlet_extraction():
        print("\n🎉 All outlet extraction tests passed!")
    else:
        print("\n❌ Some tests failed.")

if __name__ == "__main__":
    main()
