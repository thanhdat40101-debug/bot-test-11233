import os
import time
import threading
import requests
import telebot
from flask import Flask

# -------------------------------------------------------------
# CẤU HÌNH BOT TELEGRAM
# -------------------------------------------------------------
BOT_TOKEN = "8463492839:AAGgzUV1a7O_8pzt6ZQ8wFLpTG_GrXFF4qI"
CHAT_ID = "6285849261"
API_MD5 = "https://bottele-production-4be9.up.railway.app/api/history/md5"

# -------------------------------------------------------------
# ENGINE PHÂN TÍCH CHUỖI HEX MD5 (MD5 HASH PARSER)
# -------------------------------------------------------------
class MD5HashEngine:
    def parse_md5_features(self, md5_str):
        """Bóc tách chuỗi MD5 32 ký tựHex thành thông số toán học"""
        if not md5_str or len(md5_str) < 32 or md5_str == 'N/A':
            return 50, 50, "Mã MD5 không khả dụng - Dùng mặc định"

        # 1. Trích xuất 8 ký tự Hex cuối
        last_8 = md5_str[-8:]
        hex_val = int(last_8, 16)
        
        # 2. Tính mật độ bit (Bit Parity)
        binary_str = bin(hex_val)[2:].zfill(32)
        ones_count = binary_str.count('1')
        
        # 3. Phân tích XOR Checksum giữa 4 khối Hex (mỗi khối 8 ký tự)
        b1 = int(md5_str[0:8], 16)
        b2 = int(md5_str[8:16], 16)
        b3 = int(md5_str[16:24], 16)
        b4 = int(md5_str[24:32], 16)
        xor_checksum = b1 ^ b2 ^ b3 ^ b4
        
        # 4. Tính toán trọng số Tài / Xỉu dựa trên MD5 Hex
        mod_score = hex_val % 100
        tai_weight = (mod_score * 0.4) + ((ones_count / 32.0) * 100 * 0.4) + ((xor_checksum % 100) * 0.2)
        
        p_tai = round(max(15, min(85, tai_weight)))
        p_xiu = 100 - p_tai
        
        ly_do = f"MD5 XOR: `{hex(xor_checksum)[-6:]}` | Mật độ Bit 1: {ones_count}/32 | Hex Mod: {mod_score}"
        return p_tai, p_xiu, ly_do

    def analyze(self, history):
        data = []
        for p in history:
            if not isinstance(p, dict): continue
            tong = p.get('Tong') or p.get('tong') or 0
            ma_md5 = p.get('Ma_hash') or p.get('md5') or p.get('hash') or p.get('MD5') or ''
            if tong > 0:
                is_tai = 1 if tong >= 11 else 0
            else:
                kq = str(p.get('Ket_qua', '')).lower()
                is_tai = 1 if 'tai' in kq or 't' in kq else 0
                tong = 11 if is_tai else 8
            data.append({'is_tai': is_tai, 'tong': tong, 'md5': ma_md5})

        if not data:
            return "Tài", "🔴", 50, 50, 50, "⚪", ["Chờ dữ liệu"]

        # Phân tích chuỗi MD5 phiên mới nhất
        latest_md5 = data[0]['md5']
        p_tai_hash, p_xiu_hash, ly_do_hash = self.parse_md5_features(latest_md5)

        # Trọng số lịch sử 3 phiên gần nhất (30% tỷ trọng)
        short_trend = sum(d['is_tai'] for d in data[:3])
        
        # Tổng hợp lực chọn (70% từ mã MD5 Hex, 30% từ xu hướng phiên)
        final_tai = (p_tai_hash * 0.7) + ((short_trend / 3.0) * 100 * 0.3)
        final_xiu = 100 - final_tai
        
        p_tai = round(max(10, min(90, final_tai)))
        p_xiu = 100 - p_tai
        
        confidence = max(p_tai, p_xiu)
        du_doan = "Tài" if p_tai > p_xiu else "Xỉu"
        dot = "🔴" if du_doan == "Tài" else "🔵"
        
        cau_list = ["🔴" if d['is_tai'] == 1 else "🔵" for d in data[:7]]
        cau_str = "".join(reversed(cau_list))

        return du_doan, dot, p_tai, p_xiu, confidence, cau_str, [ly_do_hash]

