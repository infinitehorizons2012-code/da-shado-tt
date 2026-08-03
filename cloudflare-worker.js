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

          // Trigger GitHub Repository Dispatch
          // NOTE: Replace 'infinitehorizons2012-code' and 'da-shado-tt' with your actual username and repo name if different
          const githubRepoUrl = `https://api.github.com/repos/infinitehorizons2012-code/da-shado-tt/dispatches`;
          
          const githubResponse = await fetch(githubRepoUrl, {
            method: 'POST',
            headers: {
              'Accept': 'application/vnd.github.v3+json',
              'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
              'Content-Type': 'application/json',
              'User-Agent': 'Cloudflare-Worker'
            },
            body: JSON.stringify({
              event_type: 'process_video',
              client_payload: {
                video_url: videoUrl
              }
            })
          });

          if (githubResponse.ok) {
            // Reply back to Telegram
            await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, update.message.chat.id, "Đã nhận link! Hệ thống đang xử lý và sẽ đẩy lên web sau ít phút.");
            return new Response("OK", { status: 200 });
          } else {
            const errorText = await githubResponse.text();
            await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, update.message.chat.id, `Lỗi khi gọi GitHub: ${errorText}`);
            return new Response("GitHub Error", { status: 500 });
          }
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
