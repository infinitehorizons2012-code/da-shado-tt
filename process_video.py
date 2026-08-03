import os
import sys
import subprocess
import json
import cloudinary
import cloudinary.uploader
from funasr import AutoModel
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

def extract_audio(video_path, audio_path="audio.wav"):
    print("Extracting audio...")
    subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path, '-y'], check=True)
    return audio_path

def process_funasr(audio_path):
    print("Running FunASR...")
    # Initialize model
    model = AutoModel(
        model="paraformer-zh", 
        vad_model="fsmn-vad", 
        punc_model="ct-punc",
        disable_update=True
    )
    
    # Generate subtitles with timestamps
    res = model.generate(input=audio_path, batch_size_s=300, return_raw_text=False, timestamp=True)
    
    if not res or len(res) == 0:
        return []

    res_dict = res[0]
    text_with_punc = res_dict.get('text', '')
    timestamps = res_dict.get('timestamp', [])
    
    sentences = []
    current_sentence = []
    punc_chars = set('，。！？；：,.!?;:')
    end_chars = set('，。！？；：,.!?;:')
    
    timestamp_idx = 0
    for char in text_with_punc:
        if char in punc_chars:
            if current_sentence:
                current_sentence[-1]['word'] += char
            # Break sentence if it's an ending punctuation
            if char in end_chars:
                if current_sentence:
                    sentences.append(current_sentence)
                    current_sentence = []
        else:
            if timestamp_idx < len(timestamps):
                ts = timestamps[timestamp_idx]
                start_time = ts[0] / 1000.0  # Convert to seconds
                end_time = ts[1] / 1000.0
                
                # Get Pinyin
                pinyin_list = pypinyin.pinyin(char, style=pypinyin.Style.TONE)
                py = pinyin_list[0][0] if pinyin_list else ""
                
                word_info = {
                    "word": char,
                    "pinyin": py,
                    "start": round(start_time, 2),
                    "end": round(end_time, 2),
                    "confidence": 0.99  # Mocked as paraformer doesn't easily output word-level conf
                }
                current_sentence.append(word_info)
                timestamp_idx += 1
                
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
    subtitles = process_funasr(audio_path)
    
    # Structure the final JSON
    final_data = {
        "video_url": cloud_video_url,
        "subtitles": subtitles
    }
    
    # Save to public/data.json
    os.makedirs('public', exist_ok=True)
    with open('public/data.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
        
    print("Processing complete. Data saved to public/data.json")

if __name__ == "__main__":
    main()
