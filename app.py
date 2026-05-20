import re
import requests 
import tkinter as tk
from tkinter import messagebox, font as tkfont, ttk
import base64
from PIL import Image, ImageTk
from io import BytesIO

API_URL = "https://rwfc.net/api/leaderboard/player/{}"
current_friend_code = None
data_window = None
current_font = "@FOT-RodinNTLG Pro EB"
ui_elements = {}


def format_friend_code(code: str) -> str:
    digits = re.sub(r"\D", "", code)
    if len(digits) != 12:
        return ""
    return f"{digits[0:4]}-{digits[4:8]}-{digits[8:12]}"


def fetch_player_data(friend_code_input: str = None) -> None:
    global current_friend_code, data_window
    
    if friend_code_input:
        raw_code = friend_code_input.strip()
    else:
        raw_code = friend_code_entry.get().strip()
    
    friend_code = format_friend_code(raw_code)
    if not friend_code:
        messagebox.showerror("Invalid Code", "Enter a 12-digit friend code like 1159-6423-1010.")
        return

    status_label.config(text="Fetching...")
    window.update_idletasks()

    try:
        response = requests.get(API_URL.format(friend_code), timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        messagebox.showerror("Request Failed", f"Could not fetch data:\n{exc}")
        status_label.config(text="")
        return

    current_friend_code = friend_code
    data = response.json()
    vr_value = data.get("vr", "N/A")
    mii_image_base64 = data.get("miiImageBase64", "")

    # Create new data window if it doesn't exist or was closed
    if data_window is None or not data_window.winfo_exists():
        create_data_window(vr_value, mii_image_base64)
    else:
        update_data_window(vr_value, mii_image_base64)
    
    status_label.config(text="Overlay loaded.")


def create_data_window(vr_value, mii_image_base64) -> None:
    global data_window
    
    data_window = tk.Toplevel(window)
    data_window.title("overlay display")
    data_window.geometry("350x180")
    data_window.resizable(False, False)
    data_window.config(bg="#00FF00")
    
    frame_data = tk.Frame(data_window, padx=14, pady=14, bg="#00FF00")
    frame_data.pack(fill="both", expand=True)
    
    # Display VR data
    vr_frame = tk.Frame(frame_data, bg="#00FF00")
    vr_frame.pack(fill="x", pady=(0, 10), anchor="w")
    vr_frame.columnconfigure(1, weight=0)
    
    vr_combined = tk.Label(vr_frame, text=f"VR: {vr_value}", font=("@FOT-RodinNTLG Pro EB", 18, "bold"), bg="#00FF00", fg="white")
    vr_combined.grid(row=0, column=0, sticky="nsw", padx=(0, 0), rowspan=2)
    ui_elements["data_vr_label"] = vr_combined


    if mii_image_base64:
        try:
            image_data = base64.b64decode(mii_image_base64)
            image = Image.open(BytesIO(image_data))
            image = image.resize((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            mii_label = tk.Label(vr_frame, image=photo, bg="#00FF00")
            mii_label.image = photo
            mii_label.grid(row=0, column=1, rowspan=2, padx=(2, 0))
            ui_elements["data_mii_label"] = mii_label
        except Exception as e:
            print(f"Error loading Mii image: {e}")


def update_data_window(vr_value, mii_image_base64) -> None:
    if data_window is None or not data_window.winfo_exists():
        return

    vr_label = ui_elements.get("data_vr_label")
    if vr_label:
        vr_label.config(text=f"VR: {vr_value}")

    if mii_image_base64:
        try:
            image_data = base64.b64decode(mii_image_base64)
            image = Image.open(BytesIO(image_data))
            image = image.resize((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            mii_label = ui_elements.get("data_mii_label")
            if mii_label and mii_label.winfo_exists():
                mii_label.config(image=photo)
                mii_label.image = photo
            else:
                mii_label = tk.Label(vr_label.master, image=photo, bg="#00FF00")
                mii_label.image = photo
                mii_label.grid(row=0, column=1, rowspan=2, padx=(2, 0))
                ui_elements["data_mii_label"] = mii_label
        except Exception as e:
            print(f"Error updating Mii image: {e}")
    else:
        mii_label = ui_elements.get("data_mii_label")
        if mii_label and mii_label.winfo_exists():
            mii_label.destroy()
            ui_elements.pop("data_mii_label", None)


def change_font(new_font: str) -> None:
    global current_font
    current_font = new_font
    
    for widget_name, widget in ui_elements.items():
        try:
            current_font_config = widget.cget("font")
            if current_font_config:
                font_parts = tkfont.Font(font=current_font_config).actual()
                size = font_parts.get("size", 11)
                weight = font_parts.get("weight", "normal")
                new_font_tuple = (current_font, size, weight)
                widget.config(font=new_font_tuple)
        except Exception as e:
            print(f"Error updating font for {widget_name}: {e}")


window = tk.Tk()
window.title("vr overlay settings")
window.geometry("420x280")
window.resizable(False, False)
window.config(bg="#3A3A3A")

frame = tk.Frame(window, padx=14, pady=14, bg="#3A3A3A")
frame.pack(fill="both", expand=True)

# Font selector
font_frame = tk.Frame(frame, bg="#3A3A3A")
font_frame.pack(anchor="w", pady=(0, 10))
font_label = tk.Label(font_frame, text="Font:", font=("@FOT-RodinNTLG Pro EB", 9), bg="#3A3A3A", fg="white")
font_label.pack(side=tk.LEFT, padx=(0, 5))
available_fonts = sorted(tkfont.families())
font_combo = ttk.Combobox(font_frame, values=available_fonts, state="readonly", width=20)
font_combo.set("@FOT-RodinNTLG Pro EB")
font_combo.pack(side=tk.LEFT)
font_combo.bind("<<ComboboxSelected>>", lambda e: change_font(font_combo.get()))

instruction = tk.Label(frame, text="Enter your friend code", font=("@FOT-RodinNTLG Pro EB", 11), bg="#3A3A3A", fg="white")
instruction.pack(anchor="w")
ui_elements["instruction"] = instruction

friend_code_entry = tk.Entry(frame, font=("@FOT-RodinNTLG Pro EB", 11), width=24)
friend_code_entry.pack(pady=(6, 10))
friend_code_entry.focus()
ui_elements["friend_code_entry"] = friend_code_entry

button_row = tk.Frame(frame, bg="#3A3A3A")
button_row.pack(pady=(0, 12))

fetch_button = tk.Button(button_row, text="Fetch Data", command=fetch_player_data, font=("@FOT-RodinNTLG Pro EB", 11), width=16)
fetch_button.pack(side=tk.LEFT, padx=(0, 5))
ui_elements["fetch_button"] = fetch_button

status_label = tk.Label(frame, text="", font=("@FOT-RodinNTLG Pro EB", 9), fg="white", bg="#00FF00")
status_label.pack(anchor="w")
ui_elements["status_label"] = status_label

window.mainloop()
