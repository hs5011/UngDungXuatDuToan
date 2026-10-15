# Hướng dẫn chạy local và triển khai lên server

Ứng dụng là web app **Python + Streamlit** (`app.py`, thư viện trong `dutoan/`). Không cần cơ sở dữ liệu:
dự án lưu thành file JSON trong `workspace/projects/`. Ứng dụng **không cần** 2 file template Excel khi chạy
(chỉ dùng để đối chiếu), nên lên server chỉ cần mã nguồn.

---

## 1. Chạy ở máy local (Windows)

### 1.1 Yêu cầu
- Python 3.10 trở lên (đã thử với 3.13). Tải tại https://www.python.org/downloads/ – khi cài tích **Add python.exe to PATH**.
- Kiểm tra: `python --version`

### 1.2 Cài đặt (làm 1 lần)
Mở PowerShell tại thư mục dự án:

```powershell
cd "E:\OneDrive - CONG TY CP CONG NGHE VIETINFO\Documents\UngdungXuatDuToan"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(Nếu PowerShell báo không cho chạy script: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.)

### 1.3 Chạy
Cách 1 – bấm đúp `chay_ung_dung.bat`.

Cách 2 – dòng lệnh:

```powershell
python -X utf8 -m streamlit run app.py
```

Trình duyệt tự mở `http://localhost:8501`. Dừng bằng `Ctrl + C`.

### 1.4 Chạy thử kiểm tra tính toán

```powershell
python -m pytest
```

### 1.5 Dữ liệu
- Dự án tự lưu tại `workspace/projects/<mã>.json` (không đưa lên git).
- Sao lưu / chuyển máy: bước **9. Xuất Excel & lưu** tải file `.json`, máy kia dùng **➕ Tạo dự án mới → nhập từ file .json**.

---

## 2. Đưa lên server

Có 3 cách, chọn theo nhu cầu. **Khuyến nghị cách A** (server Linux nội bộ/VPS, Ubuntu 22.04 trở lên).

> **Lưu ý bảo mật:** Streamlit **không có đăng nhập**. Ai vào được URL là xem/sửa/xoá được mọi dự án.
> Khi đưa ra Internet bắt buộc đặt sau Nginx có mật khẩu (xem 2.A.5) hoặc chỉ mở trong mạng nội bộ/VPN.
> Repo GitHub đang **công khai**: không đẩy dữ liệu dự án hay template Excel lên đó.

### A. Server Linux + systemd + Nginx

#### A.1 Chuẩn bị server
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx
```

#### A.2 Lấy mã nguồn
```bash
sudo mkdir -p /opt/dutoan && sudo chown $USER /opt/dutoan
git clone https://github.com/hs5011/UngDungXuatDuToan.git /opt/dutoan
cd /opt/dutoan
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Kiểm tra nhanh: `.venv/bin/python -m streamlit run app.py --server.port 8501` rồi mở `http://IP-server:8501`.

#### A.3 Chạy thành dịch vụ (tự khởi động lại)
Tạo `/etc/systemd/system/dutoan.service`:

```ini
[Unit]
Description=Ung dung xuat du toan TT39
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/dutoan
Environment=PYTHONUTF8=1
ExecStart=/opt/dutoan/.venv/bin/python -m streamlit run app.py \
  --server.port 8501 --server.address 127.0.0.1 --server.headless true \
  --browser.gatherUsageStats false
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R www-data /opt/dutoan/workspace 2>/dev/null || (sudo mkdir -p /opt/dutoan/workspace && sudo chown -R www-data /opt/dutoan/workspace)
sudo systemctl daemon-reload
sudo systemctl enable --now dutoan
sudo systemctl status dutoan
```

`www-data` cần quyền ghi vào `/opt/dutoan/workspace` (nơi lưu dự án).

#### A.4 Nginx (reverse proxy – bắt buộc cho WebSocket của Streamlit)
Tạo `/etc/nginx/sites-available/dutoan` (đổi `dutoan.example.vn` thành tên miền của bạn):

```nginx
server {
    listen 80;
    server_name dutoan.example.vn;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/dutoan /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

HTTPS miễn phí: `sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx -d dutoan.example.vn`

#### A.5 Đặt mật khẩu (Basic Auth)
```bash
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd tennguoidung
```
Thêm vào khối `location /` của Nginx:
```nginx
        auth_basic "Dutoan";
        auth_basic_user_file /etc/nginx/.htpasswd;
```
rồi `sudo systemctl reload nginx`.

#### A.6 Cập nhật phiên bản mới
```bash
cd /opt/dutoan
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart dutoan
```
Dữ liệu trong `workspace/` không bị ảnh hưởng (đã nằm ngoài git).

#### A.7 Sao lưu
```bash
tar czf dutoan-backup-$(date +%F).tgz /opt/dutoan/workspace
```
Nên đặt cron chạy hằng ngày.

---

### B. Docker

Tạo file `Dockerfile` ở thư mục gốc:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUTF8=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--browser.gatherUsageStats=false"]
```

Build và chạy (gắn volume để không mất dự án khi cập nhật container):

```bash
docker build -t dutoan .
docker run -d --name dutoan --restart always -p 8501:8501 -v dutoan_data:/app/workspace dutoan
```

Cập nhật: `git pull && docker build -t dutoan . && docker rm -f dutoan` rồi chạy lại lệnh `docker run`.
Vẫn đặt Nginx phía trước như A.4/A.5.

---

### C. Server Windows (máy chủ nội bộ)

1. Cài Python, làm theo mục 1.1–1.2 trên server (copy thư mục dự án hoặc `git clone`).
2. Chạy bằng `chay_ung_dung.bat`; để mọi máy trong mạng truy cập, thêm `--server.address 0.0.0.0`:
   ```powershell
   python -X utf8 -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
   ```
3. Mở cổng tường lửa:
   ```powershell
   New-NetFirewallRule -DisplayName "Dutoan 8501" -Direction Inbound -Protocol TCP -LocalPort 8501 -Action Allow
   ```
4. Chạy nền tự khởi động: dùng **NSSM** (`nssm install Dutoan` → trỏ tới `python.exe`, tham số như trên, thư mục = thư mục dự án) hoặc Task Scheduler (trigger *At startup*).
5. Người dùng truy cập `http://IP-server:8501`.

---

## 3. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `streamlit` không nhận lệnh | Dùng `python -m streamlit ...` hoặc kích hoạt `.venv` |
| Lỗi font/tiếng Việt trên Windows | Thêm `-X utf8` (đã có trong `.bat`) |
| Trang trắng / "Please wait" mãi sau Nginx | Thiếu cấu hình WebSocket (`Upgrade`/`Connection`) trong A.4 |
| Cổng 8501 bị chiếm | Đổi `--server.port 8502` (và sửa Nginx/Docker tương ứng) |
| Không lưu được dự án trên server | Cấp quyền ghi cho user chạy dịch vụ vào thư mục `workspace/` |
| Mất dự án sau khi cập nhật Docker | Chưa gắn volume `-v dutoan_data:/app/workspace` |
| Xem log | Linux: `journalctl -u dutoan -f` · Docker: `docker logs -f dutoan` |

## 4. Lưu ý vận hành
- Nhiều người dùng chung một thư mục `workspace/` → cùng thấy mọi dự án; nếu cần tách người dùng hãy chạy mỗi nhóm một bản riêng (cổng/thư mục khác nhau).
- Hai người cùng sửa một dự án cùng lúc: bản lưu sau ghi đè bản trước.
- Mỗi lần nâng cấp mã (`git pull`) nên chạy `python -m pytest` trước khi khởi động lại dịch vụ.
