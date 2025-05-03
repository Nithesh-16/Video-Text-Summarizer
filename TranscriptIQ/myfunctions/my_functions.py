import os
import yt_dlp
import shutil
from datetime import datetime
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
import whisper
import glob
from yt_dlp import YoutubeDL
import math
import tempfile
from pathlib import Path

def get_video_info(video_url):
    try:
        ydl_opts = {}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        
        return {
            "title": info.get("title", "Unknown Title"),
            "views": info.get("view_count", 0),
            "duration": info.get("duration", 0),
            "author": info.get("uploader", "Unknown Author"),
            "video_id": info.get("id", "N/A"),
            "publish_date": info.get("upload_date", "Unknown Date"),
            "thumbnail_url": info.get("thumbnail", ""),
        }
    except Exception as e:
        print(f"Error getting video info: {str(e)}")
        return None

def current_directory(n):
    """Removes older temporary directories if more than `n` exist."""
    temp_dir = Path(tempfile.gettempdir())
    directories = [d for d in temp_dir.glob("Folder_*") if d.is_dir()]
    
    if len(directories) > n:
        for directory in directories:
            try:
                shutil.rmtree(directory)
                print(f"Removed directory: {directory}")
            except Exception as e:
                print(f"Error removing directory {directory}: {str(e)}")
    else:
        print("There are not enough matching directories to remove.")

def create_folder_and_directories():
    """Creates necessary folders for storing downloaded content in temp directory."""
    try:
        temp_dir = Path(tempfile.gettempdir())
        now = datetime.now()
        current_folder = temp_dir / f"Folder_{now.strftime('%Y%m%d_%H%M%S')}"
        current_folder.mkdir(parents=True, exist_ok=True)

        mp4_directory = current_folder / 'media' / 'mp4'
        mp3_directory = current_folder / 'media' / 'mp3'
        txt_directory = current_folder / 'media' / 'txt'

        for directory in [mp4_directory, mp3_directory, txt_directory]:
            directory.mkdir(parents=True, exist_ok=True)

        return str(current_folder)
    except Exception as e:
        print(f"Error creating directories: {str(e)}")
        return None

