import os
import threading
import telebot
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Telegram Taixiu đang hoạt động 24/7!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

BOT_TOKEN = "8527232891:AAGrm_KA-2EwX6nj39DYSIXm_guMXxKSebg"
bot = telebot.TeleBot(BOT_TOKEN)

# DỮ LIỆU MẪU ĐỂ TEST BOT (Giả lập 10 phiên gần nhất từ API)
MOCK_DATA = [
    {"ketqua": "tai"}, {"ketqua": "tai"}, {"ketqua": "tai"},
    {"ketqua": "xiu"}, {"ketqua": "tai"}, {"ketqua": "tai"},
    {"ketqua": "tai"}, {"ketqua": "xiu"}, {"ketqua": "tai"}, {"ketqua": "tai"}
]

def thuat_toan_danh_gia(data_list):
    recent = data_list[:10]
    danh_sach_kq = [str(phien.get('ketqua', '')).lower() for phien in recent]
            
    tai_count = sum(1 for kq in danh_sach_kq if 'tai' in kq)
    xiu_count = sum(1 for kq in danh_sach_kq if 'xiu' in kq)
    
    total = len(danh_sach_kq)
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
    bot.reply_to(message, "Chào mừng bạn! Nhập lệnh /dudoan để nhận phân tích.")

@bot.message_handler(commands=['dudoan'])
def handle_dudoan(message):
    thong_bao = thuat_toan_danh_gia(MOCK_DATA)
    bot.send_message(message.chat.id, thong_bao, parse_mode="Markdown")

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Bot đang hoạt động...", flush=True)
    bot.infinity_polling(skip_pending=True)
