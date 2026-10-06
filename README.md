# Desktop Strata MoE Inference Engine (PRJ-17)

[![Cluster Standard](https://img.shields.io/badge/Homelab-PRJ--17-blue.svg)](https://github.com/TravT/Enterprise_Hub)
[![Architecture](https://img.shields.io/badge/Architecture-ADR--46-green.svg)](https://github.com/TravT/Enterprise_Hub)
[![Engine](https://img.shields.io/badge/Engine-Strata%20v0.1.39-orange.svg)](https://github.com/Niko1221/Strata)
[![Model](https://img.shields.io/badge/Model-Qwen3.8--Flash--Next--Coder-purple.svg)](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF)

High-performance, tiered Mixture-of-Experts (MoE) inference server designed to run **Qwen3.8-Flash-Next Coder** (125B parameters, 12,288 retained experts) on consumer gaming hardware at **52–58 tokens/sec**, integrated directly into the Enterprise Hub cluster GitOps infrastructure.

---

## 1. Executive Summary

This repository codifies the deployment, orchestration, and power lifecycle management of the **Strata inference engine** on the homelab's high-performance desktop workstation (`desktop` / `100.77.169.15`), operating as the cluster's **Tier-3 Frontier MoE Heavy Cognitive Specialist**.

### Hardware Profile:
* **Host Rig**: AMD Ryzen 7 5700X3D (8 cores / 16 threads, 96MB 3D V-Cache)
* **GPU**: NVIDIA GeForce RTX 5070 (12GB GDDR7, 672 GB/s bandwidth)
* **Memory**: 32 GB DDR4-3200 Dual-Channel (~50 GB/s bandwidth)
* **Storage**: PCIe Gen4 NVMe M.2 SSD (>5,000 MB/s sequential read)
* **Operating Systems**: Dual-Boot Windows 11 Pro & Headless Linux via Limine

---

## 2. Collaborative 3-Tier Memory Architecture

Rather than demanding 75GB+ of dedicated VRAM, Strata partitions the model across three physical tiers:

```mermaid
flowchart TD
    subgraph Tier1["Tier 1: GPU VRAM (12GB GDDR7 @ 672 GB/s)"]
        Attn["Base Attention & DeltaNet Mixers (~1.6 GB)"]
        SharedExp["Shared Experts, Router & Output Head (~1.8 GB)"]
        MTPDraft["MTP Speculative Draft Layer (~70 MiB)"]
        KVCache["KV Cache Resident Window (~820 MiB)"]
        HotCache["Hot-Expert Cache (~4,550 Experts, 72-78% Hit Rate)"]
    end

    subgraph Tier2["Tier 2: System RAM (32GB DDR4-3200 @ ~50 GB/s)"]
        ColdExp["Pinned Cold Experts (~7,738 Experts, ~15.2 GB)"]
        KVHistory["KV Streaming History (~13.7 KB/tok, ~1.8 GB at 128K)"]
        CPUWorker["AMD Ryzen 7 5700X3D Parallel AVX2 Compute"]
    end

    subgraph Tier3["Tier 3: PCIe Gen4 NVMe SSD (>5,000 MB/s)"]
        NGramTable["28.8 GB Auxiliary Speculative n-Gram Table (Mmapped)"]
    end

    TokenIn["Token Request"] --> SharedExp
    SharedExp -->|Cache Hit (75%)| HotCache
    SharedExp -->|Cache Miss (25%)| ColdExp
    ColdExp --> CPUWorker
    NGramTable -. "Draft Predictions" .-> MTPDraft
```

---

## 3. Repository Structure

```
desktop-strata-moe/
├── config/
│   ├── strata_config.json.example   # Strata engine settings template
│   └── systemd/
│       └── strata.service           # Native Linux systemd unit
├── nomad/
│   └── strata.nomad                 # Declarative Nomad job specification
├── prompts/
│   └── PRJ-17_AGENT_KICKOFF.md      # Agent kickoff prompt & system directive
├── scripts/
│   ├── benchmark_suite.py           # Multi-context automated benchmark runner
│   ├── limine_config_generator.py   # Limine dual-boot config generator
│   ├── setup_linux.sh               # Headless Linux bootstrap
│   ├── setup_windows.ps1            # Windows 11 PowerShell bootstrap
│   └── setup_windows.bat            # Windows 11 Batch launcher
├── src/
│   ├── __init__.py
│   ├── client.py                    # Python streaming client for Strata API
│   ├── health.py                    # Health check and memory telemetry probe
│   └── power.py                     # WoL, Tuya relay, and S3 suspend manager
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 4. Quickstart Guide

### Option A: Windows 11 (Interactive / Development)
1. Clone the repository into `F:\Strata`:
   ```powershell
   git clone https://github.com/TravT/desktop-strata-moe.git F:\Strata
   cd F:\Strata
   ```
2. Run automated bootstrap:
   ```powershell
   .\scripts\setup_windows.ps1
   ```
3. Launch with optimal 64K context profile:
   ```powershell
   .\START-HERE.bat --family coder --context 65536 --draft-vocab en --low-ram resident --calibrate
   ```

### Option B: Headless Linux (Recommended for Max Performance)
1. Boot into Headless Linux (Omarchy / Arch / Ubuntu):
2. Run automated installer:
   ```bash
   bash scripts/setup_linux.sh
   ```
3. Start systemd service:
   ```bash
   sudo systemctl enable --now strata.service
   ```

---

## 5. API Usage

Strata exposes an **OpenAI-compatible and Anthropic-compatible API** on port `8080`:

```bash
curl http://100.77.169.15:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.8-flash-next-coder",
    "messages": [
      {"role": "user", "content": "Refactor this Python generator for zero-copy memory buffers."}
    ],
    "temperature": 0.2
  }'
```

---

## 6. Benchmarking & Verification

Run the automated benchmark suite to verify throughput across context tiers:

```bash
python3 scripts/benchmark_suite.py --endpoint http://100.77.169.15:8080/v1
```

Target SLAs:
* **4K Prompt TTFT**: $\le 3.0\text{ seconds}$
* **Decode Speed**: $\ge 50.0\text{ tokens/sec}$
* **NVMe Steady-State Disk Reads**: $0\text{ MB}$ (100% in-memory residence)