def download_youtube(video_url, save_path):
    """Downloads a YouTube video as MP4 format."""
    os.makedirs(save_path, exist_ok=True)

    ydl_opts = {
        "outtmpl": f"{save_path}/%(title)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # Ensure an MP4 file exists
    mp4_files = [f for f in os.listdir(save_path) if f.endswith(".mp4")]
    if not mp4_files:
        raise FileNotFoundError("❌ No MP4 file found after download. Please check yt-dlp settings.")

    print(f"🎉 Download completed! File saved in: {save_path}")

    return "mp4"

def download_youtube1(video_url, download_path):
    """Downloads YouTube video as WebM format (alternative method)."""
    opts = {
        "external_downloader": "ffmpeg",
        "quiet": True,
        "outtmpl": download_path + "/%(title)s.%(ext)s"
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([video_url])
        info = ydl.extract_info(video_url, download=False)
        duration = info.get("duration", 0)

    return "webm", duration

def rename_videos(mp4_directory):
    """Renames downloaded videos to a standard name (video.mp4)."""
    files = os.listdir(mp4_directory)
    
    if len(files) > 1:
        for i, filename in enumerate(files, start=1):
            current_path = os.path.join(mp4_directory, filename)
            new_name = f"video_{i}{os.path.splitext(filename)[1]}"
            new_path = os.path.join(mp4_directory, new_name)

            if current_path != new_path:
                os.rename(current_path, new_path)
    elif len(files) == 1:
        filename = files[0]
        current_path = os.path.join(mp4_directory, filename)
        new_name = "video" + os.path.splitext(filename)[1]
        new_path = os.path.join(mp4_directory, new_name)

        if current_path != new_path:
            os.rename(current_path, new_path)
    else:
        print("No files found in the directory.")

def mp4_to_mp3(mp4_directory, video_extension, mp3_directory):
    """Converts MP4 video to MP3 audio."""
    video_path = f"{mp4_directory}/video.{video_extension}"

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if os.path.getsize(video_path) == 0:
        raise OSError(f"Video file is empty or corrupted: {video_path}")

    try:
        video = VideoFileClip(video_path)
        audio_path = f"{mp3_directory}/my_audio.mp3"
        video.audio.write_audiofile(audio_path)
        video.close()
    except Exception as e:
        raise RuntimeError(f"Error converting video to MP3: {e}")

def transcribe_mp3(mp3_directory, name, language=None):
    """Transcribes audio using Whisper.
    
    Args:
        mp3_directory: Directory containing the MP3 file
        name: Name of the MP3 file (without extension)
        language: Language code for transcription (e.g., 'hi' for Hindi, 'te' for Telugu)
    """
    # Use tiny model to save disk space
    model = whisper.load_model("tiny")
    
    # If language is specified, use it for transcription
    if language:
        result = model.transcribe(
            f"{mp3_directory}/{name}.mp3", 
            language=language,
            task="transcribe",
            fp16=False,  # Use full precision for better accuracy
            initial_prompt="This is a high-quality transcription."  # Help guide the model
        )
    else:
        # Auto-detect language if not specified
        result = model.transcribe(
            f"{mp3_directory}/{name}.mp3",
            task="transcribe",
            fp16=False,  # Use full precision for better accuracy
            initial_prompt="This is a high-quality transcription."  # Help guide the model
        )
    
    return result

def concatenate_txt_files(directory):
    """Concatenates multiple transcript text files into one."""
    txt_files = glob.glob(os.path.join(directory, "*.txt"))
    concatenated_text = ""

    for txt_file in txt_files:
        with open(txt_file, "r") as file:
            concatenated_text += file.read() + "\n"

    return concatenated_text

def split_video_into_segments(mp4_directory, video_extension, segment_duration=600):
    """Splits a video into segments of specified duration (in seconds).
    
    Args:
        mp4_directory: Directory containing the video file
        video_extension: Extension of the video file (e.g., 'mp4')
        segment_duration: Duration of each segment in seconds (default: 600 seconds = 10 minutes)
    
    Returns:
        List of paths to the segment files
    """
    video_path = f"{mp4_directory}/video.{video_extension}"
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    try:
        # Load the video
        video = VideoFileClip(video_path)
        duration = video.duration
        
        # Calculate number of segments
        num_segments = math.ceil(duration / segment_duration)
        
        if num_segments <= 1:
            # Video is short enough, no need to split
            return [video_path]
        
        # Create segments directory
        segments_dir = os.path.join(mp4_directory, "segments")
        os.makedirs(segments_dir, exist_ok=True)
        
        segment_paths = []
        
        # Split the video into segments
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = min((i + 1) * segment_duration, duration)
            
            segment_path = os.path.join(segments_dir, f"segment_{i+1}.{video_extension}")
            
            # Extract segment using ffmpeg directly
            import subprocess
            
            # Build ffmpeg command
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-ss", str(start_time), "-t", str(end_time - start_time),
                "-c:v", "libx264", "-c:a", "aac",
                segment_path
            ]
            
            # Run ffmpeg command
            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            segment_paths.append(segment_path)
        
        # Close the video
        video.close()
        
        return segment_paths
    
    except Exception as e:
        raise RuntimeError(f"Error splitting video into segments: {e}")

def transcribe_video_segments(segment_paths, mp3_directory, language=None):
    """Transcribes multiple video segments and combines the results.
    
    Args:
        segment_paths: List of paths to video segment files
        mp3_directory: Directory to save audio files
        language: Language code for transcription (e.g., 'hi' for Hindi, 'te' for Telugu)
    
    Returns:
        Combined transcription result
    """
    if not segment_paths:
        raise ValueError("No video segments provided for transcription")
    
    # Create a directory for segment audio files
    segment_audio_dir = os.path.join(mp3_directory, "segments")
    os.makedirs(segment_audio_dir, exist_ok=True)
    
    # Transcribe each segment
    all_segments = []
    total_duration = 0
    
    for i, segment_path in enumerate(segment_paths):
        # Convert segment to audio
        segment_name = f"segment_{i+1}"
        segment_audio_path = os.path.join(segment_audio_dir, f"{segment_name}.mp3")
        
        try:
            video = VideoFileClip(segment_path)
            video.audio.write_audiofile(segment_audio_path)
            video.close()
            
            # Transcribe the segment
            result = transcribe_mp3(segment_audio_dir, segment_name, language)
            
            # Adjust timestamps to account for segment position
            for segment in result["segments"]:
                segment["start"] += total_duration
                segment["end"] += total_duration
            
            all_segments.extend(result["segments"])
            total_duration += result["duration"]
            
        except Exception as e:
            print(f"Error processing segment {i+1}: {e}")
    
    # Combine results
    combined_result = {
        "text": " ".join([segment["text"] for segment in all_segments]),
        "segments": all_segments,
        "language": result["language"] if "language" in result else None,
        "duration": total_duration
    }
    
    return combined_result
