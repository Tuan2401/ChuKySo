from flask import Flask, render_template_string, request, redirect, flash
import os, socket
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

app = Flask(__name__)
app.secret_key = "secret"
SAVE_FOLDER = "downloads_nhan"
os.makedirs(SAVE_FOLDER, exist_ok=True)

HTML = '''
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Người Nhận</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head><body class="bg-light"><div class="container py-5">
<div class="card shadow-sm">
<div class="card-header bg-primary text-white"><h4>📥 Người Nhận - Nhận file và xác minh</h4></div>
<div class="card-body">
<p><strong>IP của bạn:</strong> {{ ip }}</p>
<a href="/receive" class="btn btn-outline-success mb-4">📡 Nhận file từ người ký</a>
<hr><h5>🔍 Xác minh chữ ký</h5>
<form method="POST" action="/verify" enctype="multipart/form-data">
<div class="mb-3"><label>Chọn file gốc:</label>
<input class="form-control" type="file" name="file" required></div>
<div class="mb-3"><label>Chọn file chữ ký (.sig):</label>
<input class="form-control" type="file" name="sig" required></div>
<div class="mb-3"><label>Chọn khóa công khai (.pem):</label>
<input class="form-control" type="file" name="pub" required></div>
<button class="btn btn-primary" type="submit">Xác minh</button></form>
<hr>{% with messages = get_flashed_messages() %}
  {% if messages %}
    <div class="alert alert-info mt-3">
      {% for msg in messages %}
        <div>{{ msg }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
</div></div></div></body></html>
'''

@app.route('/')
def index():
    ip = socket.gethostbyname(socket.gethostname())
    return render_template_string(HTML, ip=ip)

@app.route('/receive')
def receive():
    try:
        HOST = socket.gethostbyname(socket.gethostname())
        PORT = 65432
        BUFFER_SIZE = 4096

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen(1)
            conn, addr = server.accept()
            with conn:
                filename_len = int.from_bytes(conn.recv(4), 'big')
                filename = conn.recv(filename_len).decode()

                sig_len = int.from_bytes(conn.recv(4), 'big')
                signature = conn.recv(sig_len)

                pub_len = int.from_bytes(conn.recv(4), 'big')
                pub_key = conn.recv(pub_len)

                file_len = int.from_bytes(conn.recv(8), 'big')
                data = b''
                while len(data) < file_len:
                    data += conn.recv(BUFFER_SIZE)

                file_path = os.path.join(SAVE_FOLDER, filename)
                sig_path = file_path + ".sig"
                pub_path = file_path + ".pem"

                with open(file_path, 'wb') as f:
                    f.write(data)
                with open(sig_path, 'wb') as f:
                    f.write(signature)
                with open(pub_path, 'wb') as f:
                    f.write(pub_key)

                flash(f"✅ Đã nhận file: {file_path}")
    except Exception as e:
        flash(f"❌ Lỗi khi nhận file: {e}")
    return redirect('/')

@app.route('/receive')
def receive_file():
    try:
        HOST = socket.gethostbyname(socket.gethostname())
        PORT = 65432
        BUFFER_SIZE = 4096

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((HOST, PORT))
            server.listen(1)
            flash(f"⏳ Đang chờ kết nối từ người gửi tại {HOST}:{PORT}...")

            conn, addr = server.accept()
            with conn:
                flash(f"🔗 Đã kết nối từ {addr}")

                # Nhận tên file
                filename_len = int.from_bytes(conn.recv(4), 'big')
                filename = conn.recv(filename_len).decode()

                # Nhận chữ ký
                sig_len = int.from_bytes(conn.recv(4), 'big')
                signature = conn.recv(sig_len)

                # Nhận public key
                pub_len = int.from_bytes(conn.recv(4), 'big')
                public_key = conn.recv(pub_len)

                # Nhận nội dung file
                file_len = int.from_bytes(conn.recv(8), 'big')
                data = b''
                while len(data) < file_len:
                    part = conn.recv(BUFFER_SIZE)
                    if not part:
                        break
                    data += part

                # Lưu các file
                file_path = os.path.join(SAVE_FOLDER, filename)
                sig_path = file_path + ".sig"
                pub_path = file_path + ".pem"

                with open(file_path, 'wb') as f:
                    f.write(data)
                with open(sig_path, 'wb') as f:
                    f.write(signature)
                with open(pub_path, 'wb') as f:
                    f.write(public_key)

                flash(f"✅ Đã nhận file: {filename}")
                flash(f"📌 Đã lưu chữ ký (.sig) và khóa công khai (.pem)")
    except Exception as e:
        flash(f"❌ Lỗi khi nhận file: {e}")
    return redirect('/')


if __name__ == '__main__':
    app.run(port=5001, host='0.0.0.0')
