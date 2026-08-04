import os
import sys
import subprocess
import json
import cloudinary
import cloudinary.uploader
import requests
import pypinyin

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

def extract_audio(video_path, audio_path="audio.mp3"):
    print("Extracting audio...")
    subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path, '-y'], check=True)
    return audio_path

def process_whisper_groq(audio_path):
    print("Running Groq Whisper API...")
    groq_api_key = os.environ.get('GROQ_API_KEY')
    if not groq_api_key:
        print("Error: GROQ_API_KEY environment variable is not set.")
        return []

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}"
    }
    data = {
        "model": "whisper-large-v3",
        "response_format": "verbose_json",
        "temperature": "0",
        "prompt": "Bắt đầu bóc băng phụ đề tiếng Trung một cách chi tiết."
    }
    
    with open(audio_path, "rb") as f:
        files = {
            "file": ("audio.mp3", f, "audio/mpeg")
        }
        print("Sending request to Groq API...")
        response = requests.post(url, headers=headers, data=data, files=files)
        
    if response.status_code != 200:
        print(f"Error from Groq API: {response.text}")
        return []
        
    res_json = response.json()
    segments = res_json.get('segments', [])
    
    sentences = []
    punc_chars = set('，。！？；：,.!?;:')
    
    for seg in segments:
        text = seg.get('text', '').strip()
        start = seg.get('start', 0.0)
        end = seg.get('end', 0.0)
        
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
            sentences.append(current_sentence)
            
    return sentences

def main():
    video_url = os.environ.get('VIDEO_URL')
    if not video_url:
        print("Error: VIDEO_URL environment variable is not set.")
        sys.exit(1)
        
    setup_cloudinary()
    
    video_path = download_video(video_url)
    cloud_video_url = upload_to_cloudinary(video_path)
    
    audio_path = extract_audio(video_path)
    subtitles = process_whisper_groq(audio_path)
    
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
