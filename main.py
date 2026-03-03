#!/usr/bin/env python3
"""
Bilibili Video Voice to Text

A tool to download Bilibili videos, extract audio, slice into chunks,
and transcribe using Silicon Flow TeleAI/TeleSpeechASR model.

Usage:
    python main.py                    # Interactive mode
    python main.py -bv BV1xx411c7mD   # Process single video
    python main.py -bv BV1xx411c7mD BV1yy822d9nE BV1zz...  # Process multiple videos
"""
import os
import sys
import argparse
from typing import List, Optional
from downloader import download_video, find_video_file, get_video_info
from audio_processor import process_audio
from silicon_flow_asr import process_transcription
from cleanup import cleanup_audio_files


def display_video_info(info: dict):
    """Display video metadata in a formatted way."""
    print("\n" + "=" * 60)
    print("Video Information")
    print("=" * 60)
    print(f"  Title:     {info.get('title', 'N/A')}")
    print(f"  Uploader:  {info.get('uploader', 'N/A')}")
    print(f"  BV Number: {info.get('bv_number', 'N/A')}")
    print(f"  Upload:    {info.get('upload_date', 'N/A')}")
    print(f"  Duration:  {info.get('duration', 0)} seconds")
    print(f"  Views:     {info.get('view_count', 0):,}")
    print(f"  Likes:     {info.get('like_count', 0):,}")
    print("=" * 60)


def process_single_video(bv_input: str, index: int = None, total: int = None) -> bool:
    """
    Process a single video from download to transcription.
    
    Args:
        bv_input: BV number (with or without 'BV' prefix)
        index: Optional index for batch processing display
        total: Optional total count for batch processing display
        
    Returns:
        True if successful, False otherwise
    """
    # Display header for this video
    prefix = ""
    if index is not None and total is not None:
        prefix = f"[{index}/{total}] "
    
    print("\n" + "=" * 70)
    print(f"{prefix}Processing video: {bv_input}")
    print("=" * 70)
    
    # Step 1: Get video info
    print("\n" + "-" * 60)
    print(f"Getting video information...")
    print("-" * 60)
    
    video_info = get_video_info(bv_input)
    if video_info:
        display_video_info(video_info)
    else:
        print(f"Warning: Could not retrieve video information for {bv_input}")
    
    # Step 2: Download video
    print("\n" + "-" * 60)
    print("Step 1: Downloading video...")
    print("-" * 60)
    
    bv_number = download_video(bv_input)
    
    if not bv_number:
        print(f"Error: Failed to download video {bv_input}!")
        return False
    
    # Step 3: Find the downloaded video file
    print("\n" + "-" * 60)
    print("Step 2: Locating video file...")
    print("-" * 60)
    
    video_path = find_video_file(bv_number)
    
    if not video_path:
        print(f"Error: Video file not found for {bv_number}")
        return False
    
    print(f"Video file found: {video_path}")
    
    # Step 4: Extract and slice audio
    print("\n" + "-" * 60)
    print("Step 3: Extracting and slicing audio...")
    print("-" * 60)
    
    try:
        folder_name, slice_dir = process_audio(video_path)
        print(f"\nAudio processing completed!")
        print(f"  - Folder name: {folder_name}")
        print(f"  - Slice directory: {slice_dir}")
    except Exception as e:
        print(f"Error: Failed to process audio: {str(e)}")
        return False
    
    # Step 5: Transcribe audio
    print("\n" + "-" * 60)
    print("Step 4: Transcribing audio using Silicon Flow ASR...")
    print("-" * 60)
    
    try:
        output_path = process_transcription(folder_name, video_info=video_info)
    except Exception as e:
        print(f"Error: Failed to transcribe audio: {str(e)}")
        return False
    
    # Step 6: Cleanup temporary audio files
    cleanup_audio_files(folder_name)
    
    # Done for this video
    print("\n" + "=" * 60)
    print(f"✓ Video {bv_input} completed!")
    print(f"  Output: {output_path}")
    if video_info and video_info.get('uploader'):
        print(f"  Uploader: {video_info['uploader']}")
    print("=" * 60)
    
    return True


def interactive_mode():
    """Run in interactive mode (prompt user for BV number)."""
    print("=" * 60)
    print("Bilibili Video Voice to Text - Interactive Mode")
    print("=" * 60)
    
    # Get BV number from user
    bv_input = input("\nEnter BV number (with or without 'BV' prefix): ").strip()
    
    if not bv_input:
        print("Error: BV number is required!")
        sys.exit(1)
    
    # Process the single video
    success = process_single_video(bv_input)
    
    # Final summary
    print("\n" + "=" * 60)
    if success:
        print("All done! Transcription saved successfully.")
    else:
        print("Processing failed!")
    print("=" * 60)
    
    return success


def batch_mode(bv_codes: List[str]):
    """
    Run in batch mode (process multiple BV codes).
    
    Args:
        bv_codes: List of BV numbers to process
    """
    print("=" * 70)
    print("Bilibili Video Voice to Text - Batch Mode")
    print(f"Processing {len(bv_codes)} video(s)")
    print("=" * 70)
    
    results = {
        "success": [],
        "failed": []
    }
    
    for i, bv_code in enumerate(bv_codes, 1):
        success = process_single_video(bv_code, index=i, total=len(bv_codes))
        
        if success:
            results["success"].append(bv_code)
        else:
            results["failed"].append(bv_code)
        
        # Add separator between videos (except after the last one)
        if i < len(bv_codes):
            print("\n" + "#" * 70)
            print(f"Moving to next video... ({i}/{len(bv_codes)} completed)")
            print("#" * 70)
    
    # Final summary
    print("\n" + "=" * 70)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 70)
    print(f"Total videos: {len(bv_codes)}")
    print(f"Successful:   {len(results['success'])}")
    print(f"Failed:       {len(results['failed'])}")
    
    if results["success"]:
        print(f"\nSuccessful videos:")
        for bv in results["success"]:
            print(f"  ✓ {bv}")
    
    if results["failed"]:
        print(f"\nFailed videos:")
        for bv in results["failed"]:
            print(f"  ✗ {bv}")
    
    print("=" * 70)
    
    return len(results["failed"]) == 0


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Download Bilibili videos and transcribe audio to text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Interactive mode
  python main.py -bv BV1xx411c7mD   # Process single video
  python main.py -bv BV1xx411c7mD BV1yy822d9nE   # Process multiple videos
  python main.py -bv BV1xx411c7mD BV1yy822d9nE BV1zz...  # Batch processing
        """
    )
    
    parser.add_argument(
        "-bv", "--bv-codes",
        nargs="+",
        help="One or more BV numbers to process (with or without 'BV' prefix)"
    )
    
    args = parser.parse_args()
    
    # Check if BV codes were provided via command line
    if args.bv_codes:
        # Batch mode
        success = batch_mode(args.bv_codes)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        success = interactive_mode()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
