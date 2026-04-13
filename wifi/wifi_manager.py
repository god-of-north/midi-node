import subprocess
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class WifiConnectionInfo:
    ssid: Optional[str]
    state: str
    interface: str
    signal_strength: Optional[str] = None

class WifiManager:
    def __init__(self, interface: str = "wlan0"):
        self.interface = interface

    def _run_command(self, command: list[str]) -> str:
        """Helper to run system commands and return output."""
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return e.stderr.strip()

    def is_connected(self) -> bool:
        """Returns True if there is an active internet/network connection."""
        status = self._run_command(["nmcli", "-t", "-f", "STATE", "g"])
        return "connected" in status

    def active_connection(self) -> Optional[WifiConnectionInfo]:
        """Returns data class with current connection details."""
        cmd = ["nmcli", "-t", "-f", "ACTIVE,SSID,STATE,DEVICE,SIGNAL", "dev", "wifi"]
        output = self._run_command(cmd)
        
        for line in output.split('\n'):
            if line.startswith("yes"):
                parts = line.split(':')
                return WifiConnectionInfo(
                    ssid=parts[1],
                    state=parts[2],
                    interface=parts[3],
                    signal_strength=f"{parts[4]}%"
                )
        return None

    def connect(self, ssid: str, password: str) -> str:
        """Connects to a new WiFi network and saves the profile for auto-reconnect."""
        # This command creates a persistent profile that the OS will manage
        return self._run_command([
            "nmcli", "device", "wifi", "connect", ssid, "password", password
        ])

    def reconnect(self) -> str:
        """Attempts to bring up the interface using the last known profile."""
        return self._run_command(["nmcli", "device", "up", self.interface])

    def disconnect(self) -> str:
        """Disables the WiFi interface."""
        return self._run_command(["nmcli", "device", "disconnect", self.interface])

# --- Example Usage ---
if __name__ == "__main__":
    wifi = WifiManager()
    
    print(f"Connected: {wifi.is_connected()}")
    
    active = wifi.active_connection()
    if active:
        print(f"Current SSID: {active.ssid} (Signal: {active.signal_strength})")
    
    # To connect to a new network:
    print(wifi.connect("Mordor", "88793788"))

