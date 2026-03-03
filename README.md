# Bilibili Video Voice to Text

A Python tool to download Bilibili videos, extract audio, slice into chunks, and transcribe using Silicon Flow's TeleAI/TeleSpeechASR model.

## Features

- **Download Bilibili videos** using `yt-dlp`
- **Extract audio** from videos using `moviepy`
- **Slice audio** into manageable chunks using `pydub`
- **Speech-to-text** using Silicon Flow API with TeleAI/TeleSpeechASR model
- **Parallel processing** with 20 threads for faster transcription
- **Automatic cleanup** of temporary audio files after transcription
- **Formatted output filenames** with uploader name and date
- **Concurrency-safe** - can run multiple instances simultaneously on different videos
- **Docker support** - containerized execution with auto-cleanup

## Quick Start with Docker

### Prerequisites

- Docker installed on your system
- `.env` file with your Silicon Flow API key (see below)

### Step 0: Configure API Key

Before running, you need to set up your API key. Create a `.env` file in the project root:

```bash
# Create .env file
cat > .env << 'EOF'
SILICON_FLOW_API_KEY=[your_api_key_here]
VOICE_RECOGNITION_MODEL=TeleAI/TeleSpeechASR
EOF
```

> ⚠️ **Important**: Replace `[your_api_key_here]` with your actual Silicon Flow API key!

Or manually create the file:
```bash
echo "SILICON_FLOW_API_KEY=[your_api_key_here]" > .env
echo "VOICE_RECOGNITION_MODEL=TeleAI/TeleSpeechASR" >> .env
```

### Using the Bash Script (Recommended)

The easiest way to run with Docker:

```bash
# Make the script executable (first time only)
chmod +x bili-voice2text.sh

# Interactive mode
./bili-voice2text.sh

# Process single video
./bili-voice2text.sh -bv BV1xx411c7mD

# Process multiple videos
./bili-voice2text.sh -bv BV1xx411c7mD BV1yy822d9nE
```

The script will:
1. Automatically build the Docker image (first run)
2. Start a new container for processing
3. Mount volumes for `outputs/`, `bilibili_video/`, and `.env`
4. Remove the container automatically after completion

### Manual Docker Commands

If you prefer to run Docker commands directly:

```bash
# Build the image
docker build -t bili-voice2text .

# Interactive mode
docker run -it --rm \
  -v "$(pwd)/outputs:/app/outputs" \
  -v "$(pwd)/bilibili_video:/app/bilibili_video" \
  -v "$(pwd)/.env:/app/.env:ro" \
  bili-voice2text

# Process specific videos
docker run -it --rm \
  -v "$(pwd)/outputs:/app/outputs" \
  -v "$(pwd)/bilibili_video:/app/bilibili_video" \
  -v "$(pwd)/.env:/app/.env:ro" \
  bili-voice2text -bv BV1xx411c7mD BV1yy822d9nE
```

### Docker Volumes

The container mounts these directories from your host:

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./outputs/` | `/app/outputs/` | Transcription output files |
| `./bilibili_video/` | `/app/bilibili_video/` | Downloaded videos |
| `./.env` | `/app/.env` | API key configuration (read-only) |

### Bilibili Login / Cookie Issues

Some videos require login to access. If you see `HTTP 412` or `HTTP 403` errors:

1. **Export cookies from your browser** (see `get-cookies-helper.md` for detailed instructions):
   - Install "Get cookies.txt LOCALLY" Chrome extension
   - Go to [bilibili.com](https://www.bilibili.com) and **log in**
   - Export cookies as `cookies.txt`
   - Place `cookies.txt` in the project directory (same folder as `main.py`)

2. **For Docker users**, mount cookies as a volume:
   ```bash
   docker run -it --rm \
     -v "$(pwd)/outputs:/app/outputs" \
     -v "$(pwd)/bilibili_video:/app/bilibili_video" \
     -v "$(pwd)/.env:/app/.env:ro" \
     -v "$(pwd)/cookies.txt:/app/cookies.txt:ro" \
     bili-voice2text -bv BV1xx411c7mD
   ```

The downloader will automatically detect and use `cookies.txt` if present.

### Docker Build Troubleshooting

If you encounter `TLS handshake timeout` or network errors during build:

```bash
# Method 1: Use the dedicated build script
./build-docker.sh

