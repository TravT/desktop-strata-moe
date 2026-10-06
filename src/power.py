"""
Desktop GPU & MoE Node Power Lifecycle Manager
Integrates Wake-on-LAN, Home Assistant relay pulse, and S3 sleep via SSH.
"""

import socket
import subprocess
import sys
import time
from typing import Optional
import requests

DESKTOP_MAC = "3c:7c:3f:78:9b:72"
DESKTOP_LAN_IP = "192.168.0.220"
DESKTOP_TAILSCALE_IP = "100.77.169.15"
DESKTOP_SSH_HOST = "desktop"
HOMEASSISTANT_URL = "http://127.0.0.1:8123"
PC_SWITCH_ENTITY_ID = "switch.pc_switch"


def send_wol_packet(mac: str = DESKTOP_MAC, broadcast: str = "192.168.0.255", port: int = 9) -> bool:
    """Dispatches a UDP Wake-on-LAN magic packet."""
    clean_mac = mac.replace(":", "").replace("-", "")
    if len(clean_mac) != 12:
        return False
    packet = bytes.fromhex("FF" * 6 + clean_mac * 16)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.sendto(packet, (broadcast, port))
            return True
    except Exception as e:
        print(f"WoL broadcast failed: {e}", file=sys.stderr)
        return False


def is_node_online(host: str = DESKTOP_TAILSCALE_IP, port: int = 8080, timeout: float = 2.0) -> bool:
    """Tests if the Strata API port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def suspend_node(ssh_host: str = DESKTOP_SSH_HOST) -> bool:
    """Puts the desktop node into low-power S3 sleep over SSH."""
    cmd = ["ssh", "-o", "ConnectTimeout=5", ssh_host, "systemctl suspend || rundll32.exe powrprof.dll,SetSuspendState 0,1,0"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return res.returncode == 0
    except Exception as e:
        print(f"Suspend failed: {e}", file=sys.stderr)
        return False
