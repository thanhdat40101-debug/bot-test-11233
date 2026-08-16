import os
import time
import threading
import requests
import telebot
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot đang hoạt động!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

BOT_TOKEN = "8527232891:AAGrm_KA-2EwX6nj39DYSIXm_guMXxKSebg"
CHAT_ID = ""  # Điền CHAT_ID dạng số nếu muốn bot tự bắn tin nhắn

bot = telebot.TeleBot(BOT_TOKEN)
API_LICH_SU = "https://bottele-production-4be9.up.railway.app/api/history/taixiu"

def get_data_and_predict():
    try:
        res = requests.get(API_LICH_SU, timeout=5)
        if res.status_code == 200:
            data = res.json()
            history = data.get('history', []) if isinstance(data, dict) else data
            if history and isinstance(history, list):
                latest = history[0]
                phien = latest.get('Phien', 'N/A')
                xx1 = latest.get('Xuc_xac_1', 0)
                xx2 = latest.get('Xuc_xac_2', 0)
                xx3 = latest.get('Xuc_xac_3', 0)
                tong = latest.get('Tong', 0)
                kq = str(latest.get('Ket_qua', ''))

                # Tính tỷ lệ
                tai_c = sum(1 for p in history[:10] if 'tai' in str(p.get('Ket_qua','')).lower())
                xiu_c = len(history[:10]) - tai_c
                r_tai, r_xiu = round(tai_c*10), round(xiu_c*10)
                du_doan = "Tài 🔴" if r_tai <= r_xiu else "Xỉu 🔵"

                msg = (
                    f"╭━━━ KẾT QUẢ PHIÊN ━━━╮\n"
                    f" Phiên: {phien}\n"
                    f" Xúc xắc: {xx1} · {xx2} · {xx3} → Tổng {tong}\n"
                    f" Kết quả: {kq}\n"
                    f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                    f"╭━━━ 🤖 DỰ ĐOÁN MD5 🤖 ━━━╮\n"
                    f" 🎯 Dự đoán phiên sau: {du_doan}\n"
                    f" ⚖️ Tỷ lệ: Tài {r_tai}% · Xỉu {r_xiu}%\n"
                    f"╰━━━━━━━━━━━━━━━━━━━━━━╯"
                )
                return msg
    except Exception as e:
        print(f"Lỗi API: {e}")
    return "❌ Không thể lấy dữ liệu từ API."

@app.route('/test')
def test():
    return "OK"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Gõ /dudoan để nhận kết quả phân tích mới nhất.")

@bot.message_handler(commands=['dudoan'])
def handle_dudoan(message):
    msg = get_data_and_predict()
    bot.send_message(message.chat.id, msg)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
