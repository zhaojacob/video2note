"""Test Whisper model download"""
from faster_whisper import WhisperModel

print('Testing Whisper with tiny model...')
print('This will download ~40MB - much faster than medium (1.5GB)')
print('Loading...')

model = WhisperModel('tiny', device='cuda', compute_type='int8_float16')
print('Success! Model loaded')
print(f'Model info: {model}')
