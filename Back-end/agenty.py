import subprocess
import time
import json
from pathlib import Path

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

BASE = Path(__file__).resolve().parent
CONFIG_FILE = BASE / "config.json"
OUT_DIR = BASE / "out"
OUT_DIR.mkdir(exist_ok=True)

# ====== Piper (TTS - 100% Offline) ======
PIPER_EXE = BASE / "piper" / "piper.exe"
MODEL = BASE / "voz" / "pt_BR-faber-medium.onnx"
CONFIG = BASE / "voz" / "pt_BR-faber-medium.onnx.json"

def tts_piper(texto: str, out_wav: Path):
    p = subprocess.run(
        [str(PIPER_EXE), "-m", str(MODEL), "-c", str(CONFIG), "-f", str(out_wav)],
        input=texto,
        text=True,
        capture_output=True
    )
    if p.returncode != 0:
        raise RuntimeError(f"Piper falhou:\n{p.stderr}")

def play_wav(wav_path: Path, device_id: int):
    data, sr_val = sf.read(str(wav_path), dtype="float32")
    sd.play(data, sr_val, device=device_id)
    sd.wait()

# ====== STT (sounddevice + SpeechRecognition) ======
def record_wav(out_path: Path, device_id: int, seconds=5, sr_rate=16000):
    print(f"\n[MIC] Gravando {seconds}s... fale agora!")
    audio = sd.rec(int(seconds * sr_rate), samplerate=sr_rate, channels=1, dtype="float32", device=device_id)
    sd.wait()
    audio = np.squeeze(audio)
    sf.write(str(out_path), audio, sr_rate)
    return out_path

def stt_google(wav_path: Path) -> str:
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(str(wav_path)) as source:
            audio = recognizer.record(source)
        # Transcrição do Google (gratuita e sem chaves necessárias)
        text = recognizer.recognize_google(audio, language="pt-BR")
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"[Erro] Falha ao conectar com o serviço de STT: {e}")
        return ""
    except Exception as e:
        print(f"[Erro] Erro inesperado no STT: {e}")
        return ""

# ====== LLM local via HTTP (Ollama) ======
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

SYSTEM_STYLE = (
    "Você é um assistente virtual extremamente rabugento, irônico, mal-humorado e sarcástico. "
    "Responda sempre em português do Brasil de forma impaciente e curta, "
    "como se estivesse muito irritado por ter que ajudar o usuário."
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

# ====== Configuração de Dispositivos de Áudio ======
def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("[Erro] Falha ao salvar config.json:", e)

def setup_devices():
    config = load_config()
    devices = sd.query_devices()
    
    input_device = config.get("input_device")
    output_device = config.get("output_device")
    
    # Verifica se os IDs gravados no config ainda são válidos
    if input_device is not None and output_device is not None:
        if 0 <= input_device < len(devices) and 0 <= output_device < len(devices):
            # Retorna direto se já estiver configurado
            return input_device, output_device
            
    print("\n=== CONFIGURAÇÃO DE DISPOSITIVOS DE ÁUDIO ===")
    print("Por favor, selecione os números dos seus dispositivos de som.")
    
    print("\n--- Microfones (Entrada de Áudio) Disponíveis ---")
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"[{i}] {dev['name']} ({dev['hostapi']})")
            
    while True:
        try:
            inp = input("\nEscolha o número do Microfone: ").strip()
            inp_idx = int(inp)
            if 0 <= inp_idx < len(devices) and devices[inp_idx]['max_input_channels'] > 0:
                break
            print("Número inválido para microfone.")
        except ValueError:
            print("Por favor, digite apenas números.")
            
    print("\n--- Fones/Alto-falantes (Saída de Áudio) Disponíveis ---")
    for i, dev in enumerate(devices):
        if dev['max_output_channels'] > 0:
            print(f"[{i}] {dev['name']} ({dev['hostapi']})")
            
    while True:
        try:
            out = input("\nEscolha o número da Saída de Som: ").strip()
            out_idx = int(out)
            if 0 <= out_idx < len(devices) and devices[out_idx]['max_output_channels'] > 0:
                break
            print("Número inválido para saída de som.")
        except ValueError:
            print("Por favor, digite apenas números.")
            
    config["input_device"] = inp_idx
    config["output_device"] = out_idx
    save_config(config)
    print(f"\n[OK] Configurações de áudio salvas em: {CONFIG_FILE.name}")
    return inp_idx, out_idx

# ====== Loop Principal ======
def main():
    # Carrega ou configura dispositivos
    input_idx, output_idx = setup_devices()
    
    print("\n[OK] STT (Google API) + LLM (Ollama HTTP) + TTS (Piper Local)")
    print("Dica: fale frases curtas. Pressione Ctrl+C para sair.\n")

    # Fala de inicialização
    reply_wav = OUT_DIR / "reply.wav"
    try:
        tts_piper("Pronto para ouvir.", reply_wav)
        play_wav(reply_wav, output_idx)
    except Exception as e:
        print("[Erro TTS]:", e)

    while True:
        mic_wav = OUT_DIR / "mic.wav"

        record_wav(mic_wav, input_idx, seconds=5)
        user_text = stt_google(mic_wav)

        if not user_text:
            print("[?] Nao entendi ou nao foi detectado audio. Tente novamente.")
            continue

        print("[Voce]:", user_text)

        try:
            reply = llm_ollama(user_text)
        except Exception as e:
            print("[Erro] Falha de conexao com o Ollama HTTP:", e)
            print("Dica: Certifique-se de que o Ollama esta rodando em segundo plano (ollama run llama3.1)")
            continue

        if not reply:
            print("[IA]: (sem resposta do LLM)")
            continue

        print("[IA]:", reply)
        
        try:
            tts_piper(reply, reply_wav)
            play_wav(reply_wav, output_idx)
        except Exception as e:
            print("[Erro TTS]:", e)

        time.sleep(0.2)

if __name__ == "__main__":
    main()