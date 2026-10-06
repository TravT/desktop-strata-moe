# PRJ-17 Agent Kickoff & Execution Directive: Desktop Strata MoE Engine

> **Project Code**: `PRJ-17`  
> **Repository**: [`TravT/desktop-strata-moe`](https://github.com/TravT/desktop-strata-moe)  
> **Cluster Role**: Tier-3 Frontier Mixture-of-Experts (MoE) Heavy Cognitive Engine  
> **Hardware Target**: Desktop Workstation (`desktop` / `100.77.169.15`), AMD Ryzen 7 5700X3D (8c/16t, 96MB 3D V-Cache), 32 GB DDR4-3200, NVIDIA GeForce RTX 5070 (12GB GDDR7), PCIe Gen4 NVMe M.2 SSD  
> **Governing Standards**: [PRJ-17 Specification](file:///home/tlima/Enterprise_Hub/docs/wiki/projects/PRJ-17-Strata-Desktop-Tiered-MoE-and-Cluster-Specialist-Mesh.md) & [ADR-46](file:///home/tlima/Enterprise_Hub/docs/wiki/adrs/ADR-46-Tiered-MoE-Inference-and-Heterogeneous-Specialist-Mesh.md)

---

## 1. High-Level Mission & Invariants

You are operating as an autonomous systems engineer and cluster integration agent for the Homelab. Your mission is to bootstrap, optimize, and orchestrate the **Strata tiered MoE inference engine** on the desktop rig to serve **Qwen3.8-Flash-Next Coder** (125B MoE, 12,288 experts) at **52–58 tokens/sec** over the Tailscale mesh (`http://100.77.169.15:8080/v1`).

### Core Cluster Invariants (Non-Negotiable)
1. **Memory Budget Invariant**: On a 32 GB physical RAM machine, **never attempt to run the unpruned 125B model under Windows 11 without low-RAM resident guarantees**. Target the **pruned Coder profile (`--family coder`)** to ensure zero SSD paging during decode.
2. **Tailscale & Ingress Invariant**: Strata exposes its API strictly on `0.0.0.0:8080` (accessible over LAN `192.168.0.220` and Tailnet `100.77.169.15`). Zero open public IPv4 ports.
3. **Power Lifecycle Invariant**: The desktop consumes 60W–150W under load versus <2W in S3 standby. All automation must wake the node via WoL/Tuya relay (`desktop_gpu_runner.py`) and return it to S3 sleep when idle.
4. **GitOps Invariant**: Do not create ad-hoc snowflake configurations. Code and scripts reside in `dev/desktop-strata-moe/` and synchronize to `TravT/desktop-strata-moe`.

---

## 2. Technical Memory Blueprint (Coder Profile)

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: RTX 5070 12GB GDDR7 VRAM (672 GB/s Bandwidth)                 │
│ ├─ Base Attention & DeltaNet Mixers:         ~1,600 MiB                │
│ ├─ Shared Experts, Router & Output Head:     ~1,800 MiB                │
│ ├─ MTP Speculative Draft Layer (--draft-vocab en): ~70 MiB             │
│ ├─ 8-Bit KV Cache (32K Resident Window):       ~820 MiB                │
│ └─ Hot-Expert Cache (Holds ~4,550 Experts):  ~6,500 MiB (72% Hit Rate) │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: System RAM (32GB DDR4-3200 @ ~50 GB/s Dual-Channel)            │
│ ├─ OS & Background Processes:                ~1,000 MiB (Linux) / ~6GB │
│ ├─ Strata Pinned Cold Experts (~7,738 Exp):  ~15,200 MiB               │
│ ├─ KV Streaming History (~13.7 KB/tok):      ~1,795 MiB (128K context) │
│ └─ Unallocated Safety Cushion:               ~10,000 MiB (Linux)       │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: PCIe Gen4 NVMe M.2 SSD (>5,000 MB/s Sequential)               │
│ └─ Auxiliary 28.8 GB n-Gram Speculative Table (Mmapped)                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-Step Execution Playbook

### Step 0: Headless Linux Dual-Boot & Storage Rebalancing (Recommended Path)
* Shrink Windows NVMe partition by **~100 GB**.
* Install Headless Linux (Omarchy / Arch minimal) utilizing the **Limine bootloader**.
* Configure `/boot/limine.conf` with a 3-second timeout defaulting to Linux, chainloading Windows Boot Manager (`bootmgfw.efi`).
* Mount existing NTFS partition (`F:\OllamaModels`) in `/etc/fstab` using `ntfs3` at `/mnt/models` to share weights with zero duplicated storage.
* Verify memory reclaim: Confirm idle RAM $\le$ 1.1 GB and 100% of 12,288 MiB VRAM available to CUDA.

### Step 1: Bootstrap Strata Engine
* Clone `Niko1221/Strata` to `/opt/strata` (Linux) or `F:\Strata` (Windows).
* Download `Qwen3.8-Flash-Next-GSQ-RCO-Coder-GGUF` shard 1 and shared shard 2.
* Execute calibration to tune `--pool-workers` (8 threads for Zen 3 physical cores) and `--pcie-frac`.
* Launch test server:
  ```bash
  # Linux launch command
  ./setup.sh --family coder --context 65536 --draft-vocab en --low-ram resident --calibrate
  
  # Windows launch command
  .\START-HERE.bat --family coder --context 65536 --draft-vocab en --low-ram resident --calibrate
  ```

### Step 2: Service Automation & Power Hooks
* **Linux**: Deploy `config/systemd/strata.service` to `/etc/systemd/system/` with `CAP_IPC_LOCK` enabled.
* **Windows Fallback**: Configure Task Scheduler with "Run with highest privileges" (`SeLockMemoryPrivilege`) and "Priority: Normal".
* Connect `src/power.py` to Home Assistant entity `switch.pc_switch` and local subnet broadcast for Wake-on-LAN.

### Step 3: Cluster Integration & Benchmarking
* Run `python3 scripts/benchmark_suite.py --endpoint http://100.77.169.15:8080/v1`.
* Confirm:
  - TTFT $\le$ 3.0s on 4K prompt.
  - Decode speed $\ge$ 50 tok/s.
  - Steady-state SSD reads = 0 MB during token generation.
* Update Open WebUI (`nomad_jobs/open-webui.nomad`) and Antigravity `homelab-gpu` MCP server to route heavy refactoring calls to the Strata endpoint.

---

## 4. Verification Checkpoint
Before declaring completion, verify:
- [ ] Strata API returns HTTP 200 on `http://100.77.169.15:8080/health`.
- [ ] Decode speed benchmark logged in `bench/results/`.
- [ ] Repository committed and pushed to `git@github.com:TravT/desktop-strata-moe.git`.
- [ ] Homelab wiki (`docs/wiki/projects/PRJ-17-*.md`) updated with live benchmark metrics.
