#!/usr/bin/env bash
#
# Copyright 2021 Canonical Ltd.
# Written by:
#   Dann Frazier <dann.frazier@canonical.com>
#   Taihsiang Ho <taihsiang.ho@canonical.com>

set -e

source nvidia-module-lib

sudo service nvidia-fabricmanager stop || /bin/true

# Some examples like:
# ubuntu@hot-koala:~$ apt-cache search --names-only "^linux-modules-nvidia-[0-9]+-server-$(uname -r)$"
# linux-modules-nvidia-418-server-5.4.0-90-generic - Linux kernel nvidia modules for version 5.4.0-90
# linux-modules-nvidia-450-server-5.4.0-90-generic - Linux kernel nvidia modules for version 5.4.0-90
# linux-modules-nvidia-460-server-5.4.0-90-generic - Linux kernel nvidia modules for version 5.4.0-90
# linux-modules-nvidia-470-server-5.4.0-90-generic - Linux kernel nvidia modules for version 5.4.0-90
for drvpkg in $(apt-cache search --names-only "^linux-modules-nvidia-[0-9]+-server-$(uname -r)$" | cut -d' ' -f1); do
    if ! pkg_compatible_with_platform "$drvpkg"; then
        echo "INFO: Skipping $drvpkg on $platform" 1>&2
        continue
    fi
    uninstall_all_nvidia_mod_pkgs
    recursive_remove_module nvidia
    sudo dmesg -c > /dev/null
    sudo apt install -y "$drvpkg"
    sudo modprobe nvidia
    if sudo dmesg | grep "NVRM: loading NVIDIA UNIX"; then
        continue
    fi
    echo "ERROR: Failed to detect nvidia driver initialization message in dmesg"
    exit 1
done
