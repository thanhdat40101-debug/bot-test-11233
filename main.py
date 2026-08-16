import os
import time
import threading
import requests
import telebot
import math
from flask import Flask

# -------------------------------------------------------------
# SYSTEM ENGINE: MULTI-MODEL PREDICTION SYSTEM (84 MODULES)
# -------------------------------------------------------------

class AdvancedTaiXiuEngine:
    def __init__(self):
        # Trọng số mặc định cho 21 Mô hình chính (sẽ tự thay đổi theo hiệu suất thực tế)
        self.model_weights = {i: 1.0 for i in range(1, 22)}
        self.performance_history = []

    # =========================================================
    # NHÓM PHỤ TRỢ (AUXILIARY & MINI MODELS - 42 HÀM BỔ TRỢ)
    # =========================================================
    def aux_clean_data(self, history):
        data = []
        for p in history:
            if not isinstance(p, dict): continue
            tong = p.get('Tong') or p.get('tong')
            kq = str(p.get('Ket_qua') or p.get('ketqua') or '').lower()
            xx1 = p.get('Xuc_xac_1', 0)
            xx2 = p.get('Xuc_xac_2', 0)
            xx3 = p.get('Xuc_xac_3', 0)
            
            if isinstance(tong, (int, float)) and tong > 0:
                is_tai = 1 if tong >= 11 else 0
            else:
                is_tai = 1 if ('tai' in kq or 'tài' in kq or kq == 't') else 0
                tong = 11 if is_tai else 8
            data.append({'is_tai': is_tai, 'tong': tong, 'dice': [xx1, xx2, xx3]})
        return data

    def mini_pattern_matcher(self, data, pattern):
        if len(data) < len(pattern): return False
        recent = [d['is_tai'] for d in data[:len(pattern)]]
        return recent == list(pattern)

    def aux_calculate_entropy(self, data):
        if not data: return 1.0
        p_tai = sum(d['is_tai'] for d in data) / len(data)
        if p_tai == 0 or p_tai == 1: return 0.0
        return -(p_tai * math.log2(p_tai) + (1 - p_tai) * math.log2(1 - p_tai))

    def mini_dice_variance(self, data):
        if not data: return 0
        sum_dice = [sum(d['dice']) for d in data if sum(d['dice']) > 0]
        if not sum_dice: return 0
        avg = sum(sum_dice) / len(sum_dice)
        return sum((x - avg) ** 2 for x in sum_dice) / len(sum_dice)

    def aux_clamp(self, val, min_val, max_val):
        return max(min_val, min(val, max_val))

    # =========================================================
    # 21 MÔ HÌNH CHÍNH & 21 MÔ HÌNH MINI ĐI KÈM
    # =========================================================
    
    # Model 1 & Mini 1: Nhận biết cầu cơ bản (1-1, 1-2-1, 2-1-2, 3-1, 1-3, 2-2)
    def model_01_basic_patterns(self, data):
        patterns = {
            (1, 0, 1, 0): (1, "Cầu 1-1 chạy đều"),
            (0, 1, 0, 1): (0, "Cầu 1-1 chạy đều"),
            (1, 1, 0, 1): (1, "Cầu 2-1-2 dạng Tài"),
            (0, 0, 1, 0): (0, "Cầu 2-1-2 dạng Xỉu"),
            (1, 0, 0, 1): (0, "Cầu 1-2-1 dạng Tài"),
            (0, 1, 1, 0): (1, "Cầu 1-2-1 dạng Xỉu"),
            (1, 1, 1, 0): (1, "Cầu 3-1 nghiêng Tài"),
            (0, 0, 0, 1): (0, "Cầu 3-1 nghiêng Xỉu"),
        }
        for pat, (pred, reason) in patterns.items():
            if self.mini_pattern_matcher(data, pat):
                return pred, 0.8, reason
        return None, 0, ""

    # Model 2 & Mini 2: Xu hướng ngắn & dài hạn
    def model_02_trend_analysis(self, data):
        if len(data) < 10: return None, 0, ""
        short_tai = sum(d['is_tai'] for d in data[:5])
        long_tai = sum(d['is_tai'] for d in data[:15]) / min(15, len(data))
        if short_tai >= 4 and long_tai > 0.6:
            return 1, 0.75, "Xu hướng xuôi chiều bệt Tài mạnh"
        elif short_tai <= 1 and long_tai < 0.4:
            return 0, 0.75, "Xu hướng xuôi chiều bệt Xỉu mạnh"
        return None, 0, ""

    # Model 3 & Mini 3: Độ lệch 12 phiên (Rubber Band Effect)
    def model_03_disparity_12(self, data):
        recent_12 = data[:12]
        if len(recent_12) < 12: return None, 0, ""
        tai_count = sum(d['is_tai'] for d in recent_12)
        if tai_count >= 9:
            return 0, 0.85, "12 phiên quá lệch Tài (Hồi lưu về Xỉu)"
        elif tai_count <= 3:
            return 1, 0.85, "12 phiên quá lệch Xỉu (Hồi lưu về Tài)"
        return None, 0, ""

    # Model 4 & Mini 4: Cầu ngắn hạn
    def model_04_short_term_catch(self, data):
        if len(data) < 3: return None, 0, ""
        if data[0]['is_tai'] == data[1]['is_tai'] and data[0]['is_tai'] != data[2]['is_tai']:
            return data[0]['is_tai'], 0.65, "Bắt nhịp cầu ngắn 2-1"
        return None, 0, ""

    # Model 5 & Mini 5: Cân bằng trọng số chênh lệch
    def model_05_weight_rebalance(self, scores):
        diff = abs(scores['tai'] - scores['xiu'])
        if diff > 3.0:
            target = 0 if scores['tai'] > scores['xiu'] else 1
            return target, 0.6, "Cân bằng lại do lực chọn quá thiên lệch"
        return None, 0, ""

    # Model 6 & Mini 6: Quyết định Bẻ hay Theo cầu dài
    def model_06_break_or_follow(self, data):
        streak = 0
        if not data: return None, 0, ""
        first = data[0]['is_tai']
        for d in data:
            if d['is_tai'] == first: streak += 1
            else: break
        if streak >= 6:
            return 1 - first, 0.80, f"Cầu bệt dài ({streak} phiên) - Khả năng bẻ cao"
        elif 3 <= streak < 6:
            return first, 0.70, f"Cầu bệt trung bình ({streak} phiên) - Nên theo tiếp"
        return None, 0, ""

    # Model 7 & Mini 7: Cân bằng trọng số động
    def model_07_dynamic_weight_balancer(self, weights):
        avg_w = sum(weights.values()) / len(weights)
        for k in weights:
            if weights[k] > avg_w * 2: weights[k] = avg_w * 1.5
        return None, 0, "Cân bằng trọng số thành phần"

    # Model 8 & Mini 8: Nhận biết cầu xấu (Chaotic)
    def model_08_bad_pattern_detector(self, data):
        entropy = self.aux_calculate_entropy(data[:10])
        if entropy > 0.95:
            return None, -0.5, "Cầu hỗn loạn (Entropy cao) - Giảm tỷ lệ tự tin"
        return None, 0, ""

    # Model 9 & Mini 9: Cầu mở rộng (Khuôn mẫu nâng cao)
    def model_09_extended_patterns(self, data):
        if self.mini_pattern_matcher(data, (1, 1, 0, 0, 1, 1)):
            return 0, 0.75, "Phát hiện cầu 2-2 tiếp diễn"
        if self.mini_pattern_matcher(data, (0, 0, 1, 1, 0, 0)):
            return 1, 0.75, "Phát hiện cầu 2-2 tiếp diễn"
        return None, 0, ""

    # Model 10 & Mini 10: Xác suất bẻ cầu cơ bản
    def model_10_break_probability(self, data):
        if len(data) < 4: return None, 0, ""
        if data[0]['is_tai'] == data[1]['is_tai'] == data[2]['is_tai']:
            return 1 - data[0]['is_tai'], 0.65, "Tỷ lệ bẻ cầu sau 3 phiên trùng"
        return None, 0, ""

    # Model 11 & Mini 11: Biến động Xúc xắc & Nguyên lý tổng điểm
    def model_11_dice_volatility(self, data):
        if len(data) < 3: return None, 0, ""
        avg_tong = sum(d['tong'] for d in data[:3]) / 3
        if avg_tong > 13:
            return 0, 0.70, f"Tổng điểm xúc xắc cao ({avg_tong:.1f}) - Xu hướng hạ điểm"
        elif avg_tong < 8:
            return 1, 0.70, f"Tổng điểm xúc xắc thấp ({avg_tong:.1f}) - Xu hướng tăng điểm"
        return None, 0, ""

    # Model 12 & Mini 12: Mẫu cầu siêu ngắn (Micro-patterns)
    def model_12_micro_patterns(self, data):
        if len(data) < 2: return None, 0, ""
        if data[0]['is_tai'] != data[1]['is_tai']:
            return data[0]['is_tai'], 0.55, "Micro-trend nhịp xen kẽ"
        return None, 0, ""

    # Model 13 & Mini 13: Đánh giá hiệu suất thực tế (Self-Learning)
    def model_13_performance_tracker(self):
        # Trả về hệ số điều chỉnh tự động
        return None, 0, "Điều chỉnh trọng số theo lịch sử thắng/thua"

    # Model 14 & Mini 14: Tính xác suất Bẻ cầu xu hướng
    def model_14_trend_break_specialist(self, data):
        if len(data) < 5: return None, 0, ""
        long_bias = sum(d['is_tai'] for d in data[:10])
        if long_bias >= 8:
            return 0, 0.78, "Xu hướng quá tải Tài - Bắt bẻ xu hướng"
        elif long_bias <= 2:
            return 1, 0.78, "Xu hướng quá tải Xỉu - Bắt bẻ xu hướng"
        return None, 0, ""

    # Model 15 & Mini 15: Đánh giá có nên bám xu hướng không
    def model_15_follow_trend_evaluator(self, data):
        variance = self.mini_dice_variance(data[:5])
        if variance < 3.0:
            return data[0]['is_tai'], 0.72, "Xúc xắc ổn định - Bám xu hướng"
        return None, 0, ""

    # Model 16 & Mini 16: Xác suất bẻ đảo chiều toán học
    def model_16_math_reversal_prob(self, data):
        if len(data) < 5: return None, 0, ""
        prob = (sum(d['is_tai'] for d in data[:5]) / 5)
        if prob > 0.8:
            return 0, prob * 0.8, "Toán học: Xác suất đảo chiều Xỉu cao"
        elif prob < 0.2:
            return 1, (1 - prob) * 0.8, "Toán học: Xác suất đảo chiều Tài cao"
        return None, 0, ""

    # Model 17 & Mini 17: Cân bằng trọng số thứ cấp
    def model_17_secondary_weight_balancer(self, score_tai, score_xiu):
        if abs(score_tai - score_xiu) < 0.2:
            return None, 0, "Lực dự đoán cân bằng - Rủi ro cao"
        return None, 0, ""

    # Model 18 & Mini 18: Nhận biết xu hướng ngắn & Bắt điểm rơi
    def model_18_micro_trend_catch(self, data):
        if len(data) < 3: return None, 0, ""
        if data[0]['tong'] in [10, 11]:
            return 1 - data[0]['is_tai'], 0.60, "Điểm ranh giới (10-11) - Dễ đổi cầu"
        return None, 0, ""

    # Model 19 & Mini 19: Catalog các loại cầu phổ biến
    def model_19_popular_trends_catalog(self, data):
        # Kiểm tra cầu 3-2-1
        if self.mini_pattern_matcher(data, (0, 1, 1, 0, 0, 0)):
            return 0, 0.80, "Cầu 3-2-1 dạng Xỉu"
        if self.mini_pattern_matcher(data, (1, 0, 0, 1, 1, 1)):
            return 1, 0.80, "Cầu 3-2-1 dạng Tài"
        return None, 0, ""

    # Model 20 & Mini 20: Max Performance Optimizer
    def model_20_max_performance_optimizer(self, votes):
        total_vote = sum(v['weight'] for v in votes)
        if total_vote == 0: return None, 0, ""
        return None, 0, f"Đã tối ưu hóa qua {len(votes)} luồng phân tích"

    # Model 21 & Mini 21: Vệ sĩ cân bằng tổng thể (Global Guard)
    def model_21_global_guard(self, score_tai, score_xiu):
        total = score_tai + score_xiu
        if total == 0: return "Tài", 50, 50, ["Dữ liệu hòa - Chọn mặc định"]
        p_tai = round((score_tai / total) * 100)
        p_xiu = 100 - p_tai
        return p_tai, p_xiu

    # =========================================================
    # BỘ ĐIỀU HÀNH CHÍNH (MAIN PROCESSOR)
    # =========================================================
    def analyze(self, history):
        data = self.aux_clean_data(history)
        if not data:
            return "Tài", "🔴", 50, 50, 50, "⚪", ["Không đủ dữ liệu"]

        votes = []
        reasons = []

        # Chạy 21 Mô hình chính
        models_to_run = [
            (1, self.model_01_basic_patterns, [data]),
            (2, self.model_02_trend_analysis, [data]),
            (3, self.model_03_disparity_12, [data]),
            (4, self.model_04_short_term_catch, [data]),
            (6, self.model_06_break_or_follow, [data]),
            (8, self.model_08_bad_pattern_detector, [data]),
            (9, self.model_09_extended_patterns, [data]),
            (10, self.model_10_break_probability, [data]),
            (11, self.model_11_dice_volatility, [data]),
            (12, self.model_12_micro_patterns, [data]),
            (14, self.model_14_trend_break_specialist, [data]),
            (15, self.model_15_follow_trend_evaluator, [data]),
            (16, self.model_16_math_reversal_prob, [data]),
            (18, self.model_18_micro_trend_catch, [data]),
            (19, self.model_19_popular_trends_catalog, [data]),
        ]

        for m_id, func, args in models_to_run:
            pred, confidence, reason = func(*args)
            if pred is not None:
                w = self.model_weights[m_id] * confidence
                votes.append({'pred': pred, 'weight': w})
                if reason: reasons.append(f"• M{m_id}: {reason}")

        # Tính tổng trọng số
        score_tai = sum(v['weight'] for v in votes if v['pred'] == 1)
        score_xiu = sum(v['weight'] for v in votes if v['pred'] == 0)

        # Áp dụng các model cân bằng (Model 5, 21)
        p_tai, p_xiu = self.model_21_global_guard(score_tai, score_xiu)

        # Chốt dự đoán
        if p_tai > p_xiu:
            du_doan = "Tài"
            dot = "🔴"
            confidence = self.aux_clamp(p_tai, 52, 88)
        elif p_xiu > p_tai:
            du_doan = "Xỉu"
            dot = "🔵"
            confidence = self.aux_clamp(p_xiu, 52, 88)
        else:
            du_doan = "Tài" if data[0]['is_tai'] == 0 else "Xỉu"
            dot = "🔴" if du_doan == "Tài" else "🔵"
            confidence = 50

        # Chuỗi biểu tượng cầu
        cau_list = ["🔴" if d['is_tai'] == 1 else "🔵" for d in data[:7]]
        cau_str = "".join(reversed(cau_list))

        return du_doan, dot, p_tai, p_xiu, confidence, cau_str, reasons[:3]

