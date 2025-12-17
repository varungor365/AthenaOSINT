#!/bin/bash
# AthenaOSINT GPU Acceleration Setup Script
# Installs NVIDIA Drivers, CUDA, and TensorRT for AI Model Acceleration
# Run this on your GPU-enabled Droplet (Ubuntu 20.04/22.04)

set -e

echo "🚀 Starting NVIDIA TensorRT Setup..."

# 1. Update System
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Essentials
sudo apt-get install -y build-essential python3-dev python3-pip git wget

# 3. Add NVIDIA Package Repositories
echo "📦 Adding NVIDIA Repositories..."
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda-repo-ubuntu2204-12-1-local_12.1.0-530.30.02-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-1-local_12.1.0-530.30.02-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-12-1-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update

# 4. Install CUDA Toolkit
echo "🔌 Installing CUDA Toolkit (This may take a while)..."
sudo apt-get install -y cuda

# 5. Install TensorRT (Placeholder - requires NVIDIA Developer login usually, attempting generic install)
# For automated/open installs, we focus on the python integration via nvidia-pyindex
echo "🧠 Installing TensorRT Python Bindings..."
pip3 install nvidia-pyindex
pip3 install nvidia-tensorrt

# 6. Install Torch with CUDA support
echo "🔥 Installing PyTorch with CUDA support..."
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo "✅ GPU Setup Complete! Please reboot your droplet."
echo "   Verify installation with: nvidia-smi"
