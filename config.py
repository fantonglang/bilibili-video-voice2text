"""
Configuration module for loading environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Silicon Flow API Configuration
SILICON_FLOW_API_KEY = os.getenv("SILICON_FLOW_API_KEY", "")
VOICE_RECOGNITION_MODEL = os.getenv("VOICE_RECOGNITION_MODEL", "TeleAI/TeleSpeechASR")
SILICON_FLOW_API_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"

# Directory Configuration
VIDEO_DIR = "bilibili_video"
AUDIO_DIR = "audio"
AUDIO_CONV_DIR = os.path.join(AUDIO_DIR, "conv")
AUDIO_SLICE_DIR = os.path.join(AUDIO_DIR, "slice")
OUTPUT_DIR = "outputs"

# Audio Slicing Configuration (default 45 seconds per slice)
SLICE_LENGTH_MS = 45000
