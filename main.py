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
    return "Bot Telegram Taixiu đang hoạt động 24/7!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# 2. CẤU HÌNH BOT TELEGRAM
BOT_TOKEN = "8527232891:AAGrm_KA-2EwX6nj39DYSIXm_guMXxKSebg"

# 👉 Nếu muốn Bot TỰ ĐỘNG gửi tin nhắn mỗi phiên mới, hãy điền CHAT_ID vào đây
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

def tao_tin_nhan_dudoan():
    res = requests.get(API_LICH_SU, timeout=7)
    if res.status_code == 200:
        data = res.json()
        history = data.get('history', []) if isinstance(data, dict) else data

        if history and isinstance(history, list):
            latest = history[0]
            phien_curr = latest.get('Phien', 0)
            xx1 = latest.get('Xuc_xac_1', 0)
            xx2 = latest.get('Xuc_xac_2', 0)
            xx3 = latest.get('Xuc_xac_3', 0)
            tong = latest.get('Tong', 0)
            kq_curr = str(latest.get('Ket_qua', ''))

            du_doan, dot_pred, rate_tai, rate_xiu, do_tin_cay, cau_string = thuat_toan_du_doan(history[:10])
            phien_next = phien_curr + 1 if isinstance(phien_curr, int) else "N/A"

            msg = (
                f"╭━━━ KẾT QUẢ PHIÊN ━━━╮\n"
                f" Phiên: {phien_curr}\n"
                f" Xúc xắc: {xx1} · {xx2} · {xx3} → tổng {tong}\n"
                f" Kết quả: {kq_curr}\n"
                f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                f"╭━━━ 🤖 TÀI XỈU MD5 🤖 ━━━╮\n"
                f" 1️⃣2️⃣ Phiên kế tiếp: {phien_next}\n\n"
                f" 🎯 Dự đoán: {du_doan} {dot_pred}\n\n"
                f" ⚖️ Điểm: Tài {rate_tai}% · Xỉu {rate_xiu}%\n"
                f" 📊 Độ tin cậy: {do_tin_cay}%\n"
                f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n"
                f"🌐 Cầu: {cau_string}\n"
                f"🎮 bot_vnss"
            )
            return msg, phien_curr, kq_curr, du_doan
    return None, None, None, None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Chào mừng bạn! Gõ /dudoan để xem phân tích hoặc /id để lấy Chat ID.")

@bot.message_handler(commands=['id'])
def get_id(message):
    bot.reply_to(message, f"CHAT ID của bạn là: `{message.chat.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['dudoan'])
def handle_dudoan(message):
    try:
        msg, _, _, _ = tao_tin_nhan_dudoan()
        if msg:
            bot.send_message(message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "❌ Lỗi kết nối API.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Lỗi: {e}")

# LUỒNG TỰ ĐỘNG BẮN TIN NHẮN
def auto_loop():
    global last_processed_phien, last_prediction, stats
    while True:
        try:
            if CHAT_ID and CHAT_ID != "DIEN_CHAT_ID_CUA_BAN_VAO_DAY":
                msg, phien_curr, kq_curr, du_doan = tao_tin_nhan_dudoan()
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
                            f"{status_str}\n"
                            f"📊 Thành tích: {stats['thang']} thắng · {stats['thua']} thua ({ty_le_dung}%)"
                        )
                        bot.send_message(CHAT_ID, msg_result)

                    if msg:
                        bot.send_message(CHAT_ID, msg)

                    last_prediction = du_doan
                    last_processed_phien = phien_curr
        except Exception as e:
            print(f"Lỗi Auto: {e}", flush=True)

        time.sleep(10)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    auto_thread = threading.Thread(target=auto_loop, daemon=True)
    auto_thread.start()

    print("Bot đang hoạt động...", flush=True)
    bot.infinity_polling(skip_pending=True)
