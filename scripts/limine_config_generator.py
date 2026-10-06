#!/usr/bin/env python3
"""
Limine Dual-Boot Configuration Generator (PRJ-17 / Step 0)
Generates /boot/limine.conf to boot Headless Linux by default (3s timeout)
while chainloading the Windows Boot Manager on EFI partition.
"""

import os
import sys

DEFAULT_LIMINE_CONF = """# Limine Bootloader Configuration (Homelab Desktop Dual-Boot)
timeout: 3
default_entry: 1

# Entry 1: Headless AI Linux (Autonomous Cluster Worker)
/Omarchy AI Worker (Headless Linux)
    protocol: linux
    kernel_path: boot():/vmlinuz-linux
    cmdline: root=UUID={ROOT_UUID} rw quiet intel_idle.max_cstate=2
    module_path: boot():/initramfs-linux.img

# Entry 2: Windows 11 Pro (Gaming & Desktop Workstation)
/Windows 11 Pro
    protocol: efi_chainload
    image_path: boot():/EFI/Microsoft/Boot/bootmgfw.efi
"""

def generate_conf(root_uuid: str = "REPLACE_WITH_ROOT_UUID") -> str:
    return DEFAULT_LIMINE_CONF.replace("{ROOT_UUID}", root_uuid)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        uuid = sys.argv[1]
    else:
        uuid = "PLACEHOLDER-UUID-CHECK-BLKID"
    print(generate_conf(uuid))
