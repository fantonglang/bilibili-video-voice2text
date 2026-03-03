"""
Cleanup module for removing temporary audio files after transcription.
"""
import os
import shutil
from config import AUDIO_CONV_DIR, AUDIO_SLICE_DIR


def delete_file_safely(file_path: str) -> bool:
    """
    Safely delete a file if it exists.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        True if deleted or didn't exist, False on error
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[Cleanup] Deleted file: {file_path}")
            return True
        return True
    except Exception as e:
        print(f"[Cleanup] Failed to delete file {file_path}: {str(e)}")
        return False


def delete_folder_safely(folder_path: str) -> bool:
    """
    Safely delete a folder and all its contents if it exists.
    
    Args:
        folder_path: Path to the folder to delete
        
    Returns:
        True if deleted or didn't exist, False on error
    """
    try:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            print(f"[Cleanup] Deleted folder: {folder_path}")
            return True
        return True
    except Exception as e:
        print(f"[Cleanup] Failed to delete folder {folder_path}: {str(e)}")
        return False


def cleanup_audio_files(folder_name: str, audio_filename: str = None) -> dict:
    """
    Clean up audio files after transcription is complete.
    
    This deletes:
    1. The converted full audio file (audio/conv/{folder_name}.mp3)
    2. All audio slices in the slice folder (audio/slice/{folder_name}/)
    
    Args:
        folder_name: The folder name used for audio processing (timestamp-based)
        audio_filename: Optional specific audio filename (defaults to folder_name)
        
    Returns:
        Dictionary with cleanup results
    """
    results = {
        "full_audio_deleted": False,
        "slices_deleted": False,
        "errors": []
    }
    
    print("\n" + "-" * 60)
    print("Step 5: Cleaning up temporary audio files...")
    print("-" * 60)
    
    # Delete the full converted audio file
    if audio_filename is None:
        audio_filename = folder_name
    
    full_audio_path = os.path.join(AUDIO_CONV_DIR, f"{audio_filename}.mp3")
    
    if os.path.exists(full_audio_path):
        if delete_file_safely(full_audio_path):
            results["full_audio_deleted"] = True
        else:
            results["errors"].append(f"Failed to delete: {full_audio_path}")
    else:
        print(f"[Cleanup] Full audio file not found: {full_audio_path}")
    
    # Delete the slices folder
    slices_folder = os.path.join(AUDIO_SLICE_DIR, folder_name)
    
    if os.path.exists(slices_folder):
        if delete_folder_safely(slices_folder):
            results["slices_deleted"] = True
        else:
            results["errors"].append(f"Failed to delete: {slices_folder}")
    else:
        print(f"[Cleanup] Slices folder not found: {slices_folder}")
    
    # Summary
    print("\n[Cleanup] Summary:")
    if results["full_audio_deleted"]:
        print("  ✓ Full audio file deleted")
    if results["slices_deleted"]:
        print("  ✓ Audio slices deleted")
    if not results["full_audio_deleted"] and not results["slices_deleted"]:
        print("  - No files to clean up")
    if results["errors"]:
        print(f"  ✗ Errors: {len(results['errors'])}")
    
    return results


def cleanup_all_audio():
    """
    Clean up all audio files in the audio directory.
    Use with caution - this deletes all processed audio files.
    """
    print("\n" + "=" * 60)
    print("[Cleanup] Cleaning ALL audio files...")
    print("=" * 60)
    
    # Delete all files in audio/conv/
    if os.path.exists(AUDIO_CONV_DIR):
        for filename in os.listdir(AUDIO_CONV_DIR):
            file_path = os.path.join(AUDIO_CONV_DIR, filename)
            if os.path.isfile(file_path):
                delete_file_safely(file_path)
    
    # Delete all folders in audio/slice/
    if os.path.exists(AUDIO_SLICE_DIR):
        for foldername in os.listdir(AUDIO_SLICE_DIR):
            folder_path = os.path.join(AUDIO_SLICE_DIR, foldername)
            if os.path.isdir(folder_path):
                delete_folder_safely(folder_path)
    
    print("[Cleanup] All audio files cleaned up!")


if __name__ == "__main__":
    # Test cleanup
    test_folder = input("Enter folder name to cleanup (or 'ALL' to cleanup everything): ")
    
    if test_folder.upper() == "ALL":
        confirm = input("Are you sure? This will delete ALL audio files! (yes/no): ")
        if confirm.lower() == "yes":
            cleanup_all_audio()
        else:
            print("Aborted.")
    else:
        cleanup_audio_files(test_folder)
