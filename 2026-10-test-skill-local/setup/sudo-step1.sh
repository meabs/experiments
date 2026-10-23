#!/usr/bin/env bash
# Run once with sudo. Moves Ollama from the (CPU-only) snap to the tarball systemd service (ROCm/Vulkan GPU),
# reusing the snap's model store read-only, and installs JDK 21 + Maven.
set -euxo pipefail

# 1. Stop the snap Ollama (keeps it installed; `sudo snap start --enable ollama` undoes this).
snap stop --disable ollama

# 2. systemd override for the tarball Ollama.
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
Environment="OLLAMA_MODELS=/var/snap/ollama/common/models"
Environment="OLLAMA_CONTEXT_LENGTH=65536"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KEEP_ALIVE=30m"
Environment="OLLAMA_NUM_PARALLEL=1"
EOF
usermod -aG render,video ollama
systemctl daemon-reload
systemctl restart ollama.service

# 3. Toolchain.
apt-get update
apt-get install -y openjdk-21-jdk-headless maven
