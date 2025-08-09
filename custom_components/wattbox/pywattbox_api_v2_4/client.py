"""
WattBox API Client

Main client class for communicating with SnapAV WattBox devices.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Union
import requests
from requests.auth import HTTPBasicAuth

import logging
import threading
from typing import Optional, List, Dict, Any, Union

from .models import (
    WattBoxDevice,
    OutletInfo,
    PowerStatus,
    UPSStatus,
    SystemInfo,
    OutletAction,
    OutletMode,
)
from .utils import (
    validate_ip_address,
    validate_port,
)

logger = logging.getLogger(__name__)


class WattBoxClient:
    def __init__(
        self,
        host: str,
        port: int = 23,
        username: str = "wattbox",
        password: str = "wattbox",
        timeout: float = 10.0,
        scheme: str = "http",
        verify: Union[bool, str] = False  # verify SSL (if using https)
    ):
        if not validate_ip_address(host):
            raise ValueError(f"Invalid IP address: {host}")
        
        if not validate_port(port):
            raise ValueError(f"Invalid port: {port}")
        
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.scheme = scheme
        self.verify = verify
        
        self._device_info: Optional[WattBoxDevice] = None
        
        # Thread lock to prevent simultaneous commands
        self._command_lock = threading.RLock()
        
        # Cache for device capabilities
        self._outlet_count: Optional[int] = None
        self._model: Optional[str] = None
        self._firmware: Optional[str] = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = requests.get(
            url,
            params=params,
            timeout=self.timeout,
            auth=HTTPBasicAuth(self.username, self.password),
            headers={
                # Not strictly required, but mirrors examples in the doc
                "Connection": "keep-alive",
                "Keep-Alive": "300",
                "User-Agent": "WattBoxClient/1.0",
            },
            verify=self.verify,
        )
        resp.raise_for_status()
        return resp
    
    def _control_raw(self, outlet: int, command: int) -> Dict[str, Any]:
        if command not in {0, 1, 3, 4, 5}:
            raise ValueError("Invalid command. Use 0(off),1(on),3(reset),4(auto reboot on),5(auto reboot off).")
        r = self._get("/control.cgi", params={"outlet": outlet, "command": command})
        return self._xml_to_dict(r.text)

    def _parse_numeric_value(self, value: str, factor = 0.1):
        i = int(value)
        return i * factor

    # Device Information Methods
    
    def get_device_info(self, refresh: bool = False) -> WattBoxDevice:
        """
        Get complete device information.
        
        Args:
            refresh: Force refresh of cached data
            include_outlet_power: Include individual outlet power data (may take longer)
        """
        if self._device_info and not refresh:
            return self._device_info
        
        logger.debug("Starting device info collection")
        
        info_response = self._get("/wattbox_info.xml")

        system_info = SystemInfo(
            "fwv",
            info_response.get('host_name'),
            info_response.get('serial_number'),
            info_response.get('hardware_version'),
            12
        )

        o_names = info_response.get('outlet_name')
        o_status = [x == "1" for x in info_response.get('outlet_status')]
        o_method = info_response.get('outlet_method')

        outlets = [
            OutletInfo(
                i + 1,
                name,
                status,
                mode=OutletMode(int(method) - 1)
            )
            for i, (name, status, method) in enumerate(tuple(zip(o_names, o_status, o_method)))
        ]

        power_status = PowerStatus(
            self._parse_numeric_value(info_response.get('power_value')),
            self._parse_numeric_value(info_response.get('power_value')),
            self._parse_numeric_value(info_response.get('voltage_value')),
            True
        )

        self._device_info = WattBoxDevice(
            system_info=system_info,
            outlets=outlets,
            power_status=power_status,
            ups_status=UPSStatus(0,0,"",False,0,False,False),
            ups_connected=False,
            auto_reboot_enabled=info_response.get('auto_reboot') == "1"
        )
        
        logger.debug("Device info collection complete")
        return self._device_info
    
    def get_system_info(self):
        return self.get_device_info(refresh=True).system_info

    # Outlet Management Methods
    
    def get_outlet_count(self) -> int:
        return 12
    
    def get_outlet_status(self) -> List[bool]:
        return list([o.status for o in self.get_device_info(refresh=True).outlets])
    
    def get_outlet_names(self) -> List[str]:
        return list([o.name for o in self.get_device_info(refresh=True).outlets])
    
    def get_all_outlets_info(self, include_power_data: bool = False) -> List[OutletInfo]:
        return self.get_device_info(True).outlets
    
    def set_outlet(self, outlet: int, action: Union[str, OutletAction], delay: Optional[int] = None) -> bool:
        if action == OutletAction.RESET:
            self._control_raw(outlet, 3)
            return True
        
        state = action == OutletAction.ON
        if action == OutletAction.TOGGLE:
            state = not self.get_device_info(True).outlets[outlet].status

        self._control_raw(outlet, int(state))
        return True
    
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
    
    def get_power_status(self) -> Optional[PowerStatus]:
        return self.get_device_info(True).power_status
    
    # Auto Reboot Methods
    
    def get_auto_reboot_status(self) -> bool:
        self.get_device_info(True).auto_reboot_enabled
    
    def set_auto_reboot(self, enabled: bool) -> bool:
        self._control_raw(0, 5 - int(enabled))
        return True
