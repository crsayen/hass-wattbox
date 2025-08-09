from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
import requests
from requests.auth import HTTPBasicAuth


@dataclass
class WattBoxClient:
    restricted_outlets = [0, 1, 2, 3, 5, 6, 7, 8, 11]
    allow_master_control = False
    host: str = '192.168.0.117'
    username: str = "chris"
    password: str = "Assbanana"
    scheme: str = "http"           # devices are typically http
    timeout: float = 5.0
    verify: Union[bool, str] = False  # verify SSL (if using https)

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

    @staticmethod
    def _xml_to_dict(xml_text: str) -> Dict[str, Any]:
        root = ET.fromstring(xml_text)
        result: Dict[str, Any] = {}

        def parse_value(txt: Optional[str]) -> Union[str, list, None]:
            if txt is None:
                return None
            if "," in txt:
                return [piece.strip().strip('"') for piece in txt.split(",")]
            return txt.strip().strip('"')

        for child in root:
            result[child.tag] = parse_value(child.text)
        return result

    def get_status(self) -> Dict[str, Any]:
        r = self._get("/wattbox_info.xml")
        return self._xml_to_dict(r.text)

    def control_raw(self, outlet: int, command: int) -> Dict[str, Any]:
        if outlet in WattBoxClient.restricted_outlets:
            raise ValueError(f'Outlet {outlet} is restricted.')
        if command not in {0, 1, 3, 4, 5}:
            raise ValueError("Invalid command. Use 0(off),1(on),3(reset),4(auto reboot on),5(auto reboot off).")
        r = self._get("/control.cgi", params={"outlet": outlet, "command": command})
        return self._xml_to_dict(r.text)

    # Convenience helpers

    def power_on(self, outlet: int) -> Dict[str, Any]:
        return self.control_raw(outlet, 1)

    def power_off(self, outlet: int) -> Dict[str, Any]:
        return self.control_raw(outlet, 0)

    def reset(self, outlet: int) -> Dict[str, Any]:
        return self.control_raw(outlet, 3)

    def auto_reboot_on(self) -> Dict[str, Any]:
        if WattBoxClient.allow_master_control:
            return self.control_raw(0, 4)

    def auto_reboot_off(self) -> Dict[str, Any]:
        if WattBoxClient.allow_master_control:
            return self.control_raw(0, 5)
