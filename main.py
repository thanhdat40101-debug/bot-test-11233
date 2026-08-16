import os
import threading
import requests
import telebot
from flask import Flask

# -------------------------------------------------------------
# 1. CẤU HÌNH TỰ ĐỘNG CỔNG WEB CHO RENDER
# -------------------------------------------------------------
app = Flask(__name__)


@app.route('/')
def home():
  # Trang web giả lập trả về dòng chữ này để Render xác nhận service sống
  return 'Bot Telegram Taixiu đang hoạt động 24/7!'


def run_web_server():
  # Render tự cấp một cổng PORT ngẫu nhiên qua biến môi trường
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


# -------------------------------------------------------------
# 2. CẤU HÌNH BOT TELEGRAM & THUẬT TOÁN DỰ ĐOÁN
# -------------------------------------------------------------
BOT_TOKEN = '8527232891:AAGrm_KA-2EwX6nj39DYSIXm_guMXxKSebg'
bot = telebot.TeleBot(BOT_TOKEN)

API_LICH_SU = (
    'https://bottele-production-4be9.up.railway.app/api/history/taixiu'
)


def thuat_toan_danh_gia(data):
  if not data or not isinstance(data, list):
    return 'Dữ liệu trả về từ API chưa đúng cấu trúc hoặc trống.'

  # Lấy 10 phiên gần nhất
  recent = data[:10]

  danh_sach_kq = []
  for phien in recent:
    kq = phien.get('ketqua', phien.get('result', ''))
    if kq:
      danh_sach_kq.append(str(kq).lower())

  tai_count = sum(1 for kq in danh_sach_kq if 'tai' in kq or 'tài' in kq)
  xiu_count = sum(1 for kq in danh_sach_kq if 'xiu' in kq or 'xỉu' in kq)

  total = len(danh_sach_kq)
  if total == 0:
    return 'Đã kết nối API nhưng chưa đọc được cấu trúc kết quả.'

  rate_tai = round((tai_count / total) * 100)
  rate_xiu = round((xiu_count / total) * 100)

  # Thuật toán đưa ra nhận định
  if tai_count >= 7:
    du_doan = 'Xỉu (Cầu lệch nghiêng về Tài, xu hướng bẻ Xỉu)'
  elif xiu_count >= 7:
    du_doan = 'Tài (Cầu lệch nghiêng về Xỉu, xu hướng bẻ Tài)'
  else:
    du_doan = 'Tài' if rate_tai <= rate_xiu else 'Xỉu'

  ket_qua_text = (
      f'📊 **KẾT QUẢ PHÂN TÍCH 10 PHIÊN GẦN NHẤT**\n'
      f'• Tỷ lệ Tài: {rate_tai}%\n'
      f'• Tỷ lệ Xỉu: {rate_xiu}%\n'
      f'-------------------------------------\n'
      f'🔮 **Dự đoán phiên tiếp theo:** **{du_doan}**'
  )
  return ket_qua_text


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  bot.reply_to(
      message,
      'Chào mừng bạn! Nhập lệnh /dudoan để nhận phân tích thuật toán từ API.',
  )


@bot.message_handler(commands=['dudoan'])
def handle_dudoan(message):
  bot.reply_to(message, '🔄 Đang gọi API và phân tích dữ liệu...')
  try:
    res = requests.get(API_LICH_SU, timeout=5)
    if res.status_code == 200:
      data = res.json()
      data_list = data if isinstance(data, list) else data.get('data', [])

      thong_bao = thuat_toan_danh_gia(data_list)
      bot.send_message(message.chat.id, thong_bao, parse_mode='Markdown')
    else:
      bot.send_message(message.chat.id, '❌ Không thể kết nối tới máy chủ API.')
  except Exception as e:
    bot.send_message(message.chat.id, f'❌ Lỗi hệ thống: {e}')


# -------------------------------------------------------------
# 3. KÍCH HOẠT CHẠY SONG SONG WEB SERVER & BOT
# -------------------------------------------------------------
if __name__ == '__main__':
  # Chạy Web server ở luồng phụ
  server_thread = threading.Thread(target=run_web_server)
  server_thread.daemon = True
  server_thread.start()

  # Chạy Bot Telegram ở luồng chính
  print('Bot đang hoạt động...')
  bot.infinity_polling()
