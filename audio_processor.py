"""
Audio processing module for extracting audio from video and slicing.
Uses moviepy for extraction and pydub for slicing.
"""
import os
import subprocess
import time
import uuid
from moviepy import VideoFileClip
from pydub import AudioSegment
from config import (
    AUDIO_CONV_DIR,
    AUDIO_SLICE_DIR,
    SLICE_LENGTH_MS
)


def check_video_integrity(file_path: str) -> bool:
    """
    Verify video file integrity using FFmpeg.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        True if video is valid, False otherwise
    """
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", file_path, "-f", "null", "-"],
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.stderr:
        print(f"[AudioProcessor] Video may be corrupted: {file_path}")
        print(f"[AudioProcessor] FFmpeg error: {result.stderr}")
        return False
    
    return True


def extract_audio_from_video(video_path: str, target_name: str = None) -> str:
    """
    Extract audio from video file and save as MP3.
    
    Args:
        video_path: Path to the video file
        target_name: Optional name for the output audio file
        
    Returns:
        Path to the extracted audio file
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not check_video_integrity(video_path):
        raise ValueError(f"Video file is corrupted: {video_path}")
    
    # Create output directory
    os.makedirs(AUDIO_CONV_DIR, exist_ok=True)
    
    # Generate output name if not provided
    if target_name is None:
        target_name = time.strftime("%Y%m%d%H%M%S")
    
    output_path = os.path.join(AUDIO_CONV_DIR, f"{target_name}.mp3")
    
    # Extract audio using moviepy
    print(f"[AudioProcessor] Extracting audio from: {video_path}")
    clip = VideoFileClip(video_path)
    audio = clip.audio
    audio.write_audiofile(output_path, logger=None)
    clip.close()
    
    print(f"[AudioProcessor] Audio saved to: {output_path}")
    return output_path


def slice_audio(
    audio_path: str,
    folder_name: str,
    slice_length_ms: int = SLICE_LENGTH_MS
) -> str:
    """
    Slice audio file into smaller chunks.
    
    Args:
        audio_path: Path to the audio file
        folder_name: Name of the folder to save slices
        slice_length_ms: Length of each slice in milliseconds
        
    Returns:
        Path to the directory containing slices
    """
    # Load audio file
    audio = AudioSegment.from_mp3(audio_path)
    total_length = len(audio)
    
    # Calculate number of slices
    total_slices = (total_length + slice_length_ms - 1) // slice_length_ms
    
    # Create output directory
    target_dir = os.path.join(AUDIO_SLICE_DIR, folder_name)
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"[AudioProcessor] Slicing audio into {total_slices} parts...")
    
    # Slice and save
    for i in range(total_slices):
        start = i * slice_length_ms
        end = min(start + slice_length_ms, total_length)
        slice_audio = audio[start:end]
        
        slice_path = os.path.join(target_dir, f"{i+1}.mp3")
        slice_audio.export(slice_path, format="mp3")
        print(f"[AudioProcessor] Slice {i+1}/{total_slices} saved: {slice_path}")
    
    return target_dir


def generate_unique_folder_name() -> str:
    """
    Generate a unique folder name that is safe for concurrent execution.
    Format: YYYYMMDDHHMMSS_{uuid_short}
    
    Returns:
        Unique folder name string
    """
    timestamp = time.strftime("%Y%m%d%H%M%S")
    # Add short UUID (first 8 chars) to ensure uniqueness across concurrent runs
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{timestamp}_{unique_suffix}"


def process_audio(video_path: str) -> tuple[str, str]:
    """
    Process video: extract audio and slice it.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Tuple of (folder_name, slice_directory_path)
    """
    # Generate unique folder name that won't collide with concurrent runs
    folder_name = generate_unique_folder_name()
    
    # Extract audio
    audio_path = extract_audio_from_video(video_path, target_name=folder_name)
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Extracted audio file not found: {audio_path}")
    
    # Slice audio
    slice_dir = slice_audio(audio_path, folder_name)
    
    return folder_name, slice_dir


if __name__ == "__main__":
    # Test with a sample video
    test_video = input("Enter video file path: ")
    if os.path.exists(test_video):
        folder, slice_dir = process_audio(test_video)
        print(f"\nAudio processed!")
        print(f"Folder name: {folder}")
        print(f"Slice directory: {slice_dir}")
    else:
        print("Video file not found!")
