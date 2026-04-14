import socket
import threading
import tkinter as tk
from tkinter import simpledialog
from cryptography.fernet import Fernet
import os
from datetime import datetime

# ===== KEY =====
KEY_FILE = "secret.key"

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    return open(KEY_FILE, "rb").read()

cipher = Fernet(load_key())

# ===== GUI =====
root = tk.Tk()
root.title("Secure Chat Pro 💬")
root.geometry("800x600")
root.configure(bg="#202225")

# SIDEBAR
sidebar = tk.Frame(root, bg="#2f3136", width=150)
sidebar.pack(side=tk.LEFT, fill=tk.Y)

tk.Label(sidebar, text="Users", bg="#2f3136", fg="white", font=("Arial", 12, "bold")).pack(pady=5)

users_list = tk.Listbox(sidebar, bg="#40444b", fg="white")
users_list.pack(fill=tk.X, padx=5, pady=5)

# MAIN
main_frame = tk.Frame(root, bg="#36393f")
main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

chat_canvas = tk.Canvas(main_frame, bg="#36393f", highlightthickness=0)
chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(main_frame, command=chat_canvas.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

chat_frame = tk.Frame(chat_canvas, bg="#36393f")
chat_canvas.create_window((0, 0), window=chat_frame, anchor="nw")
chat_canvas.configure(yscrollcommand=scrollbar.set)

def update_scroll(event):
    chat_canvas.configure(scrollregion=chat_canvas.bbox("all"))

chat_frame.bind("<Configure>", update_scroll)

# ENTRY
entry_frame = tk.Frame(root, bg="#2f3136")
entry_frame.pack(side=tk.BOTTOM, fill=tk.X)

msg_entry = tk.Entry(entry_frame, bg="#40444b", fg="white")
msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)

send_btn = tk.Button(entry_frame, text="Send", bg="#5865F2", fg="white")
send_btn.pack(side=tk.RIGHT, padx=10)

typing_label = tk.Label(main_frame, text="", bg="#36393f", fg="gray")
typing_label.pack()

# ===== NETWORK =====
clients = []
client_socket = None
username = None

def add_msg(msg, me=False):
    frame = tk.Frame(chat_frame, bg="#36393f")

    bubble = tk.Label(
        frame,
        text=msg,
        bg="#5865F2" if me else "#4f545c",
        fg="white",
        wraplength=400,
        padx=10,
        pady=5
    )

    bubble.pack(anchor="e" if me else "w")
    frame.pack(fill="x", pady=5)

    chat_canvas.update_idletasks()
    chat_canvas.yview_moveto(1)

# SERVER
def handle_client(client, addr):
    while True:
        try:
            data = client.recv(1024)
            if not data:
                break

            msg = cipher.decrypt(data).decode()

            # broadcast
            for c in clients:
                if c != client:
                    c.send(cipher.encrypt(msg.encode()))

            add_msg(msg)

        except:
            break

    clients.remove(client)
    client.close()

def start_server():
    def run():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server.bind(("0.0.0.0", 9999))
        server.listen(5)

        add_msg("Server started")

        while True:
            client, addr = server.accept()
            clients.append(client)
            threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()

    threading.Thread(target=run, daemon=True).start()

# CLIENT
def start_client():
    global client_socket, username

    username = simpledialog.askstring("Username", "Enter name:")
    if not username:
        return

    users_list.insert(tk.END, username)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 9999))

    threading.Thread(target=receive, daemon=True).start()

def receive():
    while True:
        try:
            data = client_socket.recv(1024)
            msg = cipher.decrypt(data).decode()

            if msg.startswith("TYPING:"):
                typing_label.config(text=msg.replace("TYPING:", "") + " typing...")
                root.after(1000, lambda: typing_label.config(text=""))
            else:
                add_msg(msg)

        except:
            break

# SEND
def send():
    if client_socket is None:
        add_msg("Start client first!")
        return

    msg = msg_entry.get()
    if not msg:
        return

    time_now = datetime.now().strftime("%I:%M %p")
    full = f"{time_now} - {username}: {msg}"

    client_socket.send(cipher.encrypt(full.encode()))
    add_msg(full, True)

    msg_entry.delete(0, tk.END)

# TYPING
def typing(event):
    if client_socket:
        try:
            client_socket.send(cipher.encrypt(f"TYPING:{username}".encode()))
        except:
            pass

msg_entry.bind("<KeyPress>", typing)

send_btn.config(command=send)
root.bind("<Return>", lambda e: send())

# BUTTONS
tk.Button(sidebar, text="Start Server", command=start_server).pack(fill=tk.X)
tk.Button(sidebar, text="Start Client", command=start_client).pack(fill=tk.X)

root.mainloop()