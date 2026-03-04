"""
Silicon Flow ASR module using TeleAI/TeleSpeechASR model with parallel processing.
API documentation: https://docs.siliconflow.cn/api-reference/audio/create-audio-transcriptions
"""
import os
import re
import requests
import concurrent.futures
import threading
from typing import List, Tuple, Optional, Dict
from config import (
    SILICON_FLOW_API_KEY,
    VOICE_RECOGNITION_MODEL,
    SILICON_FLOW_API_URL,
    AUDIO_SLICE_DIR,
    OUTPUT_DIR
)

# Maximum number of parallel threads
MAX_WORKERS = 20

# Maximum retry attempts for each slice
MAX_RETRIES = 5


class ASRAbortException(Exception):
    """Exception raised when ASR fails after max retries and should abort all threads."""
    pass


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing or replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove invalid characters: < > : " / \ | ? *
    # Also remove control characters (0-31)
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    # Replace multiple spaces with single space
    sanitized = re.sub(r'\s+', ' ', sanitized)
    # Limit length to 100 characters
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    return sanitized


def format_date(upload_date: str) -> str:
    """
    Format upload date from YYYYMMDD to YYYY-MM-DD.
    
    Args:
        upload_date: Date string in YYYYMMDD format
        
    Returns:
        Date string in YYYY-MM-DD format, or original if invalid
    """
    if len(upload_date) == 8 and upload_date.isdigit():
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return upload_date


def generate_output_filename(video_info: Optional[Dict]) -> str:
    """
    Generate output filename based on video metadata.
    Format: [uploader_name]-YYYY-MM-DD-[title].txt
    
    Args:
        video_info: Dictionary containing video metadata
        
    Returns:
        Formatted filename
    """
    if not video_info:
        # Fallback to timestamp if no video info
        import time
        return f"transcription-{time.strftime('%Y%m%d%H%M%S')}.txt"
    
    uploader = video_info.get('uploader', 'Unknown')
    title = video_info.get('title', 'Untitled')
    upload_date = video_info.get('upload_date', '')
    
    # Sanitize components
    uploader = sanitize_filename(uploader)
    title = sanitize_filename(title)
    formatted_date = format_date(upload_date) if upload_date else 'Unknown-Date'
    
    # Build filename: [uploader]-YYYY-MM-DD-[title].txt
    filename = f"{uploader}-{formatted_date}-{title}.txt"
    
    return filename


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file using Silicon Flow API.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Transcribed text
    """
    if not SILICON_FLOW_API_KEY:
        raise ValueError("SILICON_FLOW_API_KEY not found in environment variables")
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    headers = {
        "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
    }
    
    # Prepare multipart/form-data
    with open(audio_path, "rb") as audio_file:
        files = {
            "file": (os.path.basename(audio_path), audio_file, "audio/mpeg")
        }
        data = {
            "model": VOICE_RECOGNITION_MODEL
            # Optional parameters can be added here:
            # "language": "zh",
            # "prompt": "",
            # "response_format": "json",
            # "temperature": 0
        }
        
        try:
            response = requests.post(
                SILICON_FLOW_API_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=300  # 5 minutes timeout for large files
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract text from response
            # Response format: {"text": "transcribed text"}
            text = result.get("text", "")
            return text
            
        except requests.exceptions.RequestException as e:
            print(f"[ASR] API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ASR] Response: {e.response.text}")
            raise


def transcribe_single_file(args: Tuple[int, str], abort_event: threading.Event) -> Tuple[int, str]:
    """
    Transcribe a single audio file with retry logic and return with its index.
    This function is designed to be used with ThreadPoolExecutor.
    
    Args:
        args: Tuple of (index, audio_file_path)
        abort_event: Threading event to signal cancellation across all threads
        
    Returns:
        Tuple of (index, transcribed_text)
        
    Raises:
        ASRAbortException: If max retries exceeded, triggering abort of all threads
    """
    index, audio_path = args
    audio_file = os.path.basename(audio_path)
    
    print(f"[ASR] Thread processing {index}: {audio_file}")
    
    # Check if abort has been signaled
    if abort_event.is_set():
        print(f"[ASR] Thread {index} aborted (abort signal received)")
        return (index, f"[Aborted: {audio_file}]")
    
    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            text = transcribe_audio(audio_path)
            print(f"[ASR] Thread {index} completed: {audio_file} (attempt {attempt})")
            if text:
                preview = text[:80] + "..." if len(text) > 80 else text
                print(f"       -> {preview}")
            return (index, text)
        except Exception as e:
            if abort_event.is_set():
                print(f"[ASR] Thread {index} aborted during retry")
                return (index, f"[Aborted: {audio_file}]")
            
            if attempt < MAX_RETRIES:
                print(f"[ASR] Thread {index} attempt {attempt} failed: {audio_file} - {str(e)}")
                print(f"[ASR] Retrying... ({attempt}/{MAX_RETRIES})")
            else:
                # Max retries exceeded - signal abort and raise exception
                error_msg = f"[Error transcribing {audio_file}: Max retries ({MAX_RETRIES}) exceeded - {str(e)}]"
                print(f"[ASR] Thread {index} FAILED after {MAX_RETRIES} attempts: {audio_file}")
                print(f"[ASR] {error_msg}")
                print(f"[ASR] Signaling abort to all threads...")
                abort_event.set()
                raise ASRAbortException(f"Slice {index} ({audio_file}) failed after {MAX_RETRIES} retries")
    
    # This should never be reached
    return (index, f"[Unexpected error: {audio_file}]")


def transcribe_audio_folder_parallel(folder_name: str) -> str:
    """
    Transcribe all audio slices in a folder using parallel processing.
    
    Args:
        folder_name: Name of the folder containing audio slices
        
    Returns:
        Combined transcribed text from all slices (sorted by index)
        
    Raises:
        ASRAbortException: If any slice fails after max retries
    """
    slice_dir = os.path.join(AUDIO_SLICE_DIR, folder_name)
    
    if not os.path.exists(slice_dir):
        raise FileNotFoundError(f"Slice directory not found: {slice_dir}")
    
    # Get all audio files and sort by filename (numeric order)
    audio_files = [f for f in os.listdir(slice_dir) if f.endswith(".mp3")]
    audio_files.sort(key=lambda x: int(os.path.splitext(x)[0]))
    
    if not audio_files:
        raise ValueError(f"No audio files found in: {slice_dir}")
    
    total_files = len(audio_files)
    print(f"[ASR] Found {total_files} audio slices to transcribe")
    print(f"[ASR] Using {min(MAX_WORKERS, total_files)} parallel threads")
    print(f"[ASR] Max retries per slice: {MAX_RETRIES}\n")
    
    # Prepare arguments with index for each file
    indexed_files = [
        (i + 1, os.path.join(slice_dir, f)) 
        for i, f in enumerate(audio_files)
    ]
    
    # Shared abort event for signaling cancellation across threads
    abort_event = threading.Event()
    
    # Process in parallel using ThreadPoolExecutor
    results: List[Tuple[int, str]] = []
    abort_error = None
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks and collect results
            future_to_index = {
                executor.submit(transcribe_single_file, args, abort_event): args[0] 
                for args in indexed_files
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_index):
                try:
                    result = future.result()
                    results.append(result)
                except ASRAbortException as e:
                    # Store the abort error and stop processing
                    abort_error = e
                    print(f"[ASR] Aborting all threads due to: {str(e)}")
                    break
                except Exception as e:
                    index = future_to_index[future]
                    print(f"[ASR] Unexpected error in thread {index}: {str(e)}")
                    results.append((index, f"[Unexpected error: {str(e)}]"))
    except Exception as e:
        print(f"[ASR] Executor error: {str(e)}")
        raise
    
    # If abort occurred, raise the exception
    if abort_error:
        raise abort_error
    
    # Sort results by index to maintain order
    results.sort(key=lambda x: x[0])
    
    # Join all texts in order
    all_text = [text for _, text in results]
    
    print(f"\n[ASR] All {len(results)} threads completed successfully")
    
    return "\n".join(all_text)


def save_transcription(
    text: str,
    video_info: Optional[Dict] = None,
    folder_name: Optional[str] = None
) -> str:
    """
    Save transcription to a text file with formatted filename.
    
    Args:
        text: Transcribed text
        video_info: Optional video metadata for filename formatting
        folder_name: Optional fallback folder name (for backwards compatibility)
        
    Returns:
        Path to the saved file
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate filename based on video info
    filename = generate_output_filename(video_info)
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"[ASR] Transcription saved to: {output_path}")
    return output_path


