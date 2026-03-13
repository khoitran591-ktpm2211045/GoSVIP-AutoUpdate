import os
import sys
import time
import urllib.request
import traceback
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# CẤU HÌNH GITHUB
VERSION_URL = "https://raw.githubusercontent.com/khoitran591-ktpm2211045/GoSVIP-AutoUpdate/main/version.txt"
CURRENT_VERSION = "0.0.0"  # Sẽ được cập nhật tự động khi tải về bản mới
APP_EXECUTABLE_NAME = "AppChinh.exe"

class AutoUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GoSVIP Launcher")
        self.root.geometry("400x150")
        self.root.resizable(False, False)
        # Căn giữa màn hình
        self.root.eval('tk::PlaceWindow . center')
        
        # Ẩn nút minimize/maximize
        self.root.attributes('-toolwindow', True)

        self.label = tk.Label(root, text="Đang kiểm tra cập nhật...", font=("Arial", 12))
        self.label.pack(pady=20)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

        self.status_label = tk.Label(root, text="", font=("Arial", 9), fg="gray")
        self.status_label.pack(pady=0)

        # Bắt đầu luồng kiểm tra cập nhật
        threading.Thread(target=self.check_and_update, daemon=True).start()

    def update_status(self, text, progress_val=None):
        def _update():
            self.status_label.config(text=text)
            if progress_val is not None:
                self.progress["value"] = progress_val
        self.root.after(0, _update)

    def launch_main_app(self):
        self.update_status("Đang khởi động phần mềm chính...", 100)
        time.sleep(1)
        if os.path.exists(APP_EXECUTABLE_NAME):
            try:
                # Khởi động app chính và không đợi
                subprocess.Popen([APP_EXECUTABLE_NAME])
            except Exception as e:
                messagebox.showerror("Lỗi Khởi Động", f"Không thể bật ứng dụng chính:\n{e}")
        else:
            messagebox.showerror("Lỗi", f"Không tìm thấy file {APP_EXECUTABLE_NAME}!")
        
        # Tắt Launcher
        self.root.after(0, self.root.destroy)

    def check_and_update(self):
        try:
            # Lấy thông tin version từ phiên bản local (nếu có lưu)
            local_version = CURRENT_VERSION
            version_file_path = "local_version.txt"
            if os.path.exists(version_file_path):
                with open(version_file_path, "r", encoding="utf-8") as f:
                    local_version = f.read().strip()

            self.update_status("Đang kết nối đến máy chủ...", 10)
            
            # Tải version.txt từ GitHub
            req = urllib.request.Request(VERSION_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8').splitlines()

            remote_version = None
            download_url = None

            for line in content:
                if line.startswith("VERSION="):
                    remote_version = line.split("=")[1].strip()
                elif line.startswith("URL="):
                    download_url = line.split("=", 1)[1].strip()

            if not remote_version or not download_url:
                raise ValueError("Định dạng file version.txt trên server không hợp lệ.")

            print(f"Local: {local_version} | Remote: {remote_version}")

            if remote_version != local_version:
                self.label.config(text="Đã tìm thấy bản cập nhật mới!")
                self.update_status("Bắt đầu tải về...", 20)
                self.download_update(download_url, remote_version, version_file_path)
            else:
                self.label.config(text="Phiên bản đã cập nhật mới nhất.")
                self.update_status("Hoàn tất kiểm tra.", 100)
                time.sleep(1)
                self.launch_main_app()

        except urllib.error.URLError:
            self.label.config(text="Không thể kết nối Internet!")
            self.update_status("Sẽ mở ứng dụng hiện tại...", 100)
            time.sleep(2)
            self.launch_main_app()
        except Exception as e:
            traceback.print_exc()
            self.label.config(text="Lỗi kiểm tra cập nhật.")
            self.update_status(f"Chi tiết: {e}", 100)
            time.sleep(3)
            self.launch_main_app()

    def download_update(self, url, new_version, version_file_path):
        try:
            temp_file = "AppChinh_new.exe"
            
            # Xóa file temp cũ nếu còn
            if os.path.exists(temp_file):
                os.remove(temp_file)

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                total_size = int(response.info().get('Content-Length', 0))
                bytes_so_far = 0
                chunk_size = 8192

                with open(temp_file, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_so_far += len(chunk)
                        
                        if total_size > 0:
                            percent = (bytes_so_far / total_size) * 100
                            # Map progress from 20% to 90%
                            mapped_progress = 20 + (percent * 0.7)
                            self.update_status(f"Đang tải dữ liệu: {bytes_so_far / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB", mapped_progress)

            self.update_status("Đang cài đặt bản cập nhật...", 95)
            
            # Ghi đè file cũ
            if os.path.exists(APP_EXECUTABLE_NAME):
                # Đổi tên file cũ đi (đề phòng đang chạy ngầm không ghi đè được)
                backup_file = APP_EXECUTABLE_NAME + ".bak"
                if os.path.exists(backup_file):
                    try:
                        os.remove(backup_file)
                    except:
                        pass
                try:
                    os.rename(APP_EXECUTABLE_NAME, backup_file)
                except Exception as e:
                    print(f"Không thể đổi tên file cũ: {e}")
            
            os.rename(temp_file, APP_EXECUTABLE_NAME)
            
            # Lưu version mới
            with open(version_file_path, "w", encoding="utf-8") as f:
                f.write(new_version)

            self.update_status("Cập nhật thành công!", 100)
            time.sleep(1)
            self.launch_main_app()

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Lỗi Cập Nhật", f"Đã xảy ra lỗi trong quá trình tải bản cập nhật:\n{e}\n\nVẫn tiếp tục mở phiên bản cũ.")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            self.launch_main_app()

if __name__ == "__main__":
    # Đăng ký chạy dưới quyền Admin trong một số trường hợp (tùy chọn)
    root = tk.Tk()
    app = AutoUpdaterApp(root)
    root.mainloop()
