import os
import threading
import requests
import telebot
from flask import Flask

# -------------------------------------------------------------
# 1. KHỞI TẠO WEB SERVER (FLASK)
# -------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Telegram Taixiu đang hoạt động 24/7!"

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# -------------------------------------------------------------
# 2. KHỞI TẠO TELEGRAM BOT
# -------------------------------------------------------------
BOT_TOKEN = "8527232891:AAGrm_KA-2EwX6nj39DYSIXm_guMXxKSebg"
bot = telebot.TeleBot(BOT_TOKEN)

API_LICH_SU = "https://bottele-production-4be9.up.railway.app/api/history/taixiu"

def tao_giao_dien_phan_tich(data_list):
    if not data_list or not isinstance(data_list, list):
        return None

    recent = data_list[:10]
    
    # 1. Lấy thông tin phiên vừa kết thúc
    latest = recent[0]
    phien_curr = latest.get('Phien', 0)
    xx1 = latest.get('Xuc_xac_1', 0)
    xx2 = latest.get('Xuc_xac_2', 0)
    xx3 = latest.get('Xuc_xac_3', 0)
    tong = latest.get('Tong', 0)
    kq_curr = latest.get('Ket_qua', '')

    # 2. Tính số phiên tiếp theo
    phien_next = phien_curr + 1 if isinstance(phien_curr, int) else "N/A"

    # 3. Xử lý dữ liệu lịch sử & tạo chuỗi Cầu (🔴 = Tài, 🔵 = Xỉu)
    danh_sach_kq = []
    cau_list = []
    
    for phien in recent:
        kq = str(phien.get('Ket_qua') or phien.get('ketqua') or '').lower()
        if 'tai' in kq or 'tài' in kq:
            danh_sach_kq.append('tai')
            cau_list.append('🔴')
        elif 'xiu' in kq or 'xỉu' in kq:
            danh_sach_kq.append('xiu')
            cau_list.append('🔵')

    # Đảo ngược danh sách cầu để hiển thị theo thứ tự thời gian (từ cũ đến mới)
    cau_string = "".join(reversed(cau_list[:7]))

    # 4. Tính toán tỷ lệ % Tài/Xỉu
    total = len(danh_sach_kq)
    if total == 0:
        return None

    tai_count = danh_sach_kq.count('tai')
    xiu_count = danh_sach_kq.count('xiu')

    rate_tai = round((tai_count / total) * 100)
    rate_xiu = round((xiu_count / total) * 100)

    # 5. Thuật toán đưa ra dự đoán & Độ tin cậy
    if tai_count >= 7:
        du_doan = "Xỉu"
        dot_pred = "🔵"
        do_tin_cay = 68
    elif xiu_count >= 7:
        du_doan = "Tài"
        dot_pred = "🔴"
        do_tin_cay = 68
    else:
        if rate_tai <= rate_xiu:
            du_doan = "Tài"
            dot_pred = "🔴"
            do_tin_cay = round(52 + (rate_xiu - rate_tai) / 2)
        else:
            du_doan = "Xỉu"
            dot_pred = "🔵"
            do_tin_cay = round(52 + (rate_tai - rate_xiu) / 2)

    do_tin_cay = max(50, min(do_tin_cay, 85))

    # 6. Định dạng khung hiển thị chuẩn theo ảnh mẫu
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
    return msg

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Chào mừng bạn! Nhập lệnh /dudoan để nhận phân tích thuật toán từ API.")

@bot.message_handler(commands=['dudoan'])
def handle_dudoan(message):
    try:
        res = requests.get(API_LICH_SU, timeout=7)
        if res.status_code == 200:
            data = res.json()
            data_list = data.get('history', []) if isinstance(data, dict) else data

            thong_bao = tao_giao_dien_phan_tich(data_list)
            
            if thong_bao:
                bot.send_message(message.chat.id, thong_bao)
            else:
                bot.send_message(message.chat.id, "⚠️ Dữ liệu trả về không đúng định dạng.")
        else:
            bot.send_message(message.chat.id, f"❌ Máy chủ API báo lỗi HTTP: {res.status_code}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Lỗi kết nối API: {e}")

# -------------------------------------------------------------
# 3. KÍCH HOẠT ĐA LUỒNG
# -------------------------------------------------------------
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Bot đang hoạt động...", flush=True)
    bot.infinity_polling(skip_pending=True)
