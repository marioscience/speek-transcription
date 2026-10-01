# <==> Speek

**Speek** is a lightning-fast, privacy-first, global dictation and translation tool built natively for Linux. 

Powered entirely offline by `faster-whisper`, Speek lives in your system tray and listens for a global hotkey. Whether you want to dictate an email into your browser, or transcribe an online meeting directly from your desktop's audio output, Speek processes the audio locally and magically types the text directly into whatever window you have focused.

## <==> Features

* **<==> 100% Local AI:** No cloud, no subscriptions. Everything runs locally on your machine.
* **<==> Global Hotkey:** Press `Ctrl+Alt+V` from anywhere in your OS to start and stop dictation.
* **<==> Live Hot-Swapping:** Seamlessly toggle between capturing your **Microphone** or your **Desktop Audio** on the fly.
* **<==> Native Translation:** Click the `[EN]` toggle to instantly translate any spoken foreign language into English text.
* **<==> Linux Native:** Built for Wayland and X11, leveraging raw PulseAudio/PipeWire pipelines for zero-latency capture.

---

## <==> Prerequisites

Speek requires a few Linux-native tools to capture audio and emulate your keyboard.

```bash
# Install audio tools and ydotool (for keyboard injection on Wayland/X11)
sudo apt update
sudo apt install pulseaudio-utils ydotool
```

> **Note on ydotool:** Speek uses `ydotool` to inject text into your active windows. You must ensure the `ydotoold` daemon is running in the background for typing to work!

---

## <==> Quick Start & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/speek.git
   cd speek
   ```

2. **Set up a Python Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the App:**
   ```bash
   python -m speek.main
   ```

*(On first launch, Speek will download the `faster-whisper` AI model. This may take a minute or two depending on your internet connection).*

---

## <==> How to Use

Speek runs silently in the background until you summon it.

1. **Start Dictating:** Focus your cursor on any text box (browser, terminal, text editor) and press **`Ctrl+Alt+V`**.
2. **The GUI Appears:** A sleek floating window will appear on your screen, indicating that the microphone is hot.
3. **Stop & Type:** Press **`Ctrl+Alt+V`** again to stop recording. The AI will instantly transcribe your audio and type it directly into your focused window!

### <==> The UI Toggles

While the GUI is visible, you can click the buttons to dynamically alter the AI's behavior:

* **`[<==> Desktop] / [<==> Mic]`**: Instantly hot-swap the hardware audio source. Switch between dictating with your voice, or transcribing a video/meeting playing on your computer.
* **`[<==> EN]`**: When enabled, the AI will detect foreign languages (e.g., Spanish, French, Japanese) and natively translate them into English before typing them out.

---

## <==> Running as a System Daemon (Advanced)

For the best experience, Speek is designed to be run as a background `systemd` service so it's always ready when you boot your computer.

You can manage your local service using:
```bash
systemctl --user start speek.service
systemctl --user restart speek.service
systemctl --user status speek.service
```

Enjoy your new superpower! <==>
