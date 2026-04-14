import tkinter as tk
from cryptography.fernet import Fernet
import os

def generate():
    if os.path.exists("secret.key"):
        status.config(text="Key already exists!", fg="red")
    else:
        key = Fernet.generate_key()
        with open("secret.key", "wb") as f:
            f.write(key)
        status.config(text="Key generated successfully!", fg="green")

root = tk.Tk()
root.title("Key Generator")
root.geometry("300x200")

tk.Label(root, text="Generate Secret Key", font=("Arial", 14)).pack(pady=20)
tk.Button(root, text="Generate", command=generate).pack(pady=10)

status = tk.Label(root, text="")
status.pack()

root.mainloop()