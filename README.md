Ứng dụng Ký Số & Truyền File giữa Người Ký và Người Nhận
Đây là một hệ thống gồm 2 ứng dụng Flask:
Người Ký: Cho phép chọn file, tạo chữ ký số (sử dụng RSA), gửi file, chữ ký và khóa công khai đến người nhận.
Người Nhận: Nhận file, chữ ký, public key qua socket và xác minh tính hợp lệ của chữ ký.

Chức năng chính
Người Ký :
Tải file lên
Tự động sinh khóa riêng, khóa công khai RSA
Tạo chữ ký số cho nội dung file
Gửi file, chữ ký, và public key qua socket TCP
![image](https://github.com/user-attachments/assets/3db21e6b-3a91-465b-b67e-ceea6afa4f65)

Người Nhận :
Nhận file, chữ ký và khóa công khai từ socket
Lưu file và chữ ký
Giao diện xác minh chữ ký thủ công (nếu cần)
Tự động xác minh chữ ký
Cơ chế truyền file
Sử dụng socket TCP trên cổng 65432
![image](https://github.com/user-attachments/assets/d46db81b-3d93-4a28-8196-01af5cc4f5bd)

Truyền dữ liệu lần lượt:
Tên file
Chữ ký số
Public Key
Nội dung file
