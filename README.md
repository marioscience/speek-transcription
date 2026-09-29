# speek (Voice Terminal)

A local, offline voice command and dictation tool for Ubuntu 24.04.
`speek` uses `faster-whisper` on your local GPU to transcribe audio, and can either inject text as keystrokes or pass commands directly to the Antigravity CLI (`agy`).

## Features (v1)
- **Fully Offline**: Zero network calls at runtime. No API keys required.
- **GPU Accelerated**: Uses `faster-whisper` running locally via CUDA.
- **TYPE Mode**: Dictate anywhere. Types text directly into your focused window.
- **ANTIGRAVITY_CLI Mode**: Send voice prompts directly to the Antigravity CLI.
- **Configurable**: Define your own global hotkey and choose Whisper model sizes.

## Installation

1. Clone or navigate to the project directory.
2. Run the setup script to install dependencies:
   ```bash
   ./setup.sh
   ```
   *This will install required system packages (xdotool, ydotool, portaudio19-dev, ffmpeg) and create a Python virtual environment.*

### Wayland & ydotool Permissions
If you are on Wayland, `speek` automatically attempts to use `ydotool` for TYPE mode. `ydotool` requires a background daemon and specific permissions to simulate keystrokes.
1. Enable the `ydotool` daemon:
   ```bash
   sudo systemctl enable --now ydotool
   ```
2. Grant your user access to the `ydotool` socket (usually requires adding your user to a specific group or adjusting socket permissions per `ydotool` documentation).

*(Note on Wayland Hotkeys: Global hotkey listening using `pynput` works flawlessly out-of-the-box on X11. On Wayland, compositors restrict background keylogging. If the hotkey doesn't register on Wayland, you may need to run `speek` as root or configure your compositor to pass specific shortcuts to the app).*

## Usage

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Run the application:
   ```bash
   speek
   ```
   *Alternatively: `python -m speek`*

### Configuration
On your first run, a default config file will be created at:
`~/.config/voice-terminal/config.toml`

```toml
[general]
mode = "type" # Change to "antigravity_cli" to pipe commands to agy

[hotkey]
keys = "<ctrl>+<alt>+v"

[whisper]
model_size = "small"
device = "cuda"
```

## How It Works
- **Toggle Hotkey**: Press the configured hotkey once to start recording. Speak. Press it again to stop.
- **TYPE mode**: The app types the transcribed text directly wherever your cursor is located.
- **ANTIGRAVITY_CLI mode**: The app runs `agy "your transcription"`. You will interact with any `agy` permission prompts directly in the terminal where `speek` is running using your keyboard (`y`/`n`).

## Troubleshooting
- **Microphone not picking up audio**: Check your device index. You can set the exact index of your microphone in `config.toml` under `[audio] device_index`. Use `pyaudio` or `arecord -l` to find your device indexes.
- **CUDA errors**: Ensure your NVIDIA drivers and CUDA toolkit (12.x) are correctly installed and accessible by PyTorch/faster-whisper.

## Roadmap (v2)
- Wake word activation (hands-free).
- Streaming transcription (type as you speak).
- Pi Zero W satellite integration via the Wyoming protocol.
- Antigravity GUI controller mode.
