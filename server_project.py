import socket
import threading
import os
import json

USER_CREDENTIALS = {"admin": "1234", "user": "pass"}
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5001
BUFFER_SIZE = 4096
CHUNK_SIZE = 8192  # Increased chunk size for faster transfer

def list_files(conn):
    files = os.listdir()
    files_list = "\n".join(files) if files else "No files available."
    conn.sendall(files_list.encode())

def send_file(filename, conn, resume_from=0):
    if not os.path.exists(filename):
        conn.sendall(b"ERROR: File not found")
        return

    file_size = os.path.getsize(filename)
    metadata = json.dumps({"file_size": file_size})
    conn.sendall(metadata.encode().ljust(BUFFER_SIZE))

    with open(filename, "rb") as f:
        f.seek(resume_from)
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            conn.sendall(chunk)

def handle_client(conn, addr):
    print(f"Connected to {addr}")
    try:
        credentials = conn.recv(BUFFER_SIZE).decode().strip().split(" ")
        if len(credentials) < 2 or USER_CREDENTIALS.get(credentials[0]) != credentials[1]:
            conn.sendall(b"Authentication failed. Disconnecting.")
            conn.close()
            return

        conn.sendall(b"Authentication successful. Type LIST, GET <filename>, or RESUME <filename> <offset>.")

        while True:
            request = conn.recv(BUFFER_SIZE).decode().strip()
            if not request:
                break

            if request.lower() == "list":
                list_files(conn)
            elif request.lower().startswith("get "):
                filename = request.split(" ", 1)[1]
                send_file(filename, conn)
            elif request.lower().startswith("resume "):
                parts = request.split(" ")
                if len(parts) == 3:
                    filename, resume_from = parts[1], int(parts[2])
                    send_file(filename, conn, resume_from)
            elif request.lower() == "exit":
                break
            else:
                conn.sendall(b"Invalid command.")
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        conn.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(5)

print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

while True:
    conn, addr = server_socket.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()