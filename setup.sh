#!/bin/bash
# setup.sh — Instala dependências do Parakeet Transcriber
# Testado em Ubuntu 22.04 + CUDA 12.x + RTX 3060

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Parakeet Transcriber — Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. FFmpeg
echo ""
echo "[1/4] Verificando FFmpeg..."
if command -v ffmpeg &>/dev/null; then
    echo "  ✓ FFmpeg já instalado: $(ffmpeg -version 2>&1 | head -1)"
else
    echo "  → Instalando FFmpeg..."
    sudo apt-get update -qq && sudo apt-get install -y ffmpeg
    echo "  ✓ FFmpeg instalado."
fi

# 2. Python e pip
echo ""
echo "[2/4] Verificando Python..."
python3 --version
pip3 --version

# 3. PyTorch com CUDA 12.1
echo ""
echo "[3/4] Instalando PyTorch com suporte CUDA 12.1..."
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verifica se CUDA está disponível
python3 -c "import torch; assert torch.cuda.is_available(), 'CUDA não disponível!'; print(f'  ✓ CUDA OK — GPU: {torch.cuda.get_device_name(0)}')"

# 4. NeMo ASR
echo ""
echo "[4/4] Instalando NVIDIA NeMo [asr]..."
pip3 install "nemo_toolkit[asr]>=2.0.0"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup concluído! "
echo ""
echo "  Uso:"
echo "    mkdir -p data subtitles"
echo "    # Coloque seus vídeos em ./data"
echo "    python3 transcribe.py"
echo ""
echo "  Opções:"
echo "    python3 transcribe.py --data /caminho/videos --subtitles /caminho/saida"
echo "    python3 transcribe.py --max-words 10"
echo "    python3 transcribe.py --ext mp4 mkv avi"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"