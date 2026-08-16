import os
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

# 2. KHỞI TẠO TELEGRAM BOT
BOT_TOKEN = "8527232891:AAGrm_KA-2EwX6nj39DYSIXm_guMXxKSebg"
bot = telebot.TeleBot(BOT_TOKEN)

API_LICH_SU = "https://bottele-production-4be9.up.railway.app/api/history/taixiu"

def thuat_toan_danh_gia(data_list):
    if not data_list or not isinstance(data_list, list):
        return None

    recent = data_list[:10]
    danh_sach_kq = []
    
    for phien in recent:
        if isinstance(phien, dict):
            kq = phien.get('ketqua') or phien.get('result') or phien.get('kq') or ''
        else:
            kq = str(phien)
            
        if kq:
            danh_sach_kq.append(str(kq).lower())
            
    tai_count = sum(1 for kq in danh_sach_kq if 'tai' in kq or 'tài' in kq)
    xiu_count = sum(1 for kq in danh_sach_kq if 'xiu' in kq or 'xỉu' in kq)
    
    total = len(danh_sach_kq)
    if total == 0:
        return None

    rate_tai = round((tai_count / total) * 100)
    rate_xiu = round((xiu_count / total) * 100)

    if tai_count >= 7:
        du_doan = "Xỉu (Cầu lệch nghiêng về Tài, xu hướng bẻ Xỉu)"
    elif xiu_count >= 7:
        du_doan = "Tài (Cầu lệch nghiêng về Xỉu, xu hướng bẻ Tài)"
    else:
        du_doan = "Tài" if rate_tai <= rate_xiu else "Xỉu"

    return (
        f"📊 **KẾT QUẢ PHÂN TÍCH 10 PHIÊN GẦN NHẤT**\n"
        f"• Tỷ lệ Tài: {rate_tai}%\n"
        f"• Tỷ lệ Xỉu: {rate_xiu}%\n"
        f"-------------------------------------\n"
        f"🔮 **Dự đoán phiên tiếp theo:** **{du_doan}**"
    )

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Chào mừng bạn! Nhập lệnh /dudoan để nhận phân tích thuật toán từ API.")

@bot.message_handler(commands=['dudoan'])
def handle_dudoan(message):
    try:
        res = requests.get(API_LICH_SU, timeout=7)
        if res.status_code == 200:
            data = res.json()
            
            data_list = []
            if isinstance(data, list):
                data_list = data
            elif isinstance(data, dict):
                data_list = data.get('data') or data.get('history') or data.get('results') or data.get('list') or []

            thong_bao = thuat_toan_danh_gia(data_list)
            
            if thong_bao:
                bot.send_message(message.chat.id, thong_bao, parse_mode="Markdown")
            else:
                bot.send_message(message.chat.id, f"⚠️ API trả về dữ liệu rỗng/chưa đúng cấu trúc:\n`{str(data)[:200]}`", parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"❌ Máy chủ API báo lỗi HTTP: {res.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Lỗi kết nối API: {e}")

# 3. CHẠY ĐA LUỒNG
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Bot đang hoạt động...", flush=True)
    bot.infinity_polling(skip_pending=True)
