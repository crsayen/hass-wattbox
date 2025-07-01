"""
WattBox API Client

Main client class for communicating with SnapAV WattBox devices.
"""

import socket
import telnetlib
import time
import logging
from typing import Optional, List, Dict, Any, Union
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from .exceptions import (
    WattBoxError,
    WattBoxConnectionError,
    WattBoxAuthenticationError,
    WattBoxCommandError,
    WattBoxTimeoutError,
    WattBoxResponseError,
)
from .models import (
    WattBoxDevice,
    OutletInfo,
    PowerStatus,
    UPSStatus,
    SystemInfo,
    OutletAction,
    OutletMode,
    parse_outlet_status_response,
    parse_outlet_names_response,
    parse_outlet_power_response,
    parse_power_status_response,
    parse_ups_status_response,
)
from .endpoints import WattBoxEndpoints
from .utils import (
    validate_ip_address,
    validate_port,
    validate_outlet_number,
    format_command,
    is_success_response,
    is_error_response,
    parse_response_line,
    calculate_timeout,
)

logger = logging.getLogger(__name__)


class WattBoxClient:
    """
    Client for communicating with SnapAV WattBox devices via Telnet or SSH.
    
    Supports the Integration Protocol v2.4 for controlling and monitoring
    WattBox power distribution units.
    """
    
    def __init__(
        self,
        host: str,
        port: int = 23,
        username: str = "wattbox",
        password: str = "wattbox",
        timeout: float = 10.0,
        connection_type: str = "telnet"
    ):
        """
        Initialize WattBox client.
        
        Args:
            host: IP address of WattBox device
            port: Port number (23 for Telnet, 22 for SSH)
            username: Authentication username
            password: Authentication password
            timeout: Default command timeout in seconds
            connection_type: "telnet" or "ssh"
        """
        if not validate_ip_address(host):
            raise ValueError(f"Invalid IP address: {host}")
        
        if not validate_port(port):
            raise ValueError(f"Invalid port: {port}")
        
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.connection_type = connection_type.lower()
        
        self._connection: Optional[telnetlib.Telnet] = None
        self._authenticated = False
        self._device_info: Optional[WattBoxDevice] = None
        
        # Cache for device capabilities
        self._outlet_count: Optional[int] = None
        self._model: Optional[str] = None
        self._firmware: Optional[str] = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def connect(self) -> None:
        """Establish connection to WattBox device."""
        try:
            logger.debug(f"Connecting to WattBox at {self.host}:{self.port}")
            
            if self.connection_type == "telnet":
                self._connection = telnetlib.Telnet(self.host, self.port, self.timeout)
            else:
                raise NotImplementedError("SSH connections not yet implemented")
            
            # Authenticate
            self._authenticate()
            
            logger.info(f"Successfully connected to WattBox at {self.host}")
            
        except socket.error as e:
            raise WattBoxConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")
        except Exception as e:
            raise WattBoxConnectionError(f"Unexpected connection error: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from WattBox device."""
        if self._connection:
            try:
                # Send exit command gracefully
                if self._authenticated:
                    self._send_command(WattBoxEndpoints.EXIT)
            except Exception:
                pass  # Ignore errors during graceful exit
            
            try:
                self._connection.close()
            except Exception:
                pass
            
            self._connection = None
            self._authenticated = False
            
            logger.debug(f"Disconnected from WattBox at {self.host}")
    
    def _authenticate(self) -> None:
        """Authenticate with the WattBox device."""
        if not self._connection:
            raise WattBoxConnectionError("Not connected")
        
        try:
            # Wait for login prompt
            response = self._connection.read_until(b"login:", timeout=self.timeout)
            logger.debug(f"Login prompt: {response.decode('utf-8', errors='ignore')}")
            
            # Send username
            self._connection.write((self.username + "\n").encode())
            
            # Wait for password prompt
            response = self._connection.read_until(b"password:", timeout=self.timeout)
            logger.debug(f"Password prompt: {response.decode('utf-8', errors='ignore')}")
            
            # Send password
            self._connection.write((self.password + "\n").encode())
            
            # Check for successful login
            response = self._connection.read_until(b"\n", timeout=self.timeout)
            response_str = response.decode('utf-8', errors='ignore').strip()
            
            if "login:" in response_str.lower():
                raise WattBoxAuthenticationError("Invalid credentials")
            
            self._authenticated = True
            logger.debug("Authentication successful")
            
        except socket.timeout:
            raise WattBoxTimeoutError("Authentication timeout")
        except Exception as e:
            raise WattBoxAuthenticationError(f"Authentication failed: {e}")
    
    def _send_command(self, command: str, timeout: Optional[float] = None) -> str:
        """
        Send a command to the WattBox and return the response.
        
        Args:
            command: Command to send
            timeout: Command-specific timeout
            
        Returns:
            Response from device
        """
        if not self._connection or not self._authenticated:
            raise WattBoxConnectionError("Not connected or authenticated")
        
        timeout = timeout or self.timeout
        formatted_command = format_command(command)
        
        try:
            logger.debug(f"Sending command: {formatted_command.strip()}")
            
            # Send command
            self._connection.write(formatted_command.encode())
            
            # Read response
            response = self._connection.read_until(b"\n", timeout=timeout)
            response_str = response.decode('utf-8', errors='ignore').strip()
            
            logger.debug(f"Received response: {response_str}")
            
            # Check for error response
            if is_error_response(response_str):
                raise WattBoxCommandError(f"Command failed: {response_str}")
            
            return response_str
            
        except socket.timeout:
            raise WattBoxTimeoutError(f"Command timeout: {command}")
        except Exception as e:
            raise WattBoxCommandError(f"Command failed: {e}")
    
    # Device Information Methods
    
    def get_device_info(self, refresh: bool = False) -> WattBoxDevice:
        """Get complete device information."""
        if self._device_info and not refresh:
            return self._device_info
        
        # Get system info
        system_info = self.get_system_info()
        
        # Get outlet information
        outlets = self.get_all_outlets_info()
        
        # Get power status (if supported)
        power_status = None
        try:
            power_status = self.get_power_status()
        except WattBoxCommandError:
            pass  # Not supported on all models
        
        # Get UPS status (if applicable)
        ups_status = None
        ups_connected = self.get_ups_connection_status()
        if ups_connected:
            try:
                ups_status = self.get_ups_status()
            except WattBoxCommandError:
                pass
        
        # Get auto reboot status
        auto_reboot_enabled = self.get_auto_reboot_status()
        
        self._device_info = WattBoxDevice(
            system_info=system_info,
            outlets=outlets,
            power_status=power_status,
            ups_status=ups_status,
            ups_connected=ups_connected,
            auto_reboot_enabled=auto_reboot_enabled
        )
        
        return self._device_info
    
    def get_system_info(self) -> SystemInfo:
        """Get device system information."""
        firmware = self._send_command(WattBoxEndpoints.FIRMWARE)
        hostname = self._send_command(WattBoxEndpoints.HOSTNAME)
        service_tag = self._send_command(WattBoxEndpoints.SERVICE_TAG)
        model = self._send_command(WattBoxEndpoints.MODEL)
        outlet_count_resp = self._send_command(WattBoxEndpoints.OUTLET_COUNT)
        
        # Parse responses
        firmware_val = firmware.split("=")[1] if "=" in firmware else firmware
        hostname_val = hostname.split("=")[1] if "=" in hostname else hostname
        service_tag_val = service_tag.split("=")[1] if "=" in service_tag else service_tag
        model_val = model.split("=")[1] if "=" in model else model
        outlet_count_val = int(outlet_count_resp.split("=")[1]) if "=" in outlet_count_resp else 0
        
        # Cache values
        self._outlet_count = outlet_count_val
        self._model = model_val
        self._firmware = firmware_val
        
        return SystemInfo(
            firmware=firmware_val,
            hostname=hostname_val,
            service_tag=service_tag_val,
            model=model_val,
            outlet_count=outlet_count_val
        )
    
    # Outlet Management Methods
    
    def get_outlet_count(self) -> int:
        """Get number of outlets on device."""
        if self._outlet_count is not None:
            return self._outlet_count
        
        response = self._send_command(WattBoxEndpoints.OUTLET_COUNT)
        count = int(response.split("=")[1]) if "=" in response else 0
        self._outlet_count = count
        return count
    
    def get_outlet_status(self) -> List[bool]:
        """Get status of all outlets."""
        response = self._send_command(WattBoxEndpoints.OUTLET_STATUS)
        return parse_outlet_status_response(response)
    
    def get_outlet_names(self) -> List[str]:
        """Get names of all outlets."""
        response = self._send_command(WattBoxEndpoints.OUTLET_NAMES)
        return parse_outlet_names_response(response)
    
    def get_outlet_power_status(self, outlet: int) -> tuple:
        """Get power status for specific outlet."""
        outlet_count = self.get_outlet_count()
        if not validate_outlet_number(outlet, outlet_count):
            raise ValueError(f"Invalid outlet number: {outlet}")
        
        command = WattBoxEndpoints.outlet_power_status(outlet)
        response = self._send_command(command)
        return parse_outlet_power_response(response)
    
    def get_all_outlets_info(self) -> List[OutletInfo]:
        """Get complete information for all outlets."""
        outlet_count = self.get_outlet_count()
        outlet_statuses = self.get_outlet_status()
        outlet_names = self.get_outlet_names()
        
        outlets = []
        
        for i in range(outlet_count):
            outlet_num = i + 1
            
            # Get basic info
            status = outlet_statuses[i] if i < len(outlet_statuses) else False
            name = outlet_names[i] if i < len(outlet_names) else f"Outlet {outlet_num}"
            
            # Try to get power info (not supported on all models)
            power_watts = None
            current_amps = None
            voltage_volts = None
            
            try:
                _, power, current, voltage = self.get_outlet_power_status(outlet_num)
                power_watts = power
                current_amps = current
                voltage_volts = voltage
            except (WattBoxCommandError, WattBoxResponseError):
                pass  # Not supported on this model
            
            outlet_info = OutletInfo(
                index=outlet_num,
                name=name,
                status=status,
                power_watts=power_watts,
                current_amps=current_amps,
                voltage_volts=voltage_volts
            )
            
            outlets.append(outlet_info)
        
        return outlets
    
    def set_outlet(self, outlet: int, action: Union[str, OutletAction], delay: Optional[int] = None) -> bool:
        """Control an outlet."""
        outlet_count = self.get_outlet_count()
        if outlet != 0 and not validate_outlet_number(outlet, outlet_count):
            raise ValueError(f"Invalid outlet number: {outlet}")
        
        if isinstance(action, OutletAction):
            action = action.value
        
        if action not in {"ON", "OFF", "TOGGLE", "RESET"}:
            raise ValueError(f"Invalid action: {action}")
        
        command = WattBoxEndpoints.outlet_set(outlet, action, delay)
        response = self._send_command(command)
        return is_success_response(response)
    
    def turn_on_outlet(self, outlet: int) -> bool:
        """Turn on specific outlet."""
        return self.set_outlet(outlet, OutletAction.ON)
    
    def turn_off_outlet(self, outlet: int) -> bool:
        """Turn off specific outlet."""
        return self.set_outlet(outlet, OutletAction.OFF)
    
    def toggle_outlet(self, outlet: int) -> bool:
        """Toggle specific outlet."""
        return self.set_outlet(outlet, OutletAction.TOGGLE)
    
    def reset_outlet(self, outlet: int, delay: Optional[int] = None) -> bool:
        """Reset specific outlet."""
        return self.set_outlet(outlet, OutletAction.RESET, delay)
    
    def reset_all_outlets(self, delay: Optional[int] = None) -> bool:
        """Reset all outlets."""
        return self.set_outlet(0, OutletAction.RESET, delay)
    
    # Power Status Methods
    
    def get_power_status(self) -> PowerStatus:
        """Get system power status."""
        response = self._send_command(WattBoxEndpoints.POWER_STATUS)
        return parse_power_status_response(response)
    
    # UPS Methods
    
    def get_ups_connection_status(self) -> bool:
        """Check if UPS is connected."""
        response = self._send_command(WattBoxEndpoints.UPS_CONNECTION)
        status = response.split("=")[1] if "=" in response else "0"
        return bool(int(status))
    
    def get_ups_status(self) -> UPSStatus:
        """Get UPS status information."""
        response = self._send_command(WattBoxEndpoints.UPS_STATUS)
        return parse_ups_status_response(response)
    
    # Auto Reboot Methods
    
    def get_auto_reboot_status(self) -> bool:
        """Get auto reboot status."""
        response = self._send_command(WattBoxEndpoints.AUTO_REBOOT)
        status = response.split("=")[1] if "=" in response else "0"
        return bool(int(status))
    
    def set_auto_reboot(self, enabled: bool) -> bool:
        """Enable or disable auto reboot."""
        command = WattBoxEndpoints.auto_reboot_set(enabled)
        response = self._send_command(command)
        return is_success_response(response)
    
    # System Control Methods
    
    def reboot_device(self) -> bool:
        """Reboot the WattBox device."""
        response = self._send_command(WattBoxEndpoints.REBOOT, timeout=60.0)
        return is_success_response(response)
    
    # Utility Methods
    
    def is_connected(self) -> bool:
        """Check if client is connected and authenticated."""
        return self._connection is not None and self._authenticated
    
    def get_model(self) -> str:
        """Get device model."""
        if self._model is not None:
            return self._model
        
        response = self._send_command(WattBoxEndpoints.MODEL)
        model = response.split("=")[1] if "=" in response else response
        self._model = model
        return model
    
    def get_firmware_version(self) -> str:
        """Get firmware version."""
        if self._firmware is not None:
            return self._firmware
        
        response = self._send_command(WattBoxEndpoints.FIRMWARE)
        firmware = response.split("=")[1] if "=" in response else response
        self._firmware = firmware
        return firmware
    
    def ping(self) -> bool:
        """Test connectivity with the device."""
        try:
            self.get_firmware_version()
            return True
        except Exception:
            return False
