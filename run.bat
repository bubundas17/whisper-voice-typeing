@echo off
echo Updating from git...
git pull

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/Updating dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Check if CUDA is available and install PyTorch with CUDA support
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo CUDA GPU detected, installing PyTorch with CUDA support...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
) else (
    echo No CUDA GPU detected, installing CPU-only PyTorch...
    pip install torch torchvision torchaudio
)

echo Starting Whisper SST...
python run.py

pause
