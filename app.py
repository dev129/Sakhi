import streamlit as st
import sounddevice as sd
import queue, time, json
from vosk import Model, KaldiRecognizer
import pygame


pygame.mixer.init()
try:
    pygame.mixer.music.stop()
except:
    pass


st.set_page_config(page_title="🛡️ Women Safety App", layout="centered")
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #ff9ccf, #ffdde1) !important;
    }
    [data-testid="stTextInput"] input {
        background-color: #ffe6f0;
        color: #d63384;
    }
    [data-testid="stWidgetLabel"] {
        color: #d63384 !important;
        font-weight: bold;
    }
    .contacts-box {
        background: rgba(255,255,255,0.6);
        padding: 10px;
        border-radius: 12px;
        margin-bottom: 10px;
    }
    .helpline-box {
        background-color: #fff0f5;
        border-left: 5px solid #d63384;
        padding: 10px 15px;
        margin-bottom: 10px;
        border-radius: 8px;
        font-size: 16px;
        color: #333;
    }
    .timer {
        font-size: 48px;
        font-weight: bold;
        color: #d63384;
        text-align: center;
        margin: 20px 0;
    }
    button {
        background-color: #d63384 !important;
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    button:hover {
        background-color: #e85ca4 !important;
        box-shadow: 0 0 10px #ffb6d9;
    }
    button:active {
        box-shadow: 0 0 15px #ff69b4;
        transform: scale(0.98);
    }
    </style>
""", unsafe_allow_html=True)

# ─── 2) Title ─────────────────────────────────────────────────────────────────
st.title("👩‍🦺 Women Safety Voice-Activated SOS")

# ─── 3) Emergency Contacts ────────────────────────────────────────────────────
if "contacts" not in st.session_state:
    st.session_state.contacts = ["Police: 100"]

st.markdown("### 📇 Your Emergency Contacts")
with st.container():
    st.markdown("<div class='contacts-box'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("👤 Name", key="name_input")
    with col2:
        number = st.text_input("📞 Phone Number", key="number_input")

    if st.button("➕ Add Contact", key="add_btn"):
        if name and number:
            st.session_state.contacts.append(f"{name}: {number}")
            st.success(f"Added: {name} ({number})")
        else:
            st.warning("Please enter both name and number.")

    if st.session_state.contacts:
        st.write("Your Contacts:")
        for c in st.session_state.contacts:
            st.markdown(f"- {c}")
    else:
        st.info("No personal contacts added yet.")
    st.markdown("</div>", unsafe_allow_html=True)

# ─── 4) National Helplines ────────────────────────────────────────────────────
st.markdown("### 🚨 National Emergency Helplines")
default_helplines = {
    "Police": "100",
    "Women Helpline (Mahila)": "1091",
    "Child Helpline": "1098",
    "Ambulance": "102",
    "National Emergency Number": "112"
}
for label, num in default_helplines.items():
    st.markdown(
        f"<div class='helpline-box'><strong>{label}</strong>: 📞 {num}</div>",
        unsafe_allow_html=True
    )

# ─── 5) Audio & Vosk Setup ───────────────────────────────────────────────────
q_main  = queue.Queue()
q_reply = queue.Queue()
model   = Model("vosk-model-small-hi-0.22")
rec_main = KaldiRecognizer(model, 16000)
rec_safe = KaldiRecognizer(model, 16000)

def cb_main(indata, frames, time_info, status):
    if status:
        print("Main:", status)
    q_main.put(bytes(indata))

def cb_reply(indata, frames, time_info, status):
    if status:
        print("Reply:", status)
    q_reply.put(bytes(indata))

def play_siren():
    pygame.mixer.music.load("Siren.mp3")
    pygame.mixer.music.play()

def sos_listener():
    with sd.RawInputStream(
        samplerate=16000, blocksize=4000, dtype="int16",
        channels=1, callback=cb_main
    ):
        st.info("🎤 Listening for 'bachao', 'बचाओ' or 'help'…")
        while True:
            data = q_main.get()
            if rec_main.AcceptWaveform(data):
                txt = json.loads(rec_main.Result())["text"].lower()
                st.write("Heard:", txt)
                if any(w in txt for w in ("bachao", "बचाओ", "help")):
                    return True

def safety_countdown():
    timer_placeholder = st.empty()
    stream = sd.RawInputStream(
        samplerate=16000, blocksize=4000, dtype="int16",
        channels=1, callback=cb_reply
    )
    stream.start()

    for sec in range(5, 0, -1):
        timer_placeholder.markdown(
            f"<div class='timer'>{sec} s</div>",
            unsafe_allow_html=True
        )
        deadline = time.time() + 1
        while time.time() < deadline:
            if not q_reply.empty():
                chunk = q_reply.get()
                if rec_safe.AcceptWaveform(chunk):
                    ans = json.loads(rec_safe.Result())["text"].lower()
                    if any(k in ans for k in ("safe", "theek", "ठीक", "yes")):
                        timer_placeholder.success("✅ Safety confirmed.")
                        stream.stop()
                        return True
        time.sleep(0.1)

    stream.stop()
    timer_placeholder.error("🚨 No confirmation!")
    return False

def main_sos():
    if sos_listener():
        ok = safety_countdown()
        if not ok:
            play_siren()
            st.warning("📢 Notifications sent to police and your emergency contacts.")
            st.markdown("#### 📇 Notified Contacts:")
            for c in st.session_state.contacts:
                st.markdown(f"- {c}")

# ─── 6) Start Monitoring Button (Bottom) ─────────────────────────────────────
st.markdown("---")
st.markdown("### 🚨 Alert Check")
if st.button("🛡️ Start Monitoring", key="monitor_btn"):
    if not st.session_state.contacts:
        st.error("➕ Add at least one emergency contact first.")
    else:
        main_sos()
        st.info("Monitoring ended. Refresh to restart.")