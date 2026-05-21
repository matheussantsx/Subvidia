# 🎙️ Parakeet Transcriber

Transcreve vídeos `.mp4` e `.mkv` localmente usando **NVIDIA Parakeet TDT 0.6B v2**.  
Gera `.srt` (legendas com timestamps por palavra) e `.txt` (texto plano).

## Requisitos

| Item | Versão |
|---|---|
| GPU NVIDIA | RTX 3060+ (12GB VRAM é ótimo) |
| CUDA | 12.x |
| Python | 3.10+ |
| FFmpeg | Qualquer versão recente |

## Instalação

```bash
# Clone / copie os arquivos e entre na pasta
cd parakeet-transcriber

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

# NeMo
pip install "nemo_toolkit[asr]>=2.0.0"
```

## Uso

```bash
# Estrutura de pastas
mkdir -p data subtitles

# Coloque seus vídeos em ./data e rode:
python transcribe.py

# Ou especifique caminhos
python transcribe.py --data /mnt/videos --subtitles /mnt/legendas

# Mais palavras por bloco de legenda (padrão: 8)
python transcribe.py --max-words 12

# Aceitar mais extensões
python transcribe.py --ext mp4 mkv avi webm
```

## Saída

Para cada vídeo `data/filme.mp4`, são gerados:

```
subtitles/
├── filme.srt   ← legendas com timestamps, pronto para VLC/MPV/etc.
└── filme.txt   ← transcrição plana completa
```

**Exemplo de .srt gerado:**
```
1
00:00:00,120 --> 00:00:03,840
Hello and welcome to today's presentation.

2
00:00:03,960 --> 00:00:07,200
We're going to talk about machine learning.
```

## Performance esperada (RTX 3060 12GB)

| Vídeo | Tempo de transcrição |
|---|---|
| 10 min | ~5-10 segundos |
| 1 hora | ~30-60 segundos |
| 2 horas | ~1-2 minutos |

> O Parakeet processa em **batch** — quanto maior o vídeo, mais eficiente fica.

## Limitações

- **Idioma**: Parakeet TDT v2 é **English-only**. Para PT-BR, use Whisper Large v3.
- **Áudio ruidoso**: Performance cai em ambientes com muito ruído de fundo.
- **Múltiplos falantes**: Sem diarização (identificação de locutor) nesta versão.

## Arquitetura

```
video.mp4
    │
    ▼ FFmpeg (extrai áudio)
audio.wav  ← 16kHz, mono, PCM 16-bit
    │
    ▼ NVIDIA Parakeet TDT 0.6B v2 (NeMo)
(texto + word timestamps)
    │
    ├──▶ subtitles/video.txt  (texto plano)
    └──▶ subtitles/video.srt  (legendas agrupadas)
```

## Licença

- **Parakeet TDT**: [NVIDIA Open Model License](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2)
- **NeMo**: Apache 2.0
- **FFmpeg**: LGPL/GPL
- **Este script**: MIT