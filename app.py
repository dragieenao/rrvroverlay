import re
import requests
import tkinter as tk
from tkinter import messagebox
import base64
from PIL import Image, ImageTk
from io import BytesIO

API_URL = "https://rwfc.net/api/leaderboard/player/{}"
current_friend_code = None
data_window = None
ui_elements = {}
refresh_timer = None
REFRESH_INTERVAL = 30000
show_mii_image = True
mii_position = "left"
last_vr = None


def format_friend_code(code: str) -> str:
    digits = re.sub(r"\D", "", code)
    if len(digits) != 12:
        return ""
    return f"{digits[0:4]}-{digits[4:8]}-{digits[8:12]}"


def fetch_player_data(friend_code_input: str = None) -> None:
    global current_friend_code, data_window, last_vr

    raw_code = friend_code_input.strip() if friend_code_input else friend_code_entry.get().strip()
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

    try:
        vr_int = int(vr_value)
        vr_delta = (vr_int - last_vr) if last_vr is not None else None
        last_vr = vr_int
    except (ValueError, TypeError):
        vr_delta = None

    if data_window is None or not data_window.winfo_exists():
        create_data_window(vr_value, mii_image_base64, vr_delta)
    else:
        update_data_window(vr_value, mii_image_base64, vr_delta)

    status_label.config(text="Overlay loaded.")
    schedule_refresh()


def schedule_refresh() -> None:
    global refresh_timer

    if refresh_timer is not None:
        window.after_cancel(refresh_timer)
    refresh_timer = window.after(REFRESH_INTERVAL, auto_refresh)


def auto_refresh() -> None:
    global refresh_timer

    if current_friend_code and data_window and data_window.winfo_exists():
        fetch_player_data(current_friend_code)
    else:
        refresh_timer = None


def get_mii_anchor() -> str:
    return "w" if mii_position == "left" else "e"


def get_delta_anchor() -> str:
    return "e" if mii_position == "left" else "w"


