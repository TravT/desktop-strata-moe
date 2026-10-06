"""
Health and Telemetry Probe for Strata MoE Server
Queries /health and /metrics endpoints to inspect VRAM hit rate, RAM blobs, and PCIe share.
"""

from typing import Dict, Any, Optional
import requests


def check_health(server_url: str = "http://100.77.169.15:8080") -> Dict[str, Any]:
    """Probes Strata /health and /metrics endpoints."""
    base = server_url.rstrip("/")
    status_info: Dict[str, Any] = {
        "online": False,
        "health": "unknown",
        "hit_rate": None,
        "pcie_share": None,
        "resident_ram": None,
        "speculative_drafts": None,
    }

    try:
        # Check /health
        h_resp = requests.get(f"{base}/health", timeout=5)
        if h_resp.status_code == 200:
            status_info["online"] = True
            try:
                status_info["health"] = h_resp.json()
            except Exception:
                status_info["health"] = h_resp.text.strip()
    except Exception as e:
        status_info["error"] = str(e)
        return status_info

    # Query metrics
    try:
        m_resp = requests.get(f"{base}/metrics", timeout=5)
        if m_resp.status_code == 200:
            m_data = m_resp.json()
            status_info["hit_rate"] = m_data.get("hit_rate")
            status_info["pcie_share"] = m_data.get("pcie_share")
            status_info["metrics_raw"] = m_data
    except Exception:
        pass

    return status_info


if __name__ == "__main__":
    import pprint
    pprint.pprint(check_health())