# Method 2: Pull base image from mirror (for users in China)
docker pull docker.mirrors.sjtug.sjtu.edu.cn/library/python:3.11-slim
docker tag docker.mirrors.sjtug.sjtu.edu.cn/library/python:3.11-slim python:3.11-slim
docker build -t bili-voice2text .

# Method 3: Use host network
docker build --network=host -t bili-voice2text .

# Method 4: Use the mirror Dockerfile
docker build -f Dockerfile.mirror -t bili-voice2text .
```

**Configure permanent Docker mirror** (create/edit `/etc/docker/daemon.json`):

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

Restart Docker after configuration:
```bash
# macOS
killall Docker && open /Applications/Docker.app

# Linux
sudo systemctl restart docker
```

## Project Structure

```
.
├── .env                    # Environment variables (API key)
├── .venv/                  # Python virtual environment
├── bilibili_video/         # Downloaded videos storage
├── audio/
│   ├── conv/              # Extracted audio files (auto-cleaned after use)
│   └── slice/             # Sliced audio chunks (auto-cleaned after use)
├── outputs/               # Transcription output files
├── config.py              # Configuration module
├── downloader.py          # Video downloader (yt-dlp)
├── audio_processor.py     # Audio extraction and slicing
├── silicon_flow_asr.py    # Silicon Flow ASR API client
├── cleanup.py             # Audio cleanup module
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image definition
├── Dockerfile.mirror           # Docker image with China mirror
├── bili-voice2text.sh          # Docker wrapper script (auto-cleanup)
├── build-docker.sh             # Docker build helper script
├── .dockerignore               # Docker build exclusions
├── get-cookies-helper.md       # Guide for getting Bilibili cookies
└── cookies.txt                 # Bilibili cookies (not in git, create yourself)
```

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

The `.env` file is already configured with the Silicon Flow API key:

```env
SILICON_FLOW_API_KEY=sk-xxxx
VOICE_RECOGNITION_MODEL=TeleAI/TeleSpeechASR
```

## Usage

### Interactive Mode

Run without arguments to enter interactive mode:

```bash
python main.py
```

Then enter the BV number when prompted.

### Single Video (Command Line)

Process a single video directly:

```bash
python main.py -bv BV1xx411c7mD
# or without BV prefix:
python main.py -bv 1xx411c7mD
```

### Batch Processing (Multiple Videos)

Process multiple videos in one command:

```bash
python main.py -bv BV1xx411c7mD BV1yy822d9nE BV1zz333e4fA
```

Videos will be processed sequentially, and a summary will be shown at the end.

### Command Line Help

```bash
python main.py --help
```

### Workflow

1. **Input**: Enter the BV number (e.g., `BV1xx411c7mD` or just `1xx411c7mD`)
2. **Get Info**: Video metadata is retrieved (title, uploader, etc.)
3. **Download**: Video is downloaded to `bilibili_video/{BV_NUMBER}/`
4. **Extract Audio**: Audio is extracted and saved to `audio/conv/{timestamp}.mp3`
5. **Slice**: Audio is sliced into 45-second chunks at `audio/slice/{timestamp}/`
6. **Transcribe**: Slices are transcribed in parallel (20 threads) using Silicon Flow API
7. **Cleanup**: Temporary audio files are automatically deleted
8. **Output**: Transcription saved to `outputs/[uploader]-YYYY-MM-DD-[title].txt`

### Output Filename Format

Transcription files are named with the following format:

```
[uploader_name]-YYYY-MM-DD-[video_title].txt
```

Example:
```
[技术宅小明]-2024-01-15-[Python教程第1课].txt
```

If video metadata cannot be retrieved, a timestamp-based fallback is used.

## Modules

### `downloader.py`

- `get_video_info(bv_number)`: Get video metadata (uploader, title, date, etc.)
- `download_video(bv_number)`: Download video by BV number
- `find_video_file(bv_number)`: Locate the downloaded video file

### `audio_processor.py`

- `extract_audio_from_video(video_path)`: Extract audio from video using moviepy
- `slice_audio(audio_path, folder_name)`: Slice audio into chunks using pydub
- `process_audio(video_path)`: Full audio processing pipeline

### `silicon_flow_asr.py`

- `transcribe_audio(audio_path)`: Transcribe single audio file via API
- `transcribe_audio_folder_parallel(folder_name)`: Transcribe all slices in parallel (20 threads)
- `save_transcription(text, video_info)`: Save transcription with formatted filename
- `process_transcription(folder_name, video_info)`: Full transcription pipeline

### `cleanup.py`

- `cleanup_audio_files(folder_name)`: Delete temporary audio files and slices after transcription
- `cleanup_all_audio()`: Delete ALL audio files (use with caution)

### `config.py`

Central configuration loading environment variables from `.env`:
- `SILICON_FLOW_API_KEY`: API key for authentication
- `VOICE_RECOGNITION_MODEL`: Model name (TeleAI/TeleSpeechASR)
- Directory paths and slice length settings

## Video Metadata Available

Via `get_video_info(bv_number)`:

| Field | Description |
|-------|-------------|
| `title` | Video title |
| `uploader` | Uploader/channel name |
| `uploader_id` | Uploader's UID |
| `upload_date` | Upload date (YYYYMMDD) |
| `description` | Video description |
| `duration` | Video duration in seconds |
| `view_count` | Number of views |
| `like_count` | Number of likes |
| `webpage_url` | Video URL |
| `thumbnail` | Thumbnail URL |
| `bv_number` | BV number |

## API Reference

- **Silicon Flow Audio Transcription API**: https://docs.siliconflow.cn/api-reference/audio/create-audio-transcriptions
- **Model**: TeleAI/TeleSpeechASR
- **Audio Format**: MP3

## Dependencies

- `yt-dlp`: Video downloader
- `moviepy`: Video/audio processing
- `pydub`: Audio manipulation
- `python-dotenv`: Environment variable management
- `requests`: HTTP client for API calls
- `audioop-lts`: Python 3.13+ compatibility for pydub

## Concurrent Execution

This program is designed to be safe for concurrent execution on different videos:

### What's Safe
- ✅ Running multiple instances on **different videos**
- ✅ Each instance uses **unique folder names** (timestamp + UUID)
- ✅ Video downloads are isolated by BV number

### API Rate Limits
**Important**: The Silicon Flow API may have rate limits. When running multiple instances:
- Each instance uses 20 parallel threads internally
- Multiple instances = more concurrent API requests
- If you hit rate limits, you'll get HTTP 429 errors

**Recommendation**: For heavy concurrent usage, consider:
1. Reducing `MAX_WORKERS` in `silicon_flow_asr.py`
2. Adding delays between instances
3. Processing videos sequentially instead

### Potential Resource Conflicts
- **Disk space**: Each instance stores video files temporarily
- **Memory**: MoviePy can be memory-intensive with large videos
- **Network**: Multiple yt-dlp downloads may saturate bandwidth

### Example: Safe Concurrent Usage

```bash
# Terminal 1
python main.py
# Enter: BV1xx411c7mD

# Terminal 2 (at the same time)
python main.py
# Enter: BV1yy822d9nE
```

Each instance will create unique folders like:
- `audio/slice/20240303220115_a3f7b2d1/`
- `audio/slice/20240303220115_c8e5a9f2/`

## License

MIT License
