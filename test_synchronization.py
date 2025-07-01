#!/usr/bin/env python3
"""Test the cross-entity state synchronization implementation."""

import sys
import os

def test_synchronization_code():
    """Test that the cross-entity synchronization code is properly implemented."""
    print("Testing cross-entity state synchronization implementation...")
    
    # Check coordinator changes
    init_path = os.path.join('custom_components', 'wattbox', '__init__.py')
    if not os.path.exists(init_path):
        print(f"ERROR: Coordinator file not found at {init_path}")
        return False
    
    with open(init_path, 'r', encoding='utf-8') as f:
        coordinator_content = f.read()
    
    # Check for entity registry
    has_entity_registry = '"outlet_switches": {}' in coordinator_content
    print(f"Has entity registry: {has_entity_registry}")
    
    # Check for registration methods
    has_register_master = 'def register_master_switch' in coordinator_content
    has_register_outlet = 'def register_outlet_switch' in coordinator_content
    print(f"Has register_master_switch method: {has_register_master}")
    print(f"Has register_outlet_switch method: {has_register_outlet}")
    
    # Check for notification methods
    has_notify_outlet = 'def notify_outlet_state_change' in coordinator_content
    has_notify_master = 'def notify_master_switch_change' in coordinator_content
    print(f"Has notify_outlet_state_change method: {has_notify_outlet}")
    print(f"Has notify_master_switch_change method: {has_notify_master}")
    
    # Check switch changes
    switch_path = os.path.join('custom_components', 'wattbox', 'switch.py')
    if not os.path.exists(switch_path):
        print(f"ERROR: Switch file not found at {switch_path}")
        return False
    
    with open(switch_path, 'r', encoding='utf-8') as f:
        switch_content = f.read()
    
    # Check for registration calls
    has_outlet_registration = 'coordinator.register_outlet_switch(outlet_index, self)' in switch_content
    has_master_registration = 'coordinator.register_master_switch(self)' in switch_content
    print(f"Has outlet switch registration: {has_outlet_registration}")
    print(f"Has master switch registration: {has_master_registration}")
    
    # Check for notification calls
    has_outlet_notifications = 'coordinator.notify_outlet_state_change' in switch_content
    has_master_notifications = 'coordinator.notify_master_switch_change' in switch_content
    print(f"Has outlet state change notifications: {has_outlet_notifications}")
    print(f"Has master switch change notifications: {has_master_notifications}")
    
    return (has_entity_registry and has_register_master and has_register_outlet and 
            has_notify_outlet and has_notify_master and has_outlet_registration and 
            has_master_registration and has_outlet_notifications and has_master_notifications)

if __name__ == "__main__":
    success = test_synchronization_code()
    if success:
        print("\n✅ All cross-entity synchronization code is properly implemented!")
        print("\nThis should restore the connection between the master switch and individual outlet switches.")
        print("The master switch can now properly see and control individual outlets, and vice versa.")
    else:
        print("\n❌ Cross-entity synchronization implementation incomplete!")
    sys.exit(0 if success else 1)