# Khởi tạo Engine
engine = MD5HashEngine()

# -------------------------------------------------------------
# FLASK & TELEGRAM BOT AUTOMATION
# -------------------------------------------------------------
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

last_phien = None
last_predict = None
stats = {"thang": 0, "thua": 0}

@app.route('/')
def home():
    return "Bot MD5 Hex Parsing Engine Online 24/7!"

def auto_process():
    global last_phien, last_predict, stats
    while True:
        try:
            res = requests.get(API_MD5, timeout=6)
            if res.status_code == 200:
                data = res.json()
                history = data.get('history', []) if isinstance(data, dict) else data

                if history and isinstance(history, list):
                    curr = history[0]
                    phien = curr.get('Phien') or curr.get('phien')
                    xx1 = curr.get('Xuc_xac_1', 0)
                    xx2 = curr.get('Xuc_xac_2', 0)
                    xx3 = curr.get('Xuc_xac_3', 0)
                    tong = curr.get('Tong', 0)
                    kq = str(curr.get('Ket_qua') or curr.get('ketqua') or '')
                    ma_md5 = curr.get('Ma_hash') or curr.get('md5') or curr.get('hash') or curr.get('MD5') or 'Chưa cập nhật'

                    if phien and phien != last_phien:
                        status_eval = ""
                        if last_predict:
                            is_win = False
                            if tong >= 11 and last_predict == "Tài": is_win = True
                            elif 3 <= tong <= 10 and last_predict == "Xỉu": is_win = True
                            elif last_predict.lower() in kq.lower(): is_win = True

                            if is_win:
                                stats["thang"] += 1
                                status_eval = "\n ✅ ĐÁNH GIÁ: THẮNG"
                            else:
                                stats["thua"] += 1
                                status_eval = "\n ❌ ĐÁNH GIÁ: THUA"

                        tong_p = stats["thang"] + stats["thua"]
                        rate_win = round((stats["thang"] / tong_p) * 100, 1) if tong_p > 0 else 0

                        # Gọi thuật toán phân tích MD5 Hex
                        du_doan, dot, r_tai, r_xiu, do_tin_cay, cau_str, ly_do = engine.analyze(history)
                        phien_next = phien + 1 if isinstance(phien, int) else "N/A"

                        str_ly_do = "\n".join(f"• {ld}" for ld in ly_do)

                        msg = (
                            f"╭━━━ KẾT QUẢ SẢNH MD5 ━━━╮\n"
                            f" 📌 Phiên: {phien}\n"
                            f" 🎲 Xúc xắc: {xx1} · {xx2} · {xx3} → Tổng {tong}\n"
                            f" 🔑 Mã MD5: `{ma_md5}`\n"
                            f" 🎯 Kết quả: {kq}{status_eval}\n"
                            f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                            f"╭━━━ 🤖 DỰ ĐOÁN MD5 HEX 🤖 ━━━╮\n"
                            f" 1️⃣2️⃣ Phiên kế tiếp: {phien_next}\n\n"
                            f" 🎯 Dự đoán: {du_doan} {dot}\n"
                            f" 📊 Độ tin cậy: {do_tin_cay}%\n"
                            f" ⚖️ Trọng số MD5: Tài {r_tai}% · Xỉu {r_xiu}%\n"
                            f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n"
                            f"💡 **Cơ sở Hex MD5:**\n{str_ly_do}\n\n"
                            f"🌐 Cầu: {cau_str}\n"
                            f"📊 Thành tích: {stats['thang']} Thắng · {stats['thua']} Thua ({rate_win}%)\n"
                            f"🎮 MD5 Hex Parsing Engine Active"
                        )

                        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                        last_predict = du_doan
                        last_phien = phien
        except Exception as e:
            print(f"Lỗi Auto Loop MD5: {e}", flush=True)

        time.sleep(7)

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    bot.reply_to(message, "Bot MD5 Hex Engine đã sẵn sàng!")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    threading.Thread(target=auto_process, daemon=True).start()
    print("Khởi chạy MD5 Hex Processing Bot...", flush=True)
    bot.infinity_polling(skip_pending=True)
    
