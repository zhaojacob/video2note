"""Download Whisper medium model"""
import time
from faster_whisper import WhisperModel

print("=" * 60)
print("DOWNLOADING Whisper Medium Model")
print("=" * 60)
print("Model size: ~1.5GB")
print("This will take 5-10 minutes depending on your network speed")
print("Please be patient...")
print("=" * 60)
print()

print("Starting download...")
start_time = time.time()

try:
    model = WhisperModel(
        'medium',
        device='cuda',
        compute_type='int8_float16',
        download_root='F:/anaconda_learning/video_note_system/output/transcripts/models'
    )

    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print(f"SUCCESS! Model loaded in {elapsed:.1f} seconds")
    print("=" * 60)
    print()
    print("✓ Medium model is now ready to use!")
    print()
    print("You can now run:")
    print('  python main.py "<url>" --whisper-model medium')

except Exception as e:
    print()
    print("=" * 60)
    print(f"ERROR: {e}")
    print("=" * 60)
    print()
    print("Troubleshooting:")
    print("1. Check your internet connection")
    print("2. Try using a smaller model: --whisper-model small")
    print("3. Use CPU mode: --whisper-device cpu")
