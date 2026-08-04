from fastapi import FastAPI, BackgroundTasks, Request
import subprocess
import uvicorn
import os

app = FastAPI()

# You might need to change "antigravity" to the full path like r"C:\Program Files\Antigravity\antigravity.exe"
# if it is not in your System PATH.
ANTIGRAVITY_CMD = "antigravity"
WORKSPACE_PATH = r"C:\Users\DT.HANG\Downloads\da sha tt"

def trigger_antigravity():
    print("Bóp cò! Đang khởi tạo Antigravity Agent...")
    prompt = "Tớ vừa cào xong video mới, cậu tiến hành git pull lấy dữ liệu về, dịch tiếng Việt, tô màu và đóng gói HTML giúp tớ nhé!"
    
    try:
        # Chạy Antigravity dưới dạng tiến trình độc lập (Isolated Process)
        subprocess.Popen([
            ANTIGRAVITY_CMD, "run", prompt,
            "--workspace", WORKSPACE_PATH
        ], creationflags=subprocess.CREATE_NEW_CONSOLE) # Mở cửa sổ CMD mới trên Windows
        print("🚀 Tiến trình Antigravity đã được mở thành công!")
    except Exception as e:
        print(f"❌ Lỗi khi khởi động Antigravity: {e}")

@app.post("/webhook-step2")
async def step2_webhook(request: Request, background_tasks: BackgroundTasks):
    print("Nhận được tín hiệu từ Đám mây (Telegram/Cloudflare)!")
    background_tasks.add_task(trigger_antigravity)
    return {"status": "success", "message": "Antigravity isolated process started!"}

if __name__ == "__main__":
    print("📡 Trạm Gác (Local Bridge) đã khởi động tại cổng 8000...")
    print("Chờ lệnh từ Ngrok...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
