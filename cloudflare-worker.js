export default {
  async fetch(request, env, ctx) {
    // Chỉ chấp nhận POST request từ Telegram
    if (request.method !== "POST") {
      return new Response("Antigravity Orchestrator is running!");
    }

    const payload = await request.json();

    // ----------------------------------------------------
    // HÀM TIỆN ÍCH: GỬI TIN NHẮN TELEGRAM
    // ----------------------------------------------------
    const sendMessage = async (chat_id, text, reply_markup = null) => {
      const url = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
      const body = { chat_id, text, parse_mode: "HTML" };
      if (reply_markup) body.reply_markup = reply_markup;
      
      await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
    };

    // ----------------------------------------------------
    // HÀM TIỆN ÍCH: KÍCH HOẠT GITHUB ACTIONS (BƯỚC 1 & 3)
    // ----------------------------------------------------
    const triggerGithubAction = async (eventType, clientPayload) => {
      const url = `https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`;
      await fetch(url, {
        method: "POST",
        headers: {
          "Accept": "application/vnd.github.v3+json",
          "Authorization": `Bearer ${env.GITHUB_PAT}`,
          "User-Agent": "Cloudflare-Worker"
        },
        body: JSON.stringify({
          event_type: eventType,
          client_payload: clientPayload
        })
      });
    };

    // ====================================================
    // XỬ LÝ SỰ KIỆN: BẤM NÚT (CALLBACK QUERIES)
    // ====================================================
    if (payload.callback_query) {
      const chatId = payload.callback_query.message.chat.id;
      const data = payload.callback_query.data;

      // XỬ LÝ BƯỚC 2: ANTIGRAVITY LOCAL
      if (data === "STEP_2") {
        const promptMessage = "💡 **BƯỚC 2: PHÂN TÍCH HỌC THUẬT**\n\nBạn hãy mở **Antigravity IDE** lên, copy câu lệnh dưới đây và gửi cho AI:\n\n👉 *\"Tớ vừa bóc xong phụ đề video mới lưu ở file public/data.json, cậu hãy tiến hành dịch thuật Hán - Việt, phân tích ngữ pháp, Hán Nôm, tô màu từ vựng và cập nhật file giúp tớ nhé!\"*";
        await sendMessage(chatId, promptMessage);
        return new Response("OK");
      }

      // XỬ LÝ BƯỚC 3: ĐÓNG GÓI TRÊN CLOUD
      if (data === "STEP_3") {
        await sendMessage(chatId, "🚀 Đang đóng gói bản HTML Thương Mại trên Đám mây. File sẽ sớm được gửi lại cho bạn!");
        await triggerGithubAction("process_video", { chat_id: chatId }); // Tuỳ biến event_type theo Workflow Bước 3 của bạn
        return new Response("OK");
      }
    }

    // ====================================================
    // XỬ LÝ SỰ KIỆN: GỬI TIN NHẮN TEXT (VIDEO LINK)
    // ====================================================
    if (payload.message && payload.message.text) {
      const chatId = payload.message.chat.id;
      const text = payload.message.text;

      // Nhận Link Video để kích hoạt Bước 1
      if (text.startsWith("http")) {
        // Tạo bàn phím điều khiển
        const keyboard = {
          inline_keyboard: [
            [{ text: "▶️ Bước 2: Dịch thuật (Local AI)", callback_data: "STEP_2" }],
            [{ text: "📦 Bước 3: Đóng gói HTML (Cloud)", callback_data: "STEP_3" }]
          ]
        };
        
        await sendMessage(chatId, "⏳ Đã nhận link! Đang kích hoạt FunASR trên Github để bóc bản thô. Hãy đợi 4 phút...", keyboard);
        
        // Sử dụng ctx.waitUntil để chạy ngầm, trả về 200 OK ngay lập tức cho Telegram để tránh bị lặp tin nhắn
        ctx.waitUntil(triggerGithubAction("process_video", { video_url: text, chat_id: chatId }));
      } 
      else if (text === "/start") {
        await sendMessage(chatId, "👋 Chào mừng Chủ tịch! Hãy ném link video vào đây để bắt đầu dây chuyền cào phím đại pháp.");
      }
      else {
        await sendMessage(chatId, "Vui lòng gửi một đường link video hợp lệ (bắt đầu bằng http)!");
      }
    }

    return new Response("OK", { status: 200 });
  }
};
