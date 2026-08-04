// Cloudflare Worker Script
// This script receives the webhook from Telegram and triggers the GitHub Action

export default {
  async fetch(request, env, ctx) {
    // Only accept POST requests from Telegram
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    try {
      const update = await request.json();

      // Check if there is a message with text
      if (update.message && update.message.text) {
        const text = update.message.text;
        
        // Simple regex to extract URL from the message
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const urls = text.match(urlRegex);

        if (urls && urls.length > 0) {
          const videoUrl = urls[0];
          
          const promptMessage = `💡 **BƯỚC 1: BÓC BĂNG VIDEO**\n\nBạn hãy mở **Antigravity IDE** trên máy tính lên, copy câu lệnh dưới đây và gửi cho AI:\n\n👉 *"Tớ muốn làm bài học từ video này: ${videoUrl}\nCậu hãy chạy file process_video.py để tải video và bóc băng lưu vào data.json giúp tớ nhé!"*`;
          
          await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, update.message.chat.id, promptMessage);
          return new Response("OK", { status: 200 });
        } else if (text === "STEP_2") {
          const promptMessage = "💡 **BƯỚC 2: PHÂN TÍCH HỌC THUẬT**\n\nBạn hãy mở **Antigravity IDE** lên, copy câu lệnh dưới đây và gửi cho AI:\n\n👉 *\"Tớ vừa bóc xong phụ đề video mới lưu ở file public/data.json, cậu hãy tiến hành dịch thuật Hán - Việt, phân tích ngữ pháp, Hán Nôm, tô màu từ vựng và cập nhật file giúp tớ nhé!\"*";
          await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, update.message.chat.id, promptMessage);
          return new Response("OK", { status: 200 });
        } else {
          // No URL found in message
          await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, update.message.chat.id, "Vui lòng gửi cho tôi một đường link video hợp lệ (YouTube, TikTok, Douyin...).");
          return new Response("OK", { status: 200 });
        }
      }

      return new Response("OK", { status: 200 });
    } catch (e) {
      return new Response(e.toString(), { status: 500 });
    }
  },
};

async function sendTelegramMessage(token, chatId, text) {
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      chat_id: chatId,
      text: text,
    })
  });
}
