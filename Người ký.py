from flask import Flask, render_template_string, request, redirect, flash
import socket, os
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

app = Flask(__name__)
app.secret_key = "secret"
UPLOAD_FOLDER = 'uploads_ky'
KEY_FOLDER = 'rsa_keys'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(KEY_FOLDER, exist_ok=True)

PRIVATE_KEY_FILE = os.path.join(KEY_FOLDER, 'private_key.pem')
PUBLIC_KEY_FILE = os.path.join(KEY_FOLDER, 'public_key.pem')

# HTML template
HTML = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Người Ký</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
    <div class="card shadow-sm">
        <div class="card-header bg-success text-white"><h4>📁 Người Ký - Ký và gửi file</h4></div>
        <div class="card-body">
            <p><strong>💻 IP của bạn:</strong> {{ ip }}</p>
            <form method="POST" enctype="multipart/form-data">
                <div class="mb-3">
                    <label>Chọn file:</label>
                    <input class="form-control" type="file" name="file" required>
                </div>
                <div class="mb-3">
                    <label>IP người nhận:</label>
                    <input class="form-control" type="text" name="receiver_ip" required>
                </div>
                <button class="btn btn-success" type="submit">📤 Ký và Gửi</button>
            </form>
            <hr>
            {% with messages = get_flashed_messages() %}
              {% if messages %}
                <div class="alert alert-info mt-3">
                  {% for msg in messages %}
                    <div>{{ msg }}</div>
                  {% endfor %}
                </div>
              {% endif %}
            {% endwith %}
        </div>
    </div>
</div>
</body>
</html>
'''

def generate_and_save_keys():
    if not os.path.exists(PRIVATE_KEY_FILE):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with open(PRIVATE_KEY_FILE, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(PUBLIC_KEY_FILE, 'wb') as f:
            f.write(private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

def load_private_key():
    with open(PRIVATE_KEY_FILE, 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)

@app.route('/', methods=['GET', 'POST'])
def sign_and_send():
    ip = socket.gethostbyname(socket.gethostname())
    if request.method == 'POST':
        file = request.files['file']
        receiver_ip = request.form['receiver_ip']
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Sinh khóa RSA
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Tạo chữ ký
        data = open(file_path, 'rb').read()
        signature = private_key.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

        # Ghi khóa công khai ra file .pem
        pubkey_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        pubkey_path = file_path + ".pem"
        with open(pubkey_path, "wb") as f:
            f.write(pubkey_pem)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((receiver_ip, 65432))

                # Gửi tên file
                s.send(len(filename).to_bytes(4, 'big'))
                s.send(filename.encode())

                # Gửi chữ ký
                s.send(len(signature).to_bytes(4, 'big'))
                s.send(signature)

                # Gửi public key
                s.send(len(pubkey_pem).to_bytes(4, 'big'))
                s.send(pubkey_pem)

                # Gửi nội dung file
                s.send(len(data).to_bytes(8, 'big'))
                s.sendall(data)

            flash("✅ Đã ký và gửi thành công!")
        except Exception as e:
            flash(f"❌ Gửi thất bại: {e}")
        return redirect('/')
    return render_template_string(HTML, ip=ip)


if __name__ == '__main__':
    generate_and_save_keys()
    app.run(host='0.0.0.0', port=5000, debug=True)
