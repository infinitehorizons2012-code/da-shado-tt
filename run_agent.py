import asyncio
import sys
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
from google.antigravity.utils.interactive import run_interactive_loop

async def main():
    import os
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY").startswith("sk-dummy"):
        print("\n🔑 CHÚ Ý: Bạn chưa cấu hình GEMINI_API_KEY!")
        print("Vui lòng lấy API Key miễn phí tại: https://aistudio.google.com/app/apikey")
        key = input("Dán API Key của bạn vào đây và bấm Enter: ").strip()
        os.environ["GEMINI_API_KEY"] = key

    print("🚀 Đang nạp bộ não Google Antigravity...")
    # Bật full quyền (có thể chạy lệnh git, python, sửa file)
    config = LocalAgentConfig(
        system_instructions="Bạn là một trợ lý AI chuyên nghiệp phụ trách việc xử lý phụ đề, dịch thuật và đóng gói file HTML.",
        capabilities=CapabilitiesConfig()
    )

    async with Agent(config) as agent:
        print("🤖 Antigravity AI đã sẵn sàng! Đang bắt đầu làm việc tự động...")
        print("-" * 50)
        
        prompt = "Tớ vừa cào xong video mới, cậu tiến hành git pull lấy dữ liệu về, dịch tiếng Việt, tô màu và đóng gói HTML giúp tớ nhé!"
        print(f">> USER: {prompt}")
        print(">> ANTIGRAVITY: ", end="")
        
        # Gửi lệnh tự động và stream kết quả
        response = await agent.chat(prompt)
        async for token in response:
            sys.stdout.write(token)
            sys.stdout.flush()
            
        print("\n" + "-" * 50)
        print("✅ Đã hoàn thành tác vụ tự động! Cửa sổ này vẫn đang mở.")
        print("Bạn có thể gõ thêm lệnh (Ví dụ: 'Sửa câu 21 thành ...') hoặc gõ /exit để thoát.")
        
        # Chuyển sang chế độ trò chuyện tương tác
        await run_interactive_loop(agent)

if __name__ == "__main__":
    asyncio.run(main())