def decode_mii_image(mii_image_base64):
    image_data = base64.b64decode(mii_image_base64)
    image = Image.open(BytesIO(image_data))
    image = image.resize((100, 100), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


def format_delta(delta: int) -> tuple[str, str]:
    if delta > 0:
        return f"▲ +{delta}", "#4488FF"
    elif delta < 0:
        return f"▼ {delta}", "#FF4444"
    else:
        return "▶ +0", "#AAAAAA"


def create_data_window(vr_value, mii_image_base64, vr_delta=None) -> None:
    global data_window

    data_window = tk.Toplevel(window)
    data_window.title("overlay display")
    data_window.geometry("220x230")
    data_window.resizable(False, False)
    data_window.config(bg="#00FF00")

    frame_data = tk.Frame(data_window, padx=14, pady=14, bg="#00FF00")
    frame_data.pack(fill="both", expand=True)

    vr_canvas = tk.Canvas(frame_data, width=192, height=60, bg="#00FF00", highlightthickness=0)
    vr_canvas.pack(anchor="w")
    draw_outlined_text(vr_canvas, f"VR: {vr_value}", 96, 30, ("@FOT-RodinNTLG Pro EB", 18, "bold"))
    ui_elements["data_vr_canvas"] = vr_canvas

    delta_label = tk.Label(frame_data, text="", font=("@FOT-RodinNTLG Pro EB", 13, "bold"), bg="#00FF00")
    delta_label.pack(anchor=get_delta_anchor(), pady=(0, 4))
    ui_elements["data_delta_label"] = delta_label

    if vr_delta is not None:
        text, color = format_delta(vr_delta)
        delta_label.config(text=text, fg=color)

    if mii_image_base64:
        try:
            photo = decode_mii_image(mii_image_base64)
            mii_label = tk.Label(frame_data, image=photo, bg="#00FF00")
            mii_label.image = photo
            if show_mii_image:
                mii_label.pack(anchor=get_mii_anchor(), pady=(4, 0))
            ui_elements["data_mii_label"] = mii_label
        except Exception as e:
            print(f"Error loading Mii image: {e}")


def draw_outlined_text(canvas, text, x, y, font,
                       outline_color="black",
                       fill_color="white") -> None:
    canvas.delete("vr_text")

    outline_width = 1

    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            canvas.create_text(x + dx, y + dy, text=text, font=font, fill=outline_color, tags="vr_text")

    canvas.create_text(x, y, text=text, font=font, fill=fill_color, tags="vr_text")


def update_data_window(vr_value, mii_image_base64, vr_delta=None) -> None:
    if data_window is None or not data_window.winfo_exists():
        return

    vr_canvas = ui_elements.get("data_vr_canvas")
    if vr_canvas:
        draw_outlined_text(vr_canvas, f"VR: {vr_value}", 96, 30, ("@FOT-RodinNTLG Pro EB", 18, "bold"))

    delta_label = ui_elements.get("data_delta_label")
    if delta_label and delta_label.winfo_exists():
        if vr_delta is not None:
            text, color = format_delta(vr_delta)
            delta_label.config(text=text, fg=color)
        else:
            delta_label.config(text="")

    if mii_image_base64:
        try:
            photo = decode_mii_image(mii_image_base64)
            mii_label = ui_elements.get("data_mii_label")
            if mii_label and mii_label.winfo_exists():
                mii_label.config(image=photo)
                mii_label.image = photo
                if show_mii_image:
                    mii_label.pack(anchor=get_mii_anchor(), pady=(4, 0))
                else:
                    mii_label.pack_forget()
            else:
                parent = ui_elements["data_vr_canvas"].master
                mii_label = tk.Label(parent, image=photo, bg="#00FF00")
                mii_label.image = photo
                if show_mii_image:
                    mii_label.pack(anchor=get_mii_anchor(), pady=(4, 0))
                ui_elements["data_mii_label"] = mii_label
        except Exception as e:
            print(f"Error updating Mii image: {e}")
    else:
        mii_label = ui_elements.get("data_mii_label")
        if mii_label and mii_label.winfo_exists():
            mii_label.destroy()
            ui_elements.pop("data_mii_label", None)


def toggle_mii_image() -> None:
    global show_mii_image
    show_mii_image = not show_mii_image

    mii_label = ui_elements.get("data_mii_label")
    if mii_label and mii_label.winfo_exists():
        if show_mii_image:
            mii_label.pack(anchor=get_mii_anchor(), pady=(4, 0))
        else:
            mii_label.pack_forget()


def set_mii_position(pos: str) -> None:
    global mii_position
    mii_position = pos

    mii_label = ui_elements.get("data_mii_label")
    if mii_label and mii_label.winfo_exists() and show_mii_image:
        mii_label.pack_forget()
        mii_label.pack(anchor=get_mii_anchor(), pady=(4, 0))

    delta_label = ui_elements.get("data_delta_label")
    if delta_label and delta_label.winfo_exists():
        delta_label.pack_forget()
        delta_label.pack(anchor=get_delta_anchor(), pady=(0, 4))


FONT = ("@FOT-RodinNTLG Pro EB", 11)

window = tk.Tk()
window.title("vr overlay settings")
window.geometry("420x310")
window.resizable(False, False)
window.config(bg="#3A3A3A")

frame = tk.Frame(window, padx=14, pady=14, bg="#3A3A3A")
frame.pack(fill="both", expand=True)

tk.Label(frame, text="Enter your friend code", font=FONT, bg="#3A3A3A", fg="white").pack(anchor="w")

friend_code_entry = tk.Entry(frame, font=FONT, width=24)
friend_code_entry.pack(pady=(6, 10))
friend_code_entry.focus()

button_row = tk.Frame(frame, bg="#3A3A3A")
button_row.pack(pady=(0, 12))
tk.Button(button_row, text="Fetch Data", command=fetch_player_data, font=FONT, width=10).pack(side=tk.LEFT, padx=(0, 5))
tk.Button(button_row, text="Toggle Mii", command=toggle_mii_image, font=FONT, width=10).pack(side=tk.LEFT)

tk.Label(frame, text="Mii position", font=FONT, bg="#3A3A3A", fg="white").pack(anchor="w", pady=(4, 4))

mii_pos_row = tk.Frame(frame, bg="#3A3A3A")
mii_pos_row.pack(anchor="w", pady=(0, 10))
tk.Button(mii_pos_row, text="Left", command=lambda: set_mii_position("left"), font=FONT, width=10).pack(side=tk.LEFT, padx=(0, 5))
tk.Button(mii_pos_row, text="Right", command=lambda: set_mii_position("right"), font=FONT, width=10).pack(side=tk.LEFT)

status_label = tk.Label(frame, text="", font=("@FOT-RodinNTLG Pro EB", 9), fg="black", bg="#00FF00", relief=tk.RAISED, bd=1)
status_label.pack(anchor="w")

watermark_frame = tk.Frame(window, bg="#3A3A3A")
watermark_frame.place(relx=1.0, rely=1.0, anchor="se", x=-6, y=-6)

try:
    wm_response = requests.get(
        "https://tcrf.net/images/thumb/2/29/Chunithm_Amazon_Character_Final.png/256px-Chunithm_Amazon_Character_Final.png",
        timeout=5
    )
    wm_img = Image.open(BytesIO(wm_response.content)).convert("RGBA")
    wm_img = wm_img.resize((12, 12), Image.Resampling.LANCZOS)
    wm_photo = ImageTk.PhotoImage(wm_img)
    wm_img_label = tk.Label(watermark_frame, image=wm_photo, bg="#3A3A3A")
    wm_img_label.image = wm_photo
    wm_img_label.pack(side=tk.LEFT, padx=(0, 3))
except Exception:
    pass

tk.Label(watermark_frame, text="made by dragiee", font=("@FOT-RodinNTLG Pro EB", 8), fg="#888888", bg="#3A3A3A").pack(side=tk.LEFT)

window.mainloop()
