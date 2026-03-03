"""
Video downloader module using yt-dlp to download Bilibili videos.
"""
import os
import subprocess
import glob
import json
from config import VIDEO_DIR


def ensure_video_folder():
    """Ensure the video directory exists."""
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR)


def get_cookie_file_path() -> str:
    """
    Get the path to the cookies file.
    
    Returns:
        Path to cookies.txt or cookies.json, or empty string if not found
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for cookies.txt (Netscape format)
    cookies_txt = os.path.join(script_dir, "cookies.txt")
    if os.path.exists(cookies_txt):
        return cookies_txt
    
    # Check for cookies.json
    cookies_json = os.path.join(script_dir, "cookies.json")
    if os.path.exists(cookies_json):
        return cookies_json
    
    return ""


def get_yt_dlp_base_args() -> list:
    """
    Get base arguments for yt-dlp including cookies and user-agent.
    
    Returns:
        List of base arguments for yt-dlp
    """
    args = []
    
    # Add cookies if available
    cookie_file = get_cookie_file_path()
    if cookie_file:
        print(f"[Downloader] Using cookies from: {cookie_file}")
        if cookie_file.endswith('.json'):
            args.extend(["--cookies-from-browser", "firefox"])  # fallback
        else:
            args.extend(["--cookies", cookie_file])
    else:
        print("[Downloader] No cookies file found. Some videos may require login.")
        print("[Downloader] Create cookies.txt from your browser to access restricted content.")
    
    # Add user-agent to avoid bot detection
    args.extend([
        "--user-agent",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ])
    
    # Add referer
    args.extend(["--add-header", "Referer:https://www.bilibili.com/"])
    
    return args


def get_video_info(bv_number: str) -> dict:
    """
    Get video metadata using yt-dlp without downloading.
    
    Args:
        bv_number: BV number of the video (with or without 'BV' prefix)
        
    Returns:
        Dictionary containing video metadata including:
        - title: Video title
        - uploader: Uploader/channel name
        - upload_date: Upload date (YYYYMMDD format)
        - description: Video description
        - duration: Video duration in seconds
        - view_count: Number of views
        - like_count: Number of likes
        - webpage_url: Video URL
    """
    if not bv_number.startswith("BV"):
        bv_number = "BV" + bv_number
    
    video_url = f"https://www.bilibili.com/video/{bv_number}"
    
    try:
        # Build command with base args
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--skip-download",
        ] + get_yt_dlp_base_args() + [video_url]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            # Check for specific errors
            if "HTTP Error 412" in error_msg:
                print(f"[Downloader] HTTP 412 Error: Bilibili requires login/cookies for this video.")
                print(f"[Downloader] Please add cookies.txt to the project directory.")
            elif "HTTP Error 403" in error_msg:
                print(f"[Downloader] HTTP 403 Error: Access forbidden. Try adding cookies.")
            else:
                print(f"[Downloader] Failed to get video info: {error_msg}")
            return {}
        
        # Parse JSON output
        lines = result.stdout.strip().split('\n')
        if not lines or not lines[0]:
            return {}
            
        info = json.loads(lines[0])
        
        # Extract relevant fields
        video_info = {
            "title": info.get("title", ""),
            "uploader": info.get("uploader", ""),
            "uploader_id": info.get("uploader_id", ""),
            "upload_date": info.get("upload_date", ""),
            "description": info.get("description", ""),
            "duration": info.get("duration", 0),
            "view_count": info.get("view_count", 0),
            "like_count": info.get("like_count", 0),
            "webpage_url": info.get("webpage_url", video_url),
            "thumbnail": info.get("thumbnail", ""),
            "bv_number": bv_number
        }
        
        return video_info
        
    except subprocess.TimeoutExpired:
        print(f"[Downloader] Timeout getting video info for {bv_number}")
        return {}
    except Exception as e:
        print(f"[Downloader] Error getting video info: {str(e)}")
        return {}


def download_video(bv_number: str) -> str:
    """
    Download Bilibili video using yt-dlp.
    
    Args:
        bv_number: BV number of the video (with or without 'BV' prefix)
        
    Returns:
        The folder name where the video is saved (same as BV number with 'BV' prefix)
    """
    # Normalize BV number
    if not bv_number.startswith("BV"):
        bv_number = "BV" + bv_number
    
    video_url = f"https://www.bilibili.com/video/{bv_number}"
    output_dir = os.path.join(VIDEO_DIR, bv_number)
    
    ensure_video_folder()
    
    print(f"[Downloader] Downloading video: {video_url}")
    
    try:
        # Build command with base args
        cmd = [
            "yt-dlp",
            "-P", output_dir,
            "-o", "%(title)s.%(ext)s",
        ] + get_yt_dlp_base_args() + [video_url]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout for download
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if "HTTP Error 412" in error_msg:
                print(f"[Downloader] HTTP 412 Error: Bilibili requires login/cookies for this video.")
                print(f"[Downloader] Please add cookies.txt to the project directory.")
            elif "HTTP Error 403" in error_msg:
                print(f"[Downloader] HTTP 403 Error: Access forbidden. Try adding cookies.")
            else:
                print(f"[Downloader] Download failed: {error_msg}")
            return ""
        
        print(result.stdout)
        print(f"[Downloader] Video downloaded to: {output_dir}")
        
        # Clean up XML files
        xml_files = glob.glob(os.path.join(output_dir, "*.xml"))
        for xml_file in xml_files:
            os.remove(xml_file)
            print(f"[Downloader] Removed XML file: {xml_file}")
        
        return bv_number
        
    except subprocess.TimeoutExpired:
        print(f"[Downloader] Download timeout for {bv_number}")
        return ""
    except Exception as e:
        print(f"[Downloader] Error occurred: {str(e)}")
        return ""


def find_video_file(bv_number: str) -> str:
    """
    Find the downloaded video file path by BV number.
    
    Args:
        bv_number: BV number (with or without 'BV' prefix)
        
    Returns:
        Full path to the video file, or empty string if not found
    """
    if not bv_number.startswith("BV"):
        bv_number = "BV" + bv_number
    
    # Try direct .mp4 file first
    direct_path = os.path.join(VIDEO_DIR, f"{bv_number}.mp4")
    if os.path.exists(direct_path):
        return direct_path
    
    # Search in the subdirectory
    dir_path = os.path.join(VIDEO_DIR, bv_number)
    if os.path.isdir(dir_path):
        for file in os.listdir(dir_path):
            if file.endswith((".mp4", ".flv", ".mkv", ".avi")):
                return os.path.join(dir_path, file)
    
    return ""


if __name__ == "__main__":
    # Test download and get info
    test_bv = input("Enter BV number: ")
    
    # Check for cookies
    cookie_path = get_cookie_file_path()
    if cookie_path:
        print(f"\n[Downloader] Using cookies: {cookie_path}")
    else:
        print("\n[Downloader] Warning: No cookies.txt found!")
        print("[Downloader] Some videos may not be accessible without login.")
    
    # Get video info first
    print("\n[Downloader] Getting video info...")
    info = get_video_info(test_bv)
    if info:
        print(f"\nVideo Information:")
        print(f"  Title: {info.get('title', 'N/A')}")
        print(f"  Uploader: {info.get('uploader', 'N/A')}")
        print(f"  Upload Date: {info.get('upload_date', 'N/A')}")
        print(f"  Duration: {info.get('duration', 0)} seconds")
        print(f"  Views: {info.get('view_count', 0)}")
        print(f"  Likes: {info.get('like_count', 0)}")
    
    # Download video
    print("\n[Downloader] Starting download...")
    folder = download_video(test_bv)
    if folder:
        video_path = find_video_file(folder)
        print(f"Video file path: {video_path}")
