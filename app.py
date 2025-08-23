import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
import pygame
import threading
import time
import tkinter as tk

# Queues
main_q = queue.Queue()
safety_q = queue.Queue()

# Load offline Hindi model
model = Model("vosk-model-small-hi-0.22")   # or vosk-model-hi-0.22 for full model
recognizer = KaldiRecognizer(model, 16000)

# Initialize pygame mixer
pygame.mixer.init()

# --- Tkinter GUI ---
root = tk.Tk()
root.title("🚨 SOS System")
root.geometry("400x200")

label = tk.Label(root, text="🎤 Listening for 'Bachao' or 'Help'...",
                 font=("Arial", 16), wraplength=350, justify="center")
label.pack(expand=True)

def alarm():
    pygame.mixer.music.load("Siren.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue

def safety_callback(indata, frames, time_info, status):
    if status:
        print(status)
    safety_q.put(bytes(indata))

def confirm_safety():
    """Countdown with Tkinter that stops if user says 'safe' or 'theek hai'"""
    label.config(text="⚠️ SOS detected! Confirming safety...")

    recognizer_local = KaldiRecognizer(model, 16000)

    def run_countdown():
        with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                               channels=1, callback=safety_callback):

            for i in range(5, 0, -1):
                label.config(text=f"⏳ Countdown: {i}\nSay 'Theek hai' or 'Safe' to cancel")
                root.update()

                start = time.time()
                while time.time() - start < 1:  # 1 second loop
                    if not safety_q.empty():
                        data = safety_q.get()
                        if recognizer_local.AcceptWaveform(data):
                            result = recognizer_local.Result()
                            text = json.loads(result)["text"].lower()
                            print("Response:", text)

                            if "yes" in text or "safe" in text or "theek" in text or "ठीक" in text:
                                label.config(text="✅ Safety confirmed. Countdown stopped.")
                                root.update()
                                return  # exit immediately (no siren)

            # If loop finishes without safety confirmation
            label.config(text="🚨 No safety confirmation.\nALARM TRIGGERED!")
            root.update()
            threading.Thread(target=alarm).start()

    threading.Thread(target=run_countdown).start()

def main_callback(indata, frames, time_info, status):
    if status:
        print(status)
    main_q.put(bytes(indata))

def main_loop():
    with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16',
                           channels=1, callback=main_callback):
        print("🎤 Listening for 'Bachao' or 'Help' (Offline)...")
        while True:
            data = main_q.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                text = json.loads(result)["text"].lower()
                print("You said:", text)

                if "bachao" in text or "help" in text or "बचाओ" in text:
                    confirm_safety()

# Run listener in a background thread
threading.Thread(target=main_loop, daemon=True).start()

# Start Tkinter GUI loop
root.mainloop()