def remove_transcription_if_exists(video_info: Optional[Dict] = None) -> None:
    """
    Remove transcription file if it exists.
    Used for cleanup when ASR fails.
    
    Args:
        video_info: Optional video metadata for filename determination
    """
    filename = generate_output_filename(video_info)
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"[ASR] Removed partial output file: {output_path}")
        except Exception as e:
            print(f"[ASR] Warning: Failed to remove output file: {str(e)}")


def process_transcription(
    folder_name: str,
    video_info: Optional[Dict] = None
) -> str:
    """
    Process transcription for all slices in a folder using parallel processing.
    
    Args:
        folder_name: Name of the folder containing audio slices
        video_info: Optional video metadata for filename formatting
        
    Returns:
        Path to the saved transcription file
        
    Raises:
        ASRAbortException: If any slice fails after max retries
    """
    print(f"\n{'='*60}")
    print(f"[ASR] Starting parallel transcription for: {folder_name}")
    print(f"{'='*60}\n")
    
    try:
        text = transcribe_audio_folder_parallel(folder_name)
        output_path = save_transcription(text, video_info=video_info)
        
        print(f"\n{'='*60}")
        print(f"[ASR] Parallel transcription completed!")
        print(f"[ASR] Output: {output_path}")
        print(f"{'='*60}")
        
        return output_path
    except ASRAbortException as e:
        # Clean up partial output if exists
        print(f"\n{'='*60}")
        print(f"[ASR] Transcription FAILED: {str(e)}")
        print(f"[ASR] Cleaning up partial output...")
        remove_transcription_if_exists(video_info)
        print(f"{'='*60}\n")
        raise


if __name__ == "__main__":
    # Test transcription
    test_folder = input("Enter folder name containing audio slices: ")
    try:
        result_path = process_transcription(test_folder)
        print(f"\nTranscription saved to: {result_path}")
    except ASRAbortException as e:
        print(f"\nTranscription aborted: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
