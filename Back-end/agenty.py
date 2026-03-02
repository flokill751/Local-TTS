import subprocess
from pathlib import Path
import time

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel

BASE = Path(__file__).resolve().parent

# ====== Piper (TTS) ======
PIPER_EXE = BASE / "piper" / "piper.exe"
MODEL = BASE / "voz" / "pt_BR-faber-medium.onnx"
CONFIG = BASE / "voz" / "pt_BR-faber-medium.onnx.json"

OUT_DIR = BASE / "out"
OUT_DIR.mkdir(exist_ok=True)

def tts_piper(texto: str, out_wav: Path):
    p = subprocess.run(
        [str(PIPER_EXE), "-m", str(MODEL), "-c", str(CONFIG), "-f", str(out_wav)],
        input=texto,
        text=True,
        capture_output=True
    )
    if p.returncode != 0:
        raise RuntimeError(f"Piper falhou:\n{p.stderr}")

def play_wav(wav_path: Path):
    data, sr = sf.read(str(wav_path), dtype="float32")
    sd.play(data, sr)
    sd.wait()

# ====== STT (Whisper) ======
# "small" é um bom equilíbrio. Se ficar pesado, use "base".
stt = WhisperModel("small", device="cpu", compute_type="int8")

def record_wav(out_path: Path, seconds=5, sr=16000):
    print(f"\n🎤 Gravando {seconds}s... fale agora!")
    audio = sd.rec(int(seconds * sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    audio = np.squeeze(audio)
    sf.write(str(out_path), audio, sr)
    return out_path

def stt_whisper(wav_path: Path) -> str:
    segments, _info = stt.transcribe(str(wav_path), language="pt")
    text = " ".join(seg.text.strip() for seg in segments).strip()
    return text

# ====== LLM local via HTTP (Ollama) ======
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

SYSTEM_STYLE = (
    "Você é um assistente mais muito puto da vida "
    "Responda em português do Brasil, diretamente puto. "
    "Se fizer sentido, use uma pitada de mau humor."
)

def llm_ollama(user_text: str) -> str:
    prompt = f"{SYSTEM_STYLE}\n\nUsuário: {user_text}\nAssistente:"
    r = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=180
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()

# ====== Loop ======
def main():
    print("✅ STT + LLM(HTTP local) + TTS(Piper)")
    print("Dica: fale frases curtas. Ctrl+C para sair.\n")

    while True:
        mic_wav = OUT_DIR / "mic.wav"
        reply_wav = OUT_DIR / "reply.wav"

        record_wav(mic_wav, seconds=5)
        user_text = stt_whisper(mic_wav)

        if not user_text:
            print("🤷 Não peguei nada. Tenta de novo.")
            continue

        print("📝 Você:", user_text)

        try:
            reply = llm_ollama(user_text)
        except Exception as e:
            print("❌ Erro no Ollama HTTP:", e)
            continue

        if not reply:
            print("🤖 (sem resposta do LLM)")
            continue

        print("🤖 LLM:", reply)

        tts_piper(reply, reply_wav)
        print("🔊 Falando...")
        play_wav(reply_wav)

        time.sleep(0.2)

if __name__ == "__main__":
    main()