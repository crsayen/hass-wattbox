#!/usr/bin/env python3
"""Test script to verify threading lock in WattBox client."""

import sys
import os

def test_client_code():
    """Test that the WattBox client code has threading support."""
    print("Testing WattBox client code for threading support...")
    
    # Read the client file and check for threading imports and lock usage
    client_path = os.path.join('custom_components', 'wattbox', 'pywattbox_api_v2_4', 'client.py')
    
    if not os.path.exists(client_path):
        print(f"ERROR: Client file not found at {client_path}")
        return False
    
    with open(client_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for threading import
    has_threading_import = 'import threading' in content
    print(f"Has threading import: {has_threading_import}")
    
    # Check for lock initialization
    has_lock_init = '_command_lock = threading.RLock()' in content
    print(f"Has command lock initialization: {has_lock_init}")
    
    # Check for lock usage in _send_command
    has_lock_usage = 'with self._command_lock:' in content
    print(f"Has command lock usage: {has_lock_usage}")
    
    # Check for asyncio import in switch.py
    switch_path = os.path.join('custom_components', 'wattbox', 'switch.py')
    if os.path.exists(switch_path):
        with open(switch_path, 'r', encoding='utf-8') as f:
            switch_content = f.read()
        
        has_asyncio_import = 'import asyncio' in switch_content
        has_delay = 'await asyncio.sleep(0.5)' in switch_content
        print(f"Switch has asyncio import: {has_asyncio_import}")
        print(f"Switch has delay after commands: {has_delay}")
    
    return has_threading_import and has_lock_init and has_lock_usage

if __name__ == "__main__":
    success = test_client_code()
    if success:
        print("\n✅ All threading code checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Threading code checks failed!")
        sys.exit(1)
