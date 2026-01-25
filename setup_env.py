"""
Setup script for video note generation system
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run command and print output"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    if result.returncode != 0:
        print(f"⚠ Command failed with code {result.returncode}")
    return result.returncode == 0


def main():
    """Setup video note system"""
    print("Video Note Generation System - Setup")
    print("=" * 60)

    # Step 1: Create conda environment
    print("\nStep 1: Create conda environment 'video_note'")
    run_command(
        "conda create -n video_note python=3.11 -y",
        "Creating environment..."
    )

    # Step 2: Install PyTorch
    print("\nStep 2: Install PyTorch with CUDA support")
    print("Choose CUDA version:")
    print("  1. CUDA 12.1 (recommended for most modern GPUs)")
    print("  2. CUDA 11.8 (for older GPUs)")
    print("  3. CPU-only (no GPU)")

    choice = input("\nEnter choice (1/2/3) [default: 1]: ").strip() or "1"

    if choice == "1":
        cmd = "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
    elif choice == "2":
        cmd = "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
    else:
        cmd = "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu"

    # Activate environment and install
    full_cmd = f"conda activate video_note && {cmd}"
    run_command(full_cmd, "Installing PyTorch...")

    # Step 3: Install dependencies
    print("\nStep 3: Install Python dependencies")
    run_command(
        "conda activate video_note && pip install -r requirements.txt",
        "Installing packages..."
    )

    # Step 4: Setup API keys
    print("\nStep 4: Configure API keys")
    run_command(
        "conda activate video_note && python main.py --setup",
        "Running setup..."
    )

    # Step 5: Test GPU
    print("\nStep 5: Check GPU availability")
    run_command(
        "conda activate video_note && python main.py --check-gpu",
        "Checking GPU..."
    )

    print("\n" + "="*60)
    print("Setup complete!")
    print("="*60)
    print("\nTo use the system:")
    print("  1. Activate environment: conda activate video_note")
    print("  2. Edit .env file with your API keys")
    print("  3. Run: python main.py <video_url>")
    print("\nFor help: python main.py --help")


if __name__ == "__main__":
    main()
