import socket
import os
import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox

SERVER_IP = "172.20.10.7"  # Replace with your server IP
SERVER_PORT = 5001
BUFFER_SIZE = 4096
CHUNK_SIZE = 8192

class FileTransferClient:
    def _init_(self, root):
        self.root = root
        self.root.title("File Transfer Client")
        self.root.geometry("700x550")
        self.root.configure(bg="#1E3A8A")

        self.client_socket = None
        self.create_login_window()

    def create_login_window(self):
        self.login_frame = ttk.Frame(self.root, padding=20)
        self.login_frame.pack(expand=True)

        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1)

        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1)

        self.login_button = ttk.Button(self.login_frame, text="Login", command=self.connect_to_server)
        self.login_button.grid(row=2, column=0, columnspan=2)

    def connect_to_server(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((SERVER_IP, SERVER_PORT))
            self.client_socket.sendall(f"{username} {password}".encode())
            response = self.client_socket.recv(BUFFER_SIZE).decode()

            if "Authentication failed" in response:
                messagebox.showerror("Login Failed", response)
                self.client_socket.close()
            else:
                self.login_frame.destroy()
                self.create_main_window()
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def create_main_window(self):
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(expand=True, fill="both")

        self.status_label = ttk.Label(self.main_frame, text="Click 'List Files' to see available files.")
        self.status_label.pack(pady=5)

        self.file_list = scrolledtext.ScrolledText(self.main_frame, width=70, height=10)
        self.file_list.pack(pady=10)

        self.progress = ttk.Progressbar(self.main_frame, length=500, mode="determinate")
        self.progress.pack()
        self.progress_label = ttk.Label(self.main_frame, text="0%")
        self.progress_label.pack()

        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=15)

        ttk.Button(button_frame, text="List Files", command=self.list_files).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Download", command=self.get_file).grid(row=0, column=1, padx=10)
        ttk.Button(button_frame, text="Exit", command=self.exit_client).grid(row=0, column=2, padx=10)

    def list_files(self):
        try:
            self.client_socket.sendall(b"LIST")
            files = self.client_socket.recv(BUFFER_SIZE).decode()
            self.file_list.delete("1.0", tk.END)
            self.file_list.insert(tk.END, files)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list files: {e}")

    def get_file(self):
        filename = simpledialog.askstring("Download File", "Enter filename to download:")
        if filename:
            threading.Thread(target=self.receive_file, args=(filename,), daemon=True).start()

    def generate_unique_filename(self, filename):
        base, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        while os.path.exists(new_filename):
            new_filename = f"{base}_{counter}{ext}"
            counter += 1
        return new_filename

    def receive_file(self, filename):
        try:
            self.client_socket.sendall(f"GET {filename}".encode())

            raw_metadata = self.client_socket.recv(BUFFER_SIZE).decode()
            metadata = json.loads(raw_metadata.split('}', 1)[0] + '}')
            file_size = metadata["file_size"]

            self.progress["maximum"] = file_size
            received_size = 0
            local_filename = self.generate_unique_filename(filename)

            with open(local_filename, "wb") as f:
                while received_size < file_size:
                    chunk = self.client_socket.recv(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    received_size += len(chunk)
                    self.progress["value"] = received_size
                    percent = (received_size / file_size) * 100
                    self.progress_label.config(text=f"{percent:.2f}%")
                    self.root.update_idletasks()

            self.progress_label.config(text="100%")
            messagebox.showinfo("Download Complete", f"{local_filename} downloaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {e}")

    def exit_client(self):
        if self.client_socket:
            try:
                self.client_socket.sendall(b"EXIT")
                self.client_socket.close()
            except:
                pass
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileTransferClient(root)
    root.mainloop()