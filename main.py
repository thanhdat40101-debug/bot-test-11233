import os
import time
import threading
import requests
import telebot
from flask import Flask

# Cấu hình
BOT_TOKEN = "8527232891:AAGrm_KA-2EwX6nj39DYSIXm_guMXxKSebg"
CHAT_ID = "6285849261" # ID của bạn
API_LICH_SU = "https://bottele-production-4be9.up.railway.app/api/history/taixiu"

# Khởi tạo
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
last_processed_phien = None
last_prediction = None
stats = {"thang": 0, "thua": 0}

@app.route('/')
def home():
    return "Bot đang hoạt động!"

def thuat_toan_du_doan(history):
    danh_sach_kq = [str(p.get('Ket_qua', '')).lower() for p in history]
    tai_count = sum(1 for k in danh_sach_kq if 'tai' in k)
    xiu_count = len(danh_sach_kq) - tai_count
    
    # Dự đoán
    if tai_count >= 6: du_doan, dot = "Xỉu", "🔵"
    else: du_doan, dot = "Tài", "🔴"
    
    rate_tai = round((tai_count / len(danh_sach_kq)) * 100)
    rate_xiu = round((xiu_count / len(danh_sach_kq)) * 100)
    return du_doan, dot, rate_tai, rate_xiu

def auto_loop():
    global last_processed_phien, last_prediction, stats
    while True:
        try:
            res = requests.get(API_LICH_SU, timeout=5)
            if res.status_code == 200:
                data = res.json()
                history = data.get('history', [])
                if history:
                    latest = history[0]
                    phien = latest.get('Phien')
                    
                    if phien != last_processed_phien:
                        # Kiểm tra thắng thua
                        status = ""
                        if last_prediction:
                            is_win = (last_prediction.lower() in str(latest.get('Ket_qua', '')).lower())
                            if is_win: 
                                stats["thang"] += 1
                                status = "\n✅ ĐÁNH GIÁ: THẮNG"
                            else: 
                                stats["thua"] += 1
                                status = "\n❌ ĐÁNH GIÁ: THUA"
                        
                        # Dự đoán phiên tiếp
                        du_doan, dot, r_tai, r_xiu = thuat_toan_du_doan(history[:10])
                        
                        msg = (
                            f"╭━━━ KẾT QUẢ PHIÊN ━━━╮\n"
                            f" Phiên: {phien}\n"
                            f" Kết quả: {latest.get('Ket_qua')}{status}\n"
                            f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                            f"╭━━━ 🤖 DỰ ĐOÁN 🤖 ━━━╮\n"
                            f" 🎯 Phiên sau: {du_doan} {dot}\n"
                            f" ⚖️ Tỷ lệ: Tài {r_tai}% · Xỉu {r_xiu}%\n"
                            f" 📊 Tổng: {stats['thang']} Thắng - {stats['thua']} Thua\n"
                            f"╰━━━━━━━━━━━━━━━━━━━━━━╯"
                        )
                        bot.send_message(CHAT_ID, msg)
                        last_prediction = du_doan
                        last_processed_phien = phien
        except: pass
        time.sleep(10)

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000))), daemon=True).start()
    threading.Thread(target=auto_loop, daemon=True).start()
    bot.infinity_polling()
