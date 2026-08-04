import os
import sys
import subprocess
import json
import cloudinary
import cloudinary.uploader
import requests
import pypinyin
import glob

def setup_cloudinary():
    cloudinary.config(
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key = os.environ.get('CLOUDINARY_API_KEY'),
        api_secret = os.environ.get('CLOUDINARY_API_SECRET'),
        secure = True
    )

def download_video(url, output_path="downloaded_video.mp4"):
    print(f"Downloading video from {url}...")
    subprocess.run(['yt-dlp', '-o', output_path, '-f', 'mp4', url], check=True)
    return output_path

def upload_to_cloudinary(file_path):
    print("Uploading to Cloudinary...")
    upload_res = cloudinary.uploader.upload(file_path, resource_type="video")
    return upload_res['secure_url']

def extract_and_chunk_audio(video_path, chunk_duration=60):
    print("Extracting and chunking audio...")
    # First extract full audio to mp3
    audio_path = "audio.mp3"
    subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path, '-y'], check=True)
    
    # Split audio into chunks (e.g. chunk_000.mp3, chunk_001.mp3)
    chunk_pattern = "chunk_%03d.mp3"
    subprocess.run(['ffmpeg', '-i', audio_path, '-f', 'segment', '-segment_time', str(chunk_duration), '-c', 'copy', chunk_pattern, '-y'], check=True)
    
    # Return sorted list of chunk files
    chunks = sorted(glob.glob("chunk_*.mp3"))
    return chunks

def process_whisper_groq(audio_chunks, chunk_duration=60):
    print("Running Groq Whisper API on chunks...")
    groq_api_key = os.environ.get('GROQ_API_KEY')
    if not groq_api_key:
        print("Error: GROQ_API_KEY environment variable is not set.")
        return []

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}"
    }
    
    all_sentences = []
    punc_chars = set('，。！？；：,.!?;:')
    
    for idx, chunk_path in enumerate(audio_chunks):
        print(f"Processing {chunk_path}...")
        time_offset = idx * chunk_duration
        
        # We use a very basic prompt without Vietnamese characters to avoid encoding issues on Windows runners,
        # but keep temperature at 0 for stability.
        data = {
            "model": "whisper-large-v3",
            "response_format": "verbose_json",
            "temperature": "0",
            "prompt": "Here is a Chinese video. Please transcribe it."
        }
        
        with open(chunk_path, "rb") as f:
            files = {
                "file": (os.path.basename(chunk_path), f, "audio/mpeg")
            }
            response = requests.post(url, headers=headers, data=data, files=files)
            
        if response.status_code != 200:
            print(f"Error from Groq API for {chunk_path}: {response.text}")
            continue
            
        res_json = response.json()
        segments = res_json.get('segments', [])
        
        for seg in segments:
            text = seg.get('text', '').strip()
            # Apply time offset to the segment
            start = seg.get('start', 0.0) + time_offset
            end = seg.get('end', 0.0) + time_offset
            
            chars = [c for c in text if c not in punc_chars and c.strip()]
            if not chars:
                continue
                
            duration = end - start
            char_duration = duration / len(chars) if len(chars) > 0 else 0
            
            current_sentence = []
            current_time = start
            
            for char in text:
                if not char.strip():
                    continue
                if char in punc_chars:
                    if current_sentence:
                        current_sentence[-1]['word'] += char
                else:
                    pinyin_list = pypinyin.pinyin(char, style=pypinyin.Style.TONE)
                    py = pinyin_list[0][0] if pinyin_list else ""
                    
                    word_info = {
                        "word": char,
                        "pinyin": py,
                        "start": round(current_time, 2),
                        "end": round(current_time + char_duration, 2),
                        "confidence": 0.99
                    }
                    current_sentence.append(word_info)
                    current_time += char_duration
                    
            if current_sentence:
                all_sentences.append(current_sentence)
                
    return all_sentences

def main():
    video_url = os.environ.get('VIDEO_URL')
    if not video_url:
        print("Error: VIDEO_URL environment variable is not set.")
        sys.exit(1)
        
    setup_cloudinary()
    
    video_path = download_video(video_url)
    cloud_video_url = upload_to_cloudinary(video_path)
    
    audio_chunks = extract_and_chunk_audio(video_path, chunk_duration=60)
    subtitles = process_whisper_groq(audio_chunks, chunk_duration=60)
    
    final_data = {
        "video_url": cloud_video_url,
        "subtitles": subtitles
    }
    
    os.makedirs('public', exist_ok=True)
    with open('public/data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print("Processing complete. Data saved to public/data.json")

if __name__ == "__main__":
    main()
