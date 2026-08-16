import os
import time
import threading
import requests
import telebot
import math
from flask import Flask

# -------------------------------------------------------------
# CẤU HÌNH BOT MD5 
# -------------------------------------------------------------
BOT_TOKEN = "8463492839:AAGgzUV1a7O_8pzt6ZQ8wFLpTG_GrXFF4qI"
CHAT_ID = "6285849261"
API_MD5 = "https://bottele-production-4be9.up.railway.app/api/history/md5"

# -------------------------------------------------------------
# SYSTEM ENGINE: SMART MARKOV & Z-SCORE (TOÁN HỌC THỐNG KÊ)
# -------------------------------------------------------------
class SmartMarkovEngine:
    def __init__(self):
        self.mu = 10.5 # Điểm trung bình lý thuyết của 3 xúc xắc (3-18)

    def calculate_z_score(self, data):
        if len(data) < 5:
            return 0
        
        # Lấy tổng điểm 5 phiên gần nhất
        scores = [d['tong'] for d in data[:5] if d['tong'] > 0]
        if not scores: return 0
        
        mean_current = sum(scores) / len(scores)
        variance = sum((x - mean_current) ** 2 for x in scores) / len(scores)
        std_dev = math.sqrt(variance) if variance > 0 else 1
        
        # Z-Score: Mức độ lệch khỏi trung bình lý thuyết
        z_score = (scores[0] - self.mu) / std_dev
        return z_score

    def build_markov_chain(self, data):
        if len(data) < 10:
            return {'T': {'T': 0.5, 'X': 0.5}, 'X': {'X': 0.5, 'T': 0.5}}
            
        transitions = {'TT': 0, 'TX': 0, 'XT': 0, 'XX': 0}
        
        # Quét lịch sử để xây ma trận chuyển đổi
        for i in range(len(data) - 1):
            curr = "T" if data[i+1]['is_tai'] else "X"
            next_state = "T" if data[i]['is_tai'] else "X" # data[0] là mới nhất
            transitions[curr + next_state] += 1
            
        # Tính xác suất
        total_T = transitions['TT'] + transitions['TX']
        total_X = transitions['XT'] + transitions['XX']
        
        prob_T_to_T = transitions['TT'] / total_T if total_T > 0 else 0.5
        prob_T_to_X = transitions['TX'] / total_T if total_T > 0 else 0.5
        prob_X_to_X = transitions['XX'] / total_X if total_X > 0 else 0.5
        prob_X_to_T = transitions['XT'] / total_X if total_X > 0 else 0.5
        
        return {
            'T': {'T': prob_T_to_T, 'X': prob_T_to_X},
            'X': {'X': prob_X_to_X, 'T': prob_X_to_T}
        }

    def analyze(self, history):
        # 1. Làm sạch dữ liệu
        data = []
        for p in history:
            if not isinstance(p, dict): continue
            tong = p.get('Tong') or p.get('tong') or 0
            if tong > 0:
                is_tai = 1 if tong >= 11 else 0
            else:
                kq = str(p.get('Ket_qua', '')).lower()
                is_tai = 1 if 'tai' in kq or 't' in kq else 0
                tong = 11 if is_tai else 8
            data.append({'is_tai': is_tai, 'tong': tong})

        if len(data) < 10:
            return "Tài", "🔴", 50, 50, 50, "⚪", ["Đang thu thập thêm dữ liệu"]

        # 2. Lấy trạng thái hiện tại
        current_state = "T" if data[0]['is_tai'] == 1 else "X"
        
        # 3. Chạy Markov Chain
        markov_matrix = self.build_markov_chain(data[:20]) # Dùng 20 phiên gần nhất
        markov_prob_T = markov_matrix[current_state]['T'] * 100
        markov_prob_X = markov_matrix[current_state]['X'] * 100

        # 4. Tính điểm Z-Score (Mean Reversion)
        z_score = self.calculate_z_score(data)
        
        # 5. Cân bằng Trọng số (Kết hợp Markov và Z-Score)
        final_score_T = markov_prob_T
        final_score_X = markov_prob_X
        
        # Áp dụng Z-Score để điều chỉnh xu hướng
        if z_score > 1.5:
            final_score_X += 15
            final_score_T -= 15
            ly_do = f"Điểm đang quá cao (Z={z_score:.1f}) -> Hồi lưu về Xỉu"
        elif z_score < -1.5:
            final_score_T += 15
            final_score_X -= 15
            ly_do = f"Điểm đang quá thấp (Z={z_score:.1f}) -> Nảy lên Tài"
        else:
            ly_do = f"Phân tích Markov Chain (Từ {current_state})"

        # 6. Chốt tỷ lệ
        total_score = final_score_T + final_score_X
        if total_score == 0: total_score = 1
        p_tai = round(max(10, min(90, (final_score_T / total_score) * 100)))
        p_xiu = 100 - p_tai
        
        confidence = max(p_tai, p_xiu)
        du_doan = "Tài" if p_tai > p_xiu else "Xỉu"
        dot = "🔴" if du_doan == "Tài" else "🔵"
        
        # Chuỗi biểu tượng
        cau_list = ["🔴" if d['is_tai'] == 1 else "🔵" for d in data[:7]]
        cau_str = "".join(reversed(cau_list))

        return du_doan, dot, p_tai, p_xiu, confidence, cau_str, [ly_do]

# Khởi tạo Engine
engine = SmartMarkovEngine()

# -------------------------------------------------------------
# KHỞI TẠO BOT & FLASK SERVER
# -------------------------------------------------------------
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

last_phien = None
last_predict = None
stats = {"thang": 0, "thua": 0}

@app.route('/')
def home():
    return "Bot MD5 Smart Engine (Markov + Z-Score) đang chạy 24/7!"

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

                        # GỌI HỆ THỐNG SMART MARKOV & Z-SCORE
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
                            f"╭━━━ 🤖 DỰ ĐOÁN THÔNG MINH 🤖 ━━━╮\n"
                            f" 1️⃣2️⃣ Phiên kế tiếp: {phien_next}\n\n"
                            f" 🎯 Dự đoán: {du_doan} {dot}\n"
                            f" 📊 Độ tin cậy: {do_tin_cay}%\n"
                            f" ⚖️ Trọng số: Tài {r_tai}% · Xỉu {r_xiu}%\n"
                            f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n"
                            f"💡 **Lý do dự đoán:**\n{str_ly_do}\n\n"
                            f"🌐 Cầu: {cau_str}\n"
                            f"📊 Thành tích: {stats['thang']} Thắng · {stats['thua']} Thua ({rate_win}%)\n"
                            f"🎮 Smart Engine (Markov + Z-Score)"
                        )

                        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                        last_predict = du_doan
                        last_phien = phien
        except Exception as e:
            print(f"Lỗi Auto Loop MD5: {e}", flush=True)

        time.sleep(7)

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    bot.reply_to(message, "Bot MD5 Smart Engine đã sẵn sàng và đang chạy tự động 24/7!")

if __name__ == '__main__':
    # Tự động lấy port từ môi trường (Render), mặc định 10000
    port = int(os.environ.get('PORT', 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    threading.Thread(target=auto_process, daemon=True).start()
    print("Khởi động thành công bot MD5 với thuật toán Markov + Z-Score...", flush=True)
    bot.infinity_polling(skip_pending=True)
            
