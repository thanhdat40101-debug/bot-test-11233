import os
import time
import threading
import requests
import telebot
from flask import Flask

# 1. KHỞI TẠO WEB SERVER (FLASK)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Telegram Taixiu Auto đang hoạt động 24/7!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# 2. CẤU HÌNH BOT TELEGRAM
BOT_TOKEN = "8527232891:AAGrm_KA-2EwX6nj39DYSIXm_guMXxKSebg"

# 👉 Thay CHAT_ID của bạn/nhóm vào đây (Ví dụ: "-1001234567890" hoặc "123456789")
CHAT_ID = "DIEN_CHAT_ID_CUA_BAN_VAO_DAY"

bot = telebot.TeleBot(BOT_TOKEN)
API_LICH_SU = "https://bottele-production-4be9.up.railway.app/api/history/taixiu"

last_processed_phien = None
last_prediction = None
stats = {"thang": 0, "thua": 0}

def thuat_toan_du_doan(recent_data):
    danh_sach_kq = []
    cau_list = []
    for phien in recent_data:
        if isinstance(phien, dict):
            kq = str(phien.get('Ket_qua') or phien.get('ketqua') or '').lower()
        else:
            kq = str(phien).lower()

        if 'tai' in kq or 'tài' in kq:
            danh_sach_kq.append('tai')
            cau_list.append('🔴')
        elif 'xiu' in kq or 'xỉu' in kq:
            danh_sach_kq.append('xiu')
            cau_list.append('🔵')

    tai_count = danh_sach_kq.count('tai')
    xiu_count = danh_sach_kq.count('xiu')
    total = len(danh_sach_kq) if len(danh_sach_kq) > 0 else 1

    rate_tai = round((tai_count / total) * 100)
    rate_xiu = round((xiu_count / total) * 100)

    if tai_count >= 7:
        du_doan, dot_pred, do_tin_cay = "Xỉu", "🔵", 68
    elif xiu_count >= 7:
        du_doan, dot_pred, do_tin_cay = "Tài", "🔴", 68
    else:
        if rate_tai <= rate_xiu:
            du_doan, dot_pred = "Tài", "🔴"
            do_tin_cay = round(52 + (rate_xiu - rate_tai) / 2)
        else:
            du_doan, dot_pred = "Xỉu", "🔵"
            do_tin_cay = round(52 + (rate_tai - rate_xiu) / 2)

    do_tin_cay = max(50, min(do_tin_cay, 85))
    cau_string = "".join(reversed(cau_list[:7]))
    return du_doan, dot_pred, rate_tai, rate_xiu, do_tin_cay, cau_string

# 3. VÒNG LẶP AUTO QUÉT PHIÊN MỚI
def auto_loop():
    global last_processed_phien, last_prediction, stats
    while True:
        try:
            if CHAT_ID and CHAT_ID != "DIEN_CHAT_ID_CUA_BAN_VAO_DAY":
                res = requests.get(API_LICH_SU, timeout=7)
                if res.status_code == 200:
                    data = res.json()
                    history = data.get('history', []) if isinstance(data, dict) else data

                    if history and isinstance(history, list):
                        latest = history[0]
                        phien_curr = latest.get('Phien')
                        xx1 = latest.get('Xuc_xac_1', 0)
                        xx2 = latest.get('Xuc_xac_2', 0)
                        xx3 = latest.get('Xuc_xac_3', 0)
                        tong = latest.get('Tong', 0)
                        kq_curr = str(latest.get('Ket_qua', ''))

                        if phien_curr and phien_curr != last_processed_phien:
                            if last_prediction is not None:
                                is_win = (last_prediction.lower() in kq_curr.lower())
                                if is_win:
                                    stats["thang"] += 1
                                    status_str = "✅ THẮNG DỰ ĐOÁN"
                                else:
                                    stats["thua"] += 1
                                    status_str = "❌ SAI DỰ ĐOÁN"

                                tong_phien = stats["thang"] + stats["thua"]
                                ty_le_dung = round((stats["thang"] / tong_phien) * 100, 1) if tong_phien > 0 else 0

                                msg_result = (
                                    f"╭━━━ KẾT QUẢ PHIÊN ━━━╮\n"
                                    f" Phiên: {phien_curr}\n"
                                    f" Xúc xắc: {xx1} · {xx2} · {xx3} → tổng {tong}\n"
                                    f" Kết quả: {kq_curr}\n"
                                    f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n"
                                    f"{status_str}\n\n"
                                    f"📊 Thành tích: {stats['thang']} thắng · {stats['thua']} thua · Tổng {tong_phien} phiên\n"
                                    f"🎯 Tỷ lệ đúng: {ty_le_dung}%"
                                )
                                bot.send_message(CHAT_ID, msg_result)

                            du_doan, dot_pred, rate_tai, rate_xiu, do_tin_cay, cau_string = thuat_toan_du_doan(history[:10])
                            phien_next = phien_curr + 1 if isinstance(phien_curr, int) else "N/A"

                            msg_predict = (
                                f"╭━━━ 🤖 TÀI XỈU MD5 🤖 ━━━╮\n"
                                f" 1️⃣2️⃣ Phiên kế tiếp: {phien_next}\n\n"
                                f" 🎯 Dự đoán: {du_doan} {dot_pred}\n\n"
                                f" ⚖️ Điểm: Tài {rate_tai}% · Xỉu {rate_xiu}%\n"
                                f" 📊 Độ tin cậy: {do_tin_cay}%\n"
                                f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n"
                                f"🌐 Cầu: {cau_string}\n"
                                f"🎮 bot_vnss"
                            )
                            bot.send_message(CHAT_ID, msg_predict)

                            last_prediction = du_doan
                            last_processed_phien = phien_curr
        except Exception as e:
            print(f"Lỗi Auto Loop: {e}", flush=True)

        time.sleep(10)

@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"CHAT ID của bạn/nhóm này là: `{message.chat.id}`", parse_mode="Markdown")

# 4. CHẠY CHƯƠNG TRÌNH
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    auto_thread = threading.Thread(target=auto_loop, daemon=True)
    auto_thread.start()

    print("Bot Auto đang hoạt động 24/7...", flush=True)
    bot.infinity_polling(skip_pending=True)
