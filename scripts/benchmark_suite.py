#!/usr/bin/env python3
"""
Automated Multi-Context Benchmark Suite for Strata Desktop MoE (PRJ-17)
Measures TTFT (Time to First Token), prompt speed, and decode throughput.
"""

import argparse
import json
import time
import sys
import requests

PROMPTS = {
    "4K": "Write a complete Python asyncio TCP server with connection pooling, graceful SIGTERM shutdown, and exponential backoff retry. " * 35,
    "32K": "Analyze the following system architecture and refactor for zero-copy memory buffers. " * 280,
    "64K": "Audit this distributed system specification for split-brain and network partition race conditions. " * 560,
}


def run_benchmark(endpoint: str, model: str = "qwen3.8-flash-next-coder"):
    print(f"=== Running Strata MoE Benchmark Suite on {endpoint} ===")
    results = {}

    for name, prompt_text in PROMPTS.items():
        print(f"\n[+] Testing Context Tier: {name} (~{len(prompt_text)//4} tokens)...")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt_text}],
            "max_tokens": 128,
            "temperature": 0.1,
            "stream": True,
        }

        t_start = time.time()
        t_first_token = None
        token_count = 0

        try:
            with requests.post(f"{endpoint}/chat/completions", json=payload, stream=True, timeout=180) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: "):
                        if line_str[6:] == "[DONE]":
                            break
                        if t_first_token is None:
                            t_first_token = time.time()
                        token_count += 1
        except Exception as e:
            print(f"[-] Error running {name} benchmark: {e}")
            continue

        t_end = time.time()
        ttft = t_first_token - t_start if t_first_token else 0
        gen_time = t_end - t_first_token if t_first_token else 0
        tok_s = token_count / gen_time if gen_time > 0 and token_count > 0 else 0

        print(f"    - TTFT (Prompt Eval): {ttft:.2f}s")
        print(f"    - Output Speed:       {tok_s:.1f} tokens/s ({token_count} tokens in {gen_time:.2f}s)")

        results[name] = {
            "ttft_s": round(ttft, 2),
            "output_tok_s": round(tok_s, 1),
            "tokens_generated": token_count,
        }

    print("\n=== Benchmark Summary ===")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://100.77.169.15:8080/v1")
    parser.add_argument("--model", default="qwen3.8-flash-next-coder")
    args = parser.parse_args()

    run_benchmark(args.endpoint, args.model)