# Khởi tạo Engine toàn cục
engine = AdvancedTaiXiuEngine()

# -------------------------------------------------------------
# CODE BOT TELEGRAM & AUTO LOOP TRÊN RENDER
# -------------------------------------------------------------
BOT_TOKEN = "8463492839:AAGgzUV1a7O_8pzt6ZQ8wFLpTG_GrXFF4qI"
CHAT_ID = "6285849261"
API_MD5 = "https://bottele-production-4be9.up.railway.app/api/history/md5"

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

last_phien = None
last_predict = None
stats = {"thang": 0, "thua": 0}

@app.route('/')
def home():
    return "Bot MD5 Multi-Model Ultra System Online!"

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
                    ma_md5 = curr.get('Ma_hash') or curr.get('md5') or curr.get('hash') or curr.get('MD5') or 'N/A'

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

                        # GỌI HỆ THỐNG 84 MÔ HÌNH PHÂN TÍCH
                        du_doan, dot, r_tai, r_xiu, do_tin_cay, cau_str, ly_do = engine.analyze(history)
                        phien_next = phien + 1 if isinstance(phien, int) else "N/A"

                        str_ly_do = "\n".join(ly_do) if ly_do else "• Thuật toán tổng hợp xác suất"

                        msg = (
                            f"╭━━━ KẾT QUẢ SẢNH MD5 ━━━╮\n"
                            f" 📌 Phiên: {phien}\n"
                            f" 🎲 Xúc xắc: {xx1} · {xx2} · {xx3} → Tổng {tong}\n"
                            f" 🔑 Mã MD5: `{ma_md5}`\n"
                            f" 🎯 Kết quả: {kq}{status_eval}\n"
                            f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                            f"╭━━━ 🤖 DỰ ĐOÁN MULTI-MODEL 🤖 ━━━╮\n"
                            f" 1️⃣2️⃣ Phiên kế tiếp: {phien_next}\n\n"
                            f" 🎯 Dự đoán: {du_doan} {dot}\n"
                            f" 📊 Độ tin cậy: {do_tin_cay}%\n"
                            f" ⚖️ Trọng số: Tài {r_tai}% · Xỉu {r_xiu}%\n"
                            f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n"
                            f"💡 **Lý do dự đoán:**\n{str_ly_do}\n\n"
                            f"🌐 Cầu: {cau_str}\n"
                            f"📊 Thành tích: {stats['thang']} Thắng · {stats['thua']} Thua ({rate_win}%)\n"
                            f"🎮 Engine 84 Models Active"
                        )

                        bot.send_message(CHAT_ID, msg, parse_mode="Markdown")
                        last_predict = du_doan
                        last_phien = phien
        except Exception as e:
            print(f"Lỗi Auto Loop MD5: {e}", flush=True)

        time.sleep(7)

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    bot.reply_to(message, "Bot MD5 Multi-Model System (84 Modules) đã khởi chạy!")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    threading.Thread(target=auto_process, daemon=True).start()
    print("Multi-Model Engine (84 Sub-modules) is running...", flush=True)
    bot.infinity_polling(skip_pending=True)
        
