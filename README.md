# 🎙️ Local-TTS — Assistente de Voz 100% Local

Um assistente de voz que roda **completamente offline** na sua máquina, sem depender de nenhuma API externa paga.  
Você fala → ele ouve → processa com IA → responde em voz alta.

---

## 🧠 Como funciona

O projeto combina **três tecnologias** rodando localmente:

```
🎤 Microfone
    │
    ▼
🔊 STT — Faster-Whisper  (fala → texto)
    │
    ▼
🤖 LLM — Ollama / LLaMA 3.1  (texto → resposta)
    │
    ▼
🔈 TTS — Piper  (resposta → áudio em português)
    │
    ▼
🔊 Alto-falante
```

| Componente | Tecnologia | Descrição |
|---|---|---|
| **STT** | [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) | Transcreve sua fala em texto (modelo `small`, offline) |
| **LLM** | [Ollama](https://ollama.com) + LLaMA 3.1 | Processa o texto e gera uma resposta inteligente |
| **TTS** | [Piper](https://github.com/rhasspy/piper) | Converte a resposta em áudio com voz em pt-BR |

> **Personalidade:** O assistente já vem configurado com uma personalidade bem-humorada e sarcástica em português do Brasil 😄

---

## 📁 Estrutura do Projeto

```
Local-TTS/
└── Back-end/
    ├── agenty.py               # Script principal — o coração do projeto
    ├── piper/                  # Executável do Piper TTS (Windows)
    │   ├── piper.exe
    │   ├── espeak-ng.dll
    │   ├── onnxruntime.dll
    │   └── ...
    ├── voz/                    # Modelo de voz em português brasileiro
    │   ├── pt_BR-faber-medium.onnx
    │   └── pt_BR-faber-medium.onnx.json
    └── out/                    # Arquivos de áudio gerados durante uso
        ├── mic.wav             # Gravação do microfone
        └── reply.wav           # Resposta gerada pelo assistente
```

---

## ⚙️ Pré-requisitos

### 1. Python 3.10+
Baixe em: https://www.python.org/downloads/

### 2. Ollama (servidor LLM local)
```bash
# Baixe e instale em: https://ollama.com
# Depois rode o modelo LLaMA 3.1:
ollama run llama3.1
```
> O Ollama precisa estar rodando em segundo plano antes de iniciar o assistente.

### 3. Dependências Python
Instale todas com:
```bash
pip install faster-whisper sounddevice soundfile numpy requests
```

---

## 🚀 Como usar

### 1. Clone o repositório
```bash
git clone git@github.com:flokill751/Local-TTS.git
cd Local-TTS
```

### 2. Instale as dependências
```bash
pip install faster-whisper sounddevice soundfile numpy requests
```

### 3. Suba o Ollama com o LLaMA 3.1
Abra um terminal separado e rode:
```bash
ollama run llama3.1
```

### 4. Execute o assistente
```bash
cd Back-end
python agenty.py
```

---

## 🎤 Usando o assistente

Depois de rodar o script, o assistente vai:

1. Imprimir `✅ STT + LLM(HTTP local) + TTS(Piper)`
2. Gravar **5 segundos** de áudio pelo microfone
3. Transcrever o que você falou (Whisper)
4. Enviar para o LLaMA 3.1 e gerar uma resposta
5. Falar a resposta em voz alta (Piper, voz pt-BR)
6. Repetir o ciclo automaticamente

> Para sair, pressione **Ctrl + C**

---

## ⚠️ Observações importantes

- O projeto foi feito para **Windows** (o `piper.exe` e as DLLs incluídas são para Windows)
- Na **primeira execução**, o Whisper vai baixar o modelo `small` (~500MB) automaticamente via internet
- O Ollama com LLaMA 3.1 requer pelo menos **8GB de RAM** para rodar com fluidez
- O modelo de voz já incluso é o `pt_BR-faber-medium` — uma voz masculina natural em português do Brasil
- Se o Whisper estiver pesado, edite a linha 38 do `agenty.py` e troque `"small"` por `"base"` (mais leve, menos preciso)

---

## 🔧 Personalização

### Mudar a personalidade do assistente
Edite a variável `SYSTEM_STYLE` no arquivo `agenty.py`:
```python
SYSTEM_STYLE = (
    "Você é um assistente mais muito puto da vida "
    "Responda em português do Brasil, diretamente puto. "
    "Se fizer sentido, use uma pitada de mau humor."
)
```

### Mudar o tempo de gravação
Por padrão são **5 segundos** de gravação. Para alterar, edite a linha:
```python
record_wav(mic_wav, seconds=5)  # ← mude o valor aqui
```

### Mudar o modelo LLM
Por padrão usa `llama3.1`. Para usar outro modelo (ex: `mistral`, `gemma`):
```python
OLLAMA_MODEL = "llama3.1"  # ← troque pelo nome do modelo no Ollama
```

---

## 🛠️ Tecnologias utilizadas

- **Python** — linguagem principal
- **[Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)** — STT (Speech-to-Text) eficiente, versão otimizada do OpenAI Whisper
- **[Ollama](https://ollama.com)** — servidor local para rodar LLMs como LLaMA, Mistral etc.
- **[Piper TTS](https://github.com/rhasspy/piper)** — síntese de voz neural, rápida e offline
- **sounddevice / soundfile** — gravação e reprodução de áudio
- **numpy** — processamento de arrays de áudio

---

## 📄 Licença

Este projeto é de uso pessoal/educacional. Sinta-se livre para modificar e adaptar.