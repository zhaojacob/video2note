"""
Test script for Doubao API configuration
"""
import os
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from analysis.doubao_client import DoubaoClient
from config.api_config import get_doubao_api_key


def test_doubao_client():
    """Test Doubao client with a simple image analysis"""
    print("=" * 60)
    print("Testing Doubao Client Configuration")
    print("=" * 60)

    # Check API key
    try:
        api_key = get_doubao_api_key()
        print(f"[OK] API Key loaded: {api_key[:20]}...")
    except ValueError as e:
        print(f"[X] API Key Error: {e}")
        return

    # Initialize client
    try:
        client = DoubaoClient()
        print(f"[OK] Doubao client initialized")
        print(f"  Model: {client.model}")
        print(f"  Base URL: {client.base_url}")
    except Exception as e:
        print(f"[X] Client initialization failed: {e}")
        return

    # Check model info
    model_info = client.get_model_info()
    print(f"\nModel Info:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Configuration test complete!")
    print("=" * 60)

    print("\nTo test with a real image, create a test image and run:")
    print("  python test_doubao.py --image <path_to_image>")


if __name__ == "__main__":
    test_doubao_client()
