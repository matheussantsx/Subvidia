<div align="center">

<img src="logo-subvidia.jpeg" alt="Subvidia" width="520"/>

# Subvidia

**Transcrição de vídeos com aceleração da placa de vídeo**

Transcreve vídeos `.mp4` e `.mkv` localmente usando **Faster-Whisper** com aceleração via **CUDA**.
Gera `.srt` (legendas com timestamps por palavra) e `.txt` (texto plano).

---

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![CUDA](https://img.shields.io/badge/CUDA-12.x-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![NVIDIA](https://img.shields.io/badge/NVIDIA-GPU-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)
![Whisper](https://img.shields.io/badge/Faster--Whisper-large--v3-412991?style=for-the-badge&logo=openai&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

</div>

---

## Requisitos

| Item       | Versão                          |
| ---------- | ------------------------------- |
| GPU NVIDIA | RTX 3060+ (12GB VRAM recomendado) |
| CUDA       | 12.x                            |
| Python     | 3.10+                           |
| FFmpeg     | Qualquer versão recente         |

---

## Instalação

```bash
# Clone / copie os arquivos e entre na pasta
cd subvideo

# Rode o setup (Linux/Ubuntu)
chmod +x setup.sh
./setup.sh
```

**Ou manualmente:**

```bash
# FFmpeg
sudo apt install ffmpeg

# PyTorch com CUDA 12.1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Faster-Whisper
pip install faster-whisper
```

---

## Uso

```bash
# Estrutura de pastas
mkdir -p data subtitles

# Coloque seus vídeos em ./data e rode:
python transcribe.py

# Ou especifique caminhos
python transcribe.py --data /mnt/videos --subtitles /mnt/legendas

# Escolha o modelo (tiny / base / small / medium / large-v3)
python transcribe.py --model medium

# Defina o idioma (pt, en, es...) ou auto-detect
python transcribe.py --language pt

# Mais palavras por bloco de legenda (padrão: 8)
python transcribe.py --max-words 12

# Aceitar mais extensões
python transcribe.py --ext mp4 mkv avi webm
```

---

## Saída

Para cada vídeo `data/filme.mp4`, são gerados:

```
subtitles/
├── filme.srt   ← legendas com timestamps, pronto para VLC/MPV/etc.
└── filme.txt   ← transcrição plana completa
```

**Exemplo de `.srt` gerado:**

```
1
00:00:00,120 --> 00:00:03,840
Olá e bem-vindo à apresentação de hoje.

2
00:00:03,960 --> 00:00:07,200
Vamos falar sobre machine learning.
```

---

## Performance esperada (RTX 3060 12GB)

| Vídeo   | Tempo de transcrição |
| ------- | -------------------- |
| 10 min  | ~30-60 segundos      |
| 1 hora  | ~3-5 minutos         |
| 2 horas | ~6-10 minutos        |

> O Faster-Whisper processa em **batch** com `float16` na GPU — quanto maior o vídeo, mais eficiente fica.

---

## Limitações

- **Modelo grande**: `large-v3` exige ~10GB de VRAM. Use `medium` ou `small` em GPUs menores.
- **Áudio ruidoso**: Performance cai em ambientes com muito ruído de fundo.
- **Múltiplos falantes**: Sem diarização (identificação de locutor) nesta versão.

---

## Arquitetura

```
video.mp4
    │
    ▼ FFmpeg (extrai áudio)
audio.wav  ← 16kHz, mono, PCM 16-bit
    │
    ▼ Faster-Whisper large-v3 (CUDA / float16)
(texto + word timestamps)
    │
    ├──▶ subtitles/video.txt  (texto plano)
    └──▶ subtitles/video.srt  (legendas agrupadas)
```

---

## Stack

<div align="center">

| Camada            | Tecnologia                                                              |
| ----------------- | ----------------------------------------------------------------------- |
| **Linguagem**     | Python 3.10+                                                            |
| **Modelo ASR**    | [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (large-v3)  |
| **Deep Learning** | PyTorch + CUDA 12.1                                                     |
| **Áudio/Vídeo**   | FFmpeg + ffprobe                                                        |
| **Aceleração**    | NVIDIA GPU (CUDA cores + Tensor cores)                                  |

</div>

---

## Licença

- **Faster-Whisper**: MIT
- **Whisper (OpenAI)**: MIT
- **FFmpeg**: LGPL/GPL
- **Este script**: MIT
