#!/bin/bash

# Make the script executable
chmod +x "$0"

echo "Updating from git..."
git pull

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/Updating dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Check if CUDA is available
if command -v nvidia-smi &> /dev/null; then
    echo "CUDA GPU detected, installing PyTorch with CUDA support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    echo "No CUDA GPU detected, installing CPU-only PyTorch..."
    pip install torch torchvision torchaudio
fi

echo "Starting Whisper SST..."
python run.py
