"""
Strata API Client with Telemetry and Speed Measurement
Connects to the desktop Strata MoE server over LAN or Tailscale.
"""

import json
import time
from typing import Generator, Dict, Any, List, Optional
import requests


class StrataClient:
    def __init__(self, base_url: str = "http://100.77.169.15:8080/v1", model: str = "qwen3.8-flash-next-coder"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat_complete(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Executes a standard non-streaming or streaming chat completion."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        t_start = time.time()
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        t_elapsed = time.time() - t_start

        data = resp.json()
        usage = data.get("usage", {})
        completion_tokens = usage.get("completion_tokens", 0)
        tok_s = completion_tokens / t_elapsed if t_elapsed > 0 and completion_tokens > 0 else 0.0

        data["_telemetry"] = {
            "elapsed_s": round(t_elapsed, 3),
            "speed_tok_s": round(tok_s, 1),
        }
        return data

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> Generator[str, None, None]:
        """Streams tokens from Strata server with real-time yielding."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        with requests.post(url, json=payload, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    content = line_str[6:]
                    if content == "[DONE]":
                        break
                    try:
                        chunk = json.loads(content)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue
